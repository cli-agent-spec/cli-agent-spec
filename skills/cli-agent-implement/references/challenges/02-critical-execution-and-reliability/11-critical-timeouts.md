> **Part II: Execution & Reliability** | Challenge §11

## 11. Timeouts & Hanging Processes

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Agents have finite time budgets per tool call. A command that runs forever (network hang, deadlock, waiting for input) burns the budget and returns nothing.

**Sources of indefinite hangs:**
```bash
$ curl http://unreachable-host/api   # DNS timeout: 30-120s default
$ tool sync --remote                  # waits for remote that never responds
$ flock /var/lock/myapp.lock cmd     # waits if lock is held
$ tool process-queue                  # long-running daemon started as CLI
$ docker pull large-image            # download with no progress/timeout
```

**Partial output before hang:**
```
$ tool import large-file.csv
Importing row 1...
Importing row 2...
Importing row 3...
[hangs at row 4]
```
Agent sees partial output, doesn't know if it succeeded or hung.

**Timeout that produces no output:**
```bash
$ tool --timeout 30 slow-operation
# exits after 30s with exit code 124 (timeout's convention)
# but produces no output — agent doesn't know what happened
```

### Impact

- Agent turn fails with timeout, no error information extracted
- Partial side effects may have occurred (unknown state)
- Agent may retry, causing duplicate side effects

### Solutions

**Built-in timeout flags:**
```bash
tool operation --timeout 30s        # fail after 30 seconds
tool operation --connect-timeout 5s # specifically for connection phase
```

**Progress heartbeats to stderr:**
```bash
$ tool long-operation --output json
# stderr:
[  2s] Starting...
[  5s] Phase 1/3: downloading (23%)
[ 10s] Phase 1/3: downloading (67%)
[ 15s] Phase 2/3: processing
# stdout (only on completion):
{"ok": true, "data": {...}}
```

**Emit partial results before timeout:**
```json
{
  "ok": false,
  "partial": true,
  "data": {"processed": 42, "total": 100},
  "error": {"code": "TIMEOUT", "message": "Operation timed out after 30s"},
  "resume_token": "abc123"   // allows resuming if supported
}
```

**For framework design:**
- Every command has a default timeout; `--timeout 0` means no timeout (must be explicit)
- Timeout exits with a specific code (e.g., `7`) and always emits JSON error
- Provide `--heartbeat-interval` to control stderr progress frequency
- Track and report wall time in every JSON response's `meta.duration_ms`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No timeout mechanism; commands hang indefinitely on network or lock contention |
| 1 | `--timeout` flag exists but emits only text output; exit code is non-specific (e.g., `1`) |
| 2 | Timeout emits structured JSON error with `code: "TIMEOUT"`; exit code is defined (exit 10) |
| 3 | Timeout emits partial result with `completed_steps`, `resume_token`, and `meta.duration_ms`; `--heartbeat-interval` available |

**Check:** Run a command pointing at an unreachable host with a 2s timeout — verify it exits within 3s with a JSON error and a defined exit code.

---

### Agent Workaround

**Signature:** no output or partial progress lines, then silence until killed by timeout; `exit 124` from an external `timeout` wrapper with no JSON error emitted

**Tier:** B (one observable check, then one command)

**Enforce a timeout at the subprocess level and parse whatever partial output exists:**

```python
import subprocess, json, sys

try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=30,          # enforce externally even if --timeout not available
        text=True,
    )
    output = result.stdout
except subprocess.TimeoutExpired as e:
    output = (e.stdout or b"").decode(errors="replace")
    # Try to parse partial JSON if any was flushed before timeout
    try:
        parsed = json.loads(output.strip().split("\n")[-1])
    except Exception:
        parsed = {"ok": False, "error": {"code": "TIMEOUT", "partial_output": output}}

# Check meta.duration_ms if present to detect near-timeout situations
```

**Limitation:** If the tool buffers all output and flushes nothing before timeout, the agent receives no partial result — there is no workaround for fully-buffered tools; use a shorter timeout to fail fast and avoid wasting turn budget
