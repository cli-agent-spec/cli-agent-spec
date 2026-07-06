> **Part III: Errors & Discoverability** | Challenge §18

## 18. Error Message Quality

**Severity:** High | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** High

### The Problem

When a command fails, the agent needs to understand: what failed, why, and what to do next. Vague, undirected, or human-only error messages force the agent to guess.

**Errors that don't help the agent:**
```bash
$ tool deploy
Error: Something went wrong
exit 1
# Agent has zero actionable information
```

```bash
$ tool connect --host db.example.com
Connection failed.
exit 1
# Was it DNS? Auth? Firewall? Timeout? Agent doesn't know which to fix.
```

```bash
$ tool validate config.yaml
Validation error on line 14
exit 1
# Agent doesn't know what the error is, what the fix is, or what field
```

**Stack traces as error output:**
```bash
$ tool process file.csv
Traceback (most recent call last):
  File "tool.py", line 234, in process
    result = parser.parse(row)
  File "tool.py", line 89, in parse
    return int(row['count'])
ValueError: invalid literal for int() with base 10: 'N/A'
exit 1
# Agent receives a Python traceback — high token cost, low actionability
```

**Errors that require human interpretation:**
```bash
$ tool sync
SQLSTATE[23000]: Integrity constraint violation: 1062 Duplicate entry '42' for key 'PRIMARY'
exit 1
# Agent would need to reason about SQL error codes
```

### Impact

- Agent retries with identical parameters (no basis to change anything)
- Agent escalates to user with no useful information
- Token waste reasoning about unparseable error text

### Solutions

**Structured error format:**
```json
{
  "ok": false,
  "error": {
    "code": "CONNECTION_REFUSED",      // machine-readable code
    "message": "Cannot connect to database at db.example.com:5432",
    "cause": "Connection refused (ECONNREFUSED)",
    "suggestion": "Verify the database is running: `tool db status`",
    "docs_url": "https://docs.example.com/errors/CONNECTION_REFUSED",
    "context": {
      "host": "db.example.com",
      "port": 5432,
      "timeout_ms": 5000
    }
  }
}
```

**Error code taxonomy:**
```
{DOMAIN}_{NOUN}_{CONDITION}

Examples:
  DB_CONNECTION_REFUSED
  AUTH_TOKEN_EXPIRED
  FILE_CONFIG_NOT_FOUND
  API_RATE_LIMIT_EXCEEDED
  INPUT_PARAM_INVALID
```

**Suggestion field for common errors:**
```json
"suggestion": "Run `tool login` to refresh your credentials"
"suggestion": "Use --force to overwrite existing file"
"suggestion": "Check network connectivity with: ping db.example.com"
```

**For framework design:**
- All errors MUST have a `code` (machine) and `message` (human)
- `suggestion` field is encouraged for recoverable errors
- When the remediation is a single safe command, emit `fix_command` (exact, verbatim-executable invocation) alongside the prose (REQ-C-030): prose requires the caller to synthesize a command, `fix_command` only requires copying one
- Never emit raw stack traces to stdout; log them to stderr or a file
- Provide an error code registry queryable via `tool errors list`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Errors are prose strings or stack traces; no machine-readable `code`; agent cannot act without human interpretation |
| 1 | Some errors have a `code` field; `message` is present but `suggestion` and `context` are absent |
| 2 | All errors have `code`, `message`, and `context`; stack traces go to stderr, not stdout |
| 3 | `suggestion` field on all recoverable errors; `docs_url` per error code; `tool errors list --output json` enumerates all codes |

**Check:** Trigger a known error (e.g., pass an invalid argument) and verify stdout contains `{"ok": false, "error": {"code": "...", "message": "...", "suggestion": "..."}}` with no stack trace.

---

### Agent Workaround

**Signature:** failure exits `1` with a vague prose message (`Something went wrong`) or a `Traceback` dump; no `error.code` or `suggestion` field in output

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Do not retry with identical arguments; escalate with the command, exit code, stdout, and stderr

**Extract and act on `error.code` and `error.suggestion` rather than parsing message text:**

```python
import subprocess, json

result = subprocess.run(
    ["tool", "connect", "--host", host, "--output", "json"],
    capture_output=True, text=True,
)

try:
    parsed = json.loads(result.stdout)
except json.JSONDecodeError:
    # No structured output — raw crash or prose error on stdout
    raise RuntimeError(f"Tool produced no JSON: {result.stdout[:200]}")

if not parsed.get("ok"):
    error = parsed["error"]
    code = error.get("code", "UNKNOWN")
    suggestion = error.get("suggestion", "")
    context = error.get("context", {})

    if code == "CONNECTION_REFUSED":
        # Use the suggestion to determine next action
        raise RuntimeError(f"Connection failed: {suggestion or 'check host/port'}")
    elif code == "AUTH_TOKEN_EXPIRED":
        # Trigger re-auth flow
        refresh_token()
    else:
        raise RuntimeError(f"[{code}] {error.get('message')} | {suggestion}")
```

**Check stderr for stack traces when stdout JSON is missing:**
```python
if result.returncode != 0 and not result.stdout.strip():
    # Unstructured failure — check stderr for clues
    stderr = result.stderr
    if "Traceback" in stderr:
        # Unhandled exception — extract the last line
        last_line = [l for l in stderr.splitlines() if l.strip()][-1]
        raise RuntimeError(f"Tool crash: {last_line}")
```

**Limitation:** If the tool emits only prose error messages with no `code` field, the agent must pattern-match against message text — this is fragile and will break when the tool's error messages change wording
