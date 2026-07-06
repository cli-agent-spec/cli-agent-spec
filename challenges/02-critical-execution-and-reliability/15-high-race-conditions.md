> **Part II: Execution & Reliability** | Challenge §15

## 15. Race Conditions & Concurrency

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### Impact

- Parallel agent tool calls silently corrupt shared state — config writes lost, temp files overwritten
- Lock conflicts produce unstructured errors with no retry guidance
- Non-deterministic failures are hard to reproduce and hard to diagnose from logs

### The Problem

Agents may invoke multiple tool calls in parallel. CLI tools designed for single-user sequential use can corrupt shared state when called concurrently.

**Lock file conflicts:**
```bash
# Two parallel agent tool calls:
$ tool build   # writes to /tmp/tool.lock
$ tool test    # also writes to /tmp/tool.lock → conflict

# One gets: Error: lock file exists
# Other: runs fine
# Agent doesn't know which one to retry
```

**Shared temp files:**
```bash
$ tool process --input data.csv --output /tmp/result.json
# Two parallel calls both write to /tmp/result.json
# One overwrites the other's result silently
```

**Race on config mutation:**
```bash
# Parallel calls:
$ tool config set key1 val1   # reads config, writes key1
$ tool config set key2 val2   # reads config (before key1 written), writes key2
# Result: key1 is lost
```

### Solutions

**Session-isolated temp paths:**
```bash
tool process --input data.csv --session-id $AGENT_SESSION_ID
# Uses /tmp/tool/$AGENT_SESSION_ID/result.json automatically
```

**Advisory locking with timeout:**
```bash
$ tool build
Error: {
  "code": "LOCK_HELD",
  "message": "Another build is running (pid 1234, started 30s ago)",
  "suggestion": "Wait for it to complete or use --force-unlock if process is dead",
  "retry_after_ms": 5000
}
```

**For framework design:**
- All temp files scoped to `$TOOL_SESSION_ID` or a random run ID
- Lock acquisition has a timeout and emits `retry_after_ms`
- Config mutations use atomic write (write to temp, rename)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Shared temp files and no locking; parallel invocations silently corrupt each other |
| 1 | Some locking exists but lock conflict produces unstructured error with no retry hint |
| 2 | Structured `LOCK_HELD` error with `retry_after_ms`; lock always released on exit |
| 3 | `--session-id` namespaces all temp paths; atomic config writes; lock timeout emits structured error |

**Check:** Invoke two parallel instances of a mutating command — neither should silently succeed while corrupting the other's output; one must fail with a structured `LOCK_HELD` error containing `retry_after_ms`.

---

### Agent Workaround

**Signature:** `lock file exists` or `LOCK_HELD` in stderr only when calls run in parallel; parallel runs both exit `0` but outputs or config keys silently vanish

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** run tool invocations one at a time, never in parallel; if that fails, escalate with the command, exit code, stdout, and stderr

**Serialize parallel calls when a tool does not support concurrent invocation:**

```python
import threading, time, json

_tool_lock = threading.Lock()  # serialize within the same agent process

def run_serialized(cmd):
    with _tool_lock:
        return run(cmd)

# If a LOCK_HELD error is returned, back off and retry
def run_with_backoff(cmd, max_retries=3):
    for attempt in range(max_retries):
        result = run(cmd)
        parsed = json.loads(result.stdout) if result.stdout else {}
        error_code = parsed.get("error", {}).get("code", "")
        if error_code == "LOCK_HELD":
            wait_ms = parsed.get("error", {}).get("retry_after_ms", 2000)
            time.sleep(wait_ms / 1000)
            continue
        return result
    raise RuntimeError("Lock not released after retries")
```

**Pass a unique session ID per parallel invocation if the flag exists:**
```bash
tool process --session-id $(uuidgen) --input data.csv
```

**Limitation:** If the tool uses global shared state with no locking at all, concurrent invocations will silently corrupt each other with no error — the only safe approach is to enforce sequential execution at the agent level, which eliminates any parallelism benefit
