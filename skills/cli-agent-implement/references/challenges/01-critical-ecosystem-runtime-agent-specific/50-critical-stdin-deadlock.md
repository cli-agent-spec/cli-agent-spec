> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §50

## 50. Stdin Consumption Deadlock

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Distinct from §10 (interactive prompts), some CLI tools silently read from stdin as a default fallback — not as a deliberate prompt but as an undocumented behavior: reading config from stdin when no config flag is provided, reading a list of IDs from stdin when no positional args are given, defaulting `--password` to a stdin read when the flag is omitted. In non-TTY context, this blocks indefinitely waiting for an EOF that never comes.

```bash
# Tool reads entity IDs from stdin when none are provided as args
$ my-tool delete    # agent omits the --id flag
# ← blocks forever, waiting for stdin EOF in non-TTY mode

# Password argument defaults to stdin read when omitted
$ my-tool --user admin    # agent forgets --password flag
Password:     # ← blocking read from stdin
# In non-TTY mode: hangs until timeout

# Tool falls back to reading config from stdin
$ my-tool run     # no --config flag provided
# Waiting for config JSON on stdin...
```

The tell: the process is running, consuming no CPU, producing no output — indistinguishable from "slow initialization" until the full timeout fires.

### Impact

- Agent's entire timeout budget burned silently with no error
- No warning or error is emitted before blocking occurs
- Tool may need to be killed externally, potentially leaving partial state
- If stdin is connected to a pipe, the tool may read the pipe content as its "config", corrupting input

### Solutions

**Non-TTY stdin reads must fail immediately with exit 4:**
```json
{
  "ok": false,
  "error": {
    "code": "STDIN_REQUIRED",
    "message": "Argument '--ids' requires input but stdin is not a TTY and no value was provided.",
    "hint": "Pass --ids <value> or pipe data: echo '123' | my-tool delete --ids -"
  }
}
```

**Schema must declare all stdin-reading paths:**
```json
{
  "args": [
    {
      "name": "ids",
      "stdin_fallback": true,
      "stdin_format": "newline-separated IDs",
      "non_tty_behavior": "fail_with_exit_4"
    }
  ]
}
```

**For framework design:**
- All stdin reads must be declared in the command schema; undeclared stdin reads are a framework error
- In non-TTY mode, the framework wraps `stdin.read()` calls with an immediate-fail guard that exits 4 with a structured error listing the flag to pass instead
- The `--schema` output for every command must indicate which args accept stdin as input and what format is expected

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Tool blocks indefinitely on stdin read in non-TTY mode; no timeout, no structured error, no hint |
| 1 | Tool eventually fails or produces an unhelpful message; no structured error; `STDIN_REQUIRED` code absent |
| 2 | Non-TTY stdin read exits immediately with `STDIN_REQUIRED` structured error and a `hint` showing the flag to use |
| 3 | All stdin-reading args declared in schema with `stdin_fallback` and `non_tty_behavior` fields; framework enforces immediately on non-TTY |

**Check:** Invoke a command that reads from stdin with `stdin=subprocess.DEVNULL` — verify it exits within 1 second with `{"code": "STDIN_REQUIRED", "hint": "..."}`.

---

### Agent Workaround

**Signature:** process produces no output, consumes no CPU, and never exits when an expected flag is omitted; killed only by timeout; sometimes a bare `Password:` prompt

**Tier:** A (one safe command, no branching)

**Always pass `stdin=DEVNULL`; if a required arg is missing, the tool should fail fast — treat 1s hangs as stdin reads:**

```python
import subprocess, json, signal

def run_no_stdin(cmd: list[str], timeout: int = 10) -> dict:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            stdin=subprocess.DEVNULL,   # critical: never let tool inherit stdin
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        e.process.kill()
        raise RuntimeError(
            f"Command timed out after {timeout}s with DEVNULL stdin — "
            "likely blocking on undeclared stdin read. "
            "Check schema for required args that default to stdin fallback."
        )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"No JSON output: {result.stdout[:200]}")

    if not parsed.get("ok"):
        error = parsed.get("error", {})
        if error.get("code") == "STDIN_REQUIRED":
            hint = error.get("hint", "pass the required argument explicitly")
            raise RuntimeError(f"Tool requires stdin input: {hint}")

    return parsed
```

**Limitation:** If the tool reads from `/dev/tty` directly (bypassing `stdin`), `DEVNULL` does not prevent the block — use a short `timeout` (5–10 seconds) on every invocation as a universal guard against undeclared stdin reads
