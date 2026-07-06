> **Part I: Output & Parsing** | Challenge §3

## 3. Stderr vs Stdout Discipline

**Severity:** High | **Frequency:** Very Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Low | **Context:** High

### The Problem

Unix convention: stdout = data, stderr = diagnostics. Most CLI tools violate this, mixing progress messages, warnings, and errors into stdout alongside actual output.

```bash
$ tool export-data > output.json
Connecting to server...
Fetching records... (234 found)
Warning: 3 records skipped (missing required field)
{"records": [...]}
Export complete.
```

```bash
$ cat output.json
Connecting to server...
Fetching records... (234 found)
Warning: 3 records skipped (missing required field)
{"records": [...]}
Export complete.
# ← not valid JSON, parse fails
```

**Agent captures both streams together:**
```python
result = subprocess.run(cmd, capture_output=True)
output = result.stdout.decode()
# if tool mixed stderr into stdout, output is corrupted
```

**Warnings that belong on stderr end up in stdout:**
```
$ tool validate config.yaml
config.yaml is valid
Warning: deprecated key 'timeout' found at line 12
```
Agent parses first line as success, misses the warning.

### Impact

- Output parsing fails when stdout is contaminated
- Warnings are invisible to agents (they read stdout, log stderr separately)
- Agent cannot distinguish data from diagnostics

### Solutions

**Strict stream discipline:**
```
stdout: ONLY the command's primary output (data, result, id)
stderr: progress indicators, warnings, debug info, timing, counts
```

```bash
# Good
$ tool create-user --name Alice 2>/dev/null
{"id": 42, "name": "Alice"}

$ tool create-user --name Alice 1>/dev/null
Creating user Alice...
Done. (45ms)
```

**Structured warnings in JSON output:**
```json
{
  "ok": true,
  "data": {"records": [...]},
  "warnings": [
    {"code": "DEPRECATED_KEY", "message": "...", "location": "line 12"}
  ]
}
```

**For framework design:**
- Route all `log()`, `progress()`, `debug()` calls to stderr by default
- Only `print()` / `output()` writes to stdout
- Provide `--quiet` to suppress all stderr
- Provide `--warnings-as-errors` to exit non-zero on any warning

---

> **Merged from §39:** The following content was originally a separate challenge.
> It is consolidated here because it describes a specific case of the same root problem.

### Subsection: Help Text Routed to Stdout

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Low | **Context:** High

### The Problem

In some frameworks, particularly Commander.js (the most widely deployed Node.js CLI framework), `--help` output goes to **stdout** by default. Most agent workflows capture stdout as the primary data channel. When an agent invokes a command that prints help (e.g., because a required argument is missing), help text floods stdout, corrupting what the agent expects to be structured data.

This is distinct from challenge #3 (Stderr vs Stdout Discipline), which focuses on error messages and diagnostic output mixing into stdout. Challenge #3 describes the general class of problem. This challenge specifically concerns **help text** — which has unique properties: it is very long (filling the context window), occurs in specific failure conditions (wrong invocation), and is not a runtime error but a framework-generated response. Many CLIs that correctly route runtime errors to stderr still route help text to stdout.

```javascript
// Commander.js default: help goes to stdout
program.parse();  // If required arg missing, help printed to stdout then exits 1

// Agent capture:
const result = await exec('my-tool deploy');  // missing required --env
// result.stdout = "Usage: my-tool deploy [options]\n\nDeploy to an environment\n\nOptions:\n  -e, --env..."
// result.stderr = ""
// result.exitCode = 1
// Agent tries to parse result.stdout as JSON → fails
```

The failure is compounded by timing: help output appears on the same stdout stream as normal output, meaning an agent that has successfully called a command dozens of times may suddenly receive help text when it makes a slightly wrong call — with no separator or content-type indicator to distinguish the two.

Python Fire is worse: it routes **all** its own output (help, trace, error messages) to stdout, making stdout an indistinguishable mix of framework messages and application data.

### Impact

- Agent attempts to JSON-parse help text, fails, reasons incorrectly about the invocation
- Help text is long (hundreds of tokens), consuming context window for no useful purpose (the agent already has the schema from `--help --json` or `--schema`)
- Agent may mistake help text for successful output (e.g., a `deploy` command that prints usage text looks like it printed deployment instructions)
- If the agent does parse the failure correctly, it must distinguish help-on-failure from data-output, requiring content-sniffing heuristics
- In Python Fire specifically, there is no reliable way to separate framework messages from application output in the stdout stream

