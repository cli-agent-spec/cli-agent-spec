> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §37

## 37. REPL / Interactive Mode Accidental Triggering

**Severity:** Critical | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Some CLI tools expose a REPL (Read-Eval-Print Loop) or interactive shell mode — either as an explicit subcommand (`my-tool shell`, `my-tool repl`) or as a flag triggered under certain conditions. Python Fire's `--interactive` flag is the canonical example: passing it drops the user into an IPython shell with the object in scope. If an agent constructs an invocation that includes `--interactive` (e.g., from a misread help text, a hallucinated flag, or a misconfigured test), the process hangs indefinitely.

This is distinct from challenge #10 (Interactivity & TTY Requirements), which concerns `prompt()` and `confirm()` calls — single-question interactive pauses. A REPL is an ongoing interactive loop that cannot be resolved by sending a single stdin input. Even sending `quit\n` or `exit\n` to stdin only works if the REPL is actually reading from stdin, which is not guaranteed.

```bash
# Fire CLI: agent passes --interactive by accident
python my_fire_cli.py process_data --dataset=path/to/data.csv --interactive
# Drops into IPython: "Python 3.x.x | IPython x.x.x"
# Process is now waiting for interactive input forever
# No stderr output, no error, exit code never comes
```

Beyond Python Fire, this pattern appears in:
- Any tool with a `shell` or `repl` subcommand that does not check for TTY before launching
- `python -c` calls inside tools that may be executed with `-i` flag
- Database CLI tools (`psql`, `mysql`) invoked without a query — they drop into interactive mode
- YAML/JSON editors that open an interactive editor when no explicit value is provided

### Impact

- Process hangs until the agent's external timeout fires (challenge #11), consuming the full timeout budget
- The agent may interpret the hung process as a slow operation and retry, creating multiple hanging processes (challenge #17)
- Unlike `prompt()` which produces visible output ("Enter value:"), a REPL may produce a welcome banner that the agent misinterprets as success output
- On some terminals, the REPL changes terminal state (raw mode), potentially corrupting subsequent output
- No structured error is produced — the hang is silent from the framework's perspective

### Solutions

**For CLI authors:**
```python
import sys

# Gate ALL REPL/interactive modes behind TTY check
@app.command()
def shell():
    if not sys.stdin.isatty():
        print(json.dumps({"ok": False, "error": {"code": "INTERACTIVE_REQUIRED",
            "message": "Shell mode requires an interactive terminal. Run without redirection."}}))
        sys.exit(2)
    launch_repl()

# Python Fire: never register --interactive as a reachable flag in non-TTY environments
```

**For agents:**
```python
# Scan --help output for REPL-triggering flags before first invocation
REPL_FLAGS = {"--interactive", "--shell", "--repl", "-i"}
help_output = subprocess.run([tool, "--help"], capture_output=True).stdout.decode()
risky_flags = [f for f in REPL_FLAGS if f in help_output]
# Avoid those flags; set stdin=subprocess.DEVNULL to prevent stdin reads

result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
```

**For framework design:**
- Any command flagged as `interactive=True` or `mode="repl"` must gate on `sys.stdin.isatty()` and return a structured error if the check fails, rather than attempting to launch
- Provide a framework-level `REPL_GUARD` decorator that wraps REPL-launching commands
- Default `stdin=subprocess.DEVNULL` in all framework-generated subprocess calls and test harnesses
- Document in `--schema` output which commands require interactive mode, so agents can skip them

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | REPL/interactive mode launches in non-TTY without check; hangs indefinitely; no error emitted |
| 1 | TTY check exists but fails silently or hangs rather than emitting a structured error |
| 2 | Non-TTY invocation of REPL mode exits immediately with a structured `INTERACTIVE_REQUIRED` error (exit 2) |
| 3 | `--schema` flags commands as `"requires_interactive": true`; framework `REPL_GUARD` prevents non-TTY launch at registration time |

**Check:** Invoke any REPL/shell subcommand with `stdin=subprocess.DEVNULL` — verify it exits within 1 second with a structured JSON error, not a hang.

---

### Agent Workaround

**Signature:** process hangs and never exits; stdout shows a REPL banner or prompt (`IPython`, `>>>`, `mysql>`) instead of command output; ends only when killed by timeout

**Tier:** B (one observable check, then one command)

**Always set `stdin=DEVNULL` and scan for REPL-triggering flags before first invocation:**

```python
import subprocess, re

REPL_FLAGS = {"--interactive", "--shell", "--repl", "-i", "--console"}

def has_repl_risk(tool: str) -> set[str]:
    """Check help text for REPL-triggering flags."""
    result = subprocess.run(
        [tool, "--help"],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
    found = set()
    for flag in REPL_FLAGS:
        if flag in result.stdout or flag in result.stderr:
            found.add(flag)
    return found

risky = has_repl_risk("tool")
if risky:
    print(f"WARNING: Tool exposes REPL flags {risky} — never pass these to tool calls")

# All subprocess calls: stdin=DEVNULL prevents any blocking stdin read
result = subprocess.run(
    ["tool", "deploy", "--output", "json"],
    capture_output=True, text=True,
    stdin=subprocess.DEVNULL,  # critical: prevents any blocking read
    timeout=60,
)
```

**Kill a hung REPL invocation and mark it as an interactive-required failure:**
```python
import subprocess, signal

try:
    result = subprocess.run(
        cmd,
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
except subprocess.TimeoutExpired as e:
    e.process.send_signal(signal.SIGTERM)
    raise RuntimeError(
        "Command timed out — may have launched a REPL or interactive mode. "
        "Check for --shell/--repl/--interactive flags and avoid them."
    )
```

**Limitation:** If a tool launches a REPL unconditionally with no TTY check and ignores `DEVNULL` (e.g., reads from `/dev/tty` directly), the only defense is to kill the process after a short timeout and treat it as an interactive-required failure
