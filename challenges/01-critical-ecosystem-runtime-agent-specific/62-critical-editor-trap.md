> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §62

## 62. $EDITOR and $VISUAL Trap

**Source:** Gemini `03_execution_flow.md`, Antigravity `02_interactivity_and_prompts.md` (RA)

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Distinct from §37 (REPL triggering), many CLI tools invoke the user's `$EDITOR` or `$VISUAL` environment variable to open a text editor for structured input: `git commit` (without `-m`), `kubectl edit`, `crontab -e`, `visudo`, `tool config edit`. In non-TTY mode, these editor invocations either block indefinitely (vim waits for input), emit a flood of raw escape sequences, or crash with a tty-related error — all of which halt the agent.

```bash
# Agent runs git commit expecting to provide the message programmatically
$ git commit
# $EDITOR=vim is launched
# vim writes: \x1b[?1049h\x1b[22;0;0t\x1b[1;40r... (terminal init sequences)
# vim then blocks on stdin waiting for keystrokes
# In non-TTY mode: either hangs or immediately exits with "Vim: Warning: Input is not from a terminal"
# Either way: agent gets no commit

# kubectl edit opens $EDITOR with current resource YAML
$ kubectl edit deployment/my-app
# Opens vim with 200 lines of YAML
# Agent cannot edit the file and save it
# kubectl waits indefinitely for the editor to exit
```

### Impact

- Agent blocked indefinitely waiting for editor to complete
- Raw terminal escape sequences from editor startup contaminate any captured output
- The operation requiring the editor (commit, resource update) cannot proceed
- Agent has no way to know this will happen until after the blocking call

### Solutions

**Provide non-editor alternatives for all editor-requiring operations:**
```bash
# Good: explicit content flag bypasses editor
$ git commit -m "message"
$ kubectl patch deployment/my-app --patch '{"spec": {...}}'
$ tool config set key=value   # instead of tool config edit
```

**Set $EDITOR to a non-blocking shim in non-TTY mode:**
```bash
# Framework sets: EDITOR="tee /dev/stderr" or EDITOR="cat > /dev/null"
# Or: EDITOR="my-tool-editor-shim" which reads content from --editor-content flag
```

**Detect editor invocation in non-TTY mode and fail fast:**
```json
{
  "ok": false,
  "error": {
    "code": "EDITOR_REQUIRED",
    "message": "This command requires an interactive editor. Use --message or --from-file instead.",
    "alternatives": ["git commit -m '<message>'", "git commit --file <path>"]
  }
}
```

**For framework design:**
- Framework MUST set `EDITOR=true` (a no-op) and `VISUAL=true` in the subprocess environment when in non-TTY mode, preventing any spawned subprocess from launching an interactive editor
- Commands that use `$EDITOR` MUST declare `requires_editor: true` in their schema and provide a `--content` or `--from-file` alternative for non-TTY operation
- Framework MUST detect editor invocations in non-TTY mode and intercept them with exit 4 and a structured error listing the non-interactive alternative

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Commands launch `$EDITOR` in non-TTY mode; agent blocked indefinitely; raw terminal escape sequences contaminate captured output |
| 1 | Non-TTY detected; editor not launched; error is prose only; no `alternatives` field listing non-interactive option |
| 2 | `EDITOR_REQUIRED` structured error with `alternatives` array; exits immediately in non-TTY mode (exit 4) |
| 3 | `requires_editor: true` declared in schema; `--content` or `--from-file` alternative on all editor-requiring commands; framework sets `EDITOR=true` as no-op |

**Check:** Run any editor-requiring command (e.g., `git commit` without `-m`) with `EDITOR=` (empty) or `EDITOR=true` — verify it exits within 1 second with a structured error listing the non-interactive alternative.

---

### Agent Workaround

**Signature:** process hangs emitting raw escape sequences like `\x1b[?1049h`; or exits with `Vim: Warning: Input is not from a terminal`; occurs when `-m`/`--file` omitted

**Tier:** B (one observable check, then one command)

**Override `$EDITOR` with a no-op; always use non-interactive alternatives for editor-requiring commands:**

```python
import subprocess, json, os

env = {
    **os.environ,
    "EDITOR": "true",        # POSIX `true` command: exits 0 immediately, no output
    "VISUAL": "true",        # same for $VISUAL fallback
    "GIT_EDITOR": "true",    # override git's editor specifically
}

# For git: always use -m to bypass editor
result = subprocess.run(
    ["git", "commit", "-m", commit_message],   # never: ["git", "commit"]
    capture_output=True, text=True,
    env=env,
    stdin=subprocess.DEVNULL,
)

# For kubectl: always use --patch instead of edit
result = subprocess.run(
    ["kubectl", "patch", "deployment/my-app", "--patch", patch_json],
    capture_output=True, text=True,
    env=env,
    stdin=subprocess.DEVNULL,
)
```

**Detect EDITOR_REQUIRED errors and use the listed alternative:**
```python
parsed = json.loads(result.stdout)
if not parsed.get("ok"):
    error = parsed.get("error", {})
    if error.get("code") == "EDITOR_REQUIRED":
        alternatives = error.get("alternatives", [])
        if alternatives:
            print(f"Use instead: {alternatives[0]}")
        raise RuntimeError(f"Command requires interactive editor. Alternatives: {alternatives}")
```

**Limitation:** Setting `EDITOR=true` causes some tools to succeed silently (editor ran but made no changes), which may be indistinguishable from a successful no-op edit — always verify that the operation completed by checking the response `effect` field, not just exit code 0