### Solutions

**For agents invoking CLI tools:**
```python
result = subprocess.run(cmd, capture_output=True)
# Detect help text pollution before attempting to parse
if result.returncode != 0 and ('Usage:' in result.stdout.decode() or 'Options:' in result.stdout.decode()):
    # This is help text, not data output
    raise ValueError(f"Command failed (usage error): {cmd}")
```

**For CLI authors using Commander.js:**
```javascript
program.configureOutput({
    writeOut: (str) => process.stderr.write(str),  // ✓ route help to stderr
    writeErr: (str) => process.stderr.write(str),
});
```

**For framework design:**
- Route all help output to stderr by default when stdout is not a TTY
- Never route help or usage text to stdout, regardless of TTY state
- When `isatty(stdout) == False`, replace help display with a structured JSON error on stdout:
  ```json
  {"ok": false, "error": {"code": "USAGE_ERROR", "message": "Missing required option --env",
   "hint": "Run with --schema for the full interface definition"}}
  ```
- Ensure that exit-code-2 (usage error) is always accompanied by stderr-only output, never stdout output

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Progress messages, warnings, and help text mixed into stdout alongside data |
| 1 | Most data on stdout but some prose leaks (e.g. "Done.", help text on bad invocation, or debug lines) |
| 2 | All diagnostic content on stderr; data only on stdout; warnings present in JSON `warnings[]` field |
| 3 | Help text routed to stderr in non-TTY mode; `--quiet` suppresses all stderr; `--warnings-as-errors` flag available |

**Check:** Run any command redirecting stdout to a file and stderr to `/dev/null`, then validate the file contains only valid JSON — any prose in the file is a failure.

---

### Agent Workaround

**Signature:** redirected stdout contains progress or warning prose around the data; `Usage:` or `Options:` on stdout with nonzero exit and empty stderr

**Tier:** B (one observable check, then one command)

**Always capture stderr and stdout separately; detect contamination before parsing:**

```python
result = subprocess.run(cmd, capture_output=True, text=True)

stdout = result.stdout.strip()
stderr = result.stderr.strip()

# Detect help text on stdout (usage error with wrong invocation)
HELP_MARKERS = ("Usage:", "Options:", "Commands:", "Examples:")
if any(m in stdout for m in HELP_MARKERS):
    # Don't try to parse — extract the actual error from stderr instead
    raise ValueError(f"Usage error — got help text on stdout. stderr: {stderr[:300]}")

# Treat stderr lines as diagnostic context, not data
if stderr:
    # Log for debugging but don't mix into parsed result
    logger.debug("tool stderr: %s", stderr)

parsed = json.loads(stdout)
```

**For tools that mix prose with the JSON body on stdout, apply the canonical extraction rule (identical in §2, §41, §68; defined in [triage.md](../triage.md)):**

```python
import json, re

def extract_envelope(stdout: str):
    """Canonical JSON extraction rule — defined in challenges/triage.md."""
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", stdout)   # 1. strip ANSI codes
    try:
        return json.loads(text)                            # 2. fast path: clean stream
    except json.JSONDecodeError:
        pass
    candidates = []                                        # 3. every maximal JSON value
    decoder = json.JSONDecoder()
    i = 0
    while True:
        starts = [s for s in (text.find(c, i) for c in "{[") if s != -1]
        if not starts:
            break
        start = min(starts)
        try:
            obj, end = decoder.raw_decode(text[start:])
            candidates.append(obj)
            i = start + end
        except json.JSONDecodeError:
            i = start + 1
    envelopes = [c for c in candidates if isinstance(c, dict) and "ok" in c]
    if envelopes:
        return envelopes[-1]                               # 4. last envelope wins
    if candidates:
        return candidates[-1]                              # 5. last complete value
    return None                                            # 6. unstructured: do not guess
```

**Limitation:** If a tool routes structured data to stderr or mixes help text and JSON in the same stream with no separator, there is no reliable parse strategy — the tool requires a fix from its author before it can be safely used by agents
