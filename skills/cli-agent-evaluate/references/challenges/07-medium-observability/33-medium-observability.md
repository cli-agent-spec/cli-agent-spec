> **Part VI: Observability** | Challenge §33

## 33. Observability & Audit Trail

**Severity:** Medium | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** High | **Context:** Medium

### The Problem

When an agent-driven operation fails or produces unexpected results, there's often no way to trace what commands ran, in what order, with what parameters, and what they returned.

**No correlation between tool calls:**
```bash
# Three tool calls: deploy, verify, rollback
# Each has separate logs with no shared identifier
# Impossible to reconstruct the sequence after the fact
```

**No request ID in output:**
```bash
$ tool deploy
{"ok": true, "effect": "deployed"}
# No request ID to correlate with server-side logs
```

**No timing information:**
```bash
# Tool ran for 45 seconds
# Output has no timestamps
# Impossible to identify which step was slow
```

### Impact

- No audit trail means post-incident reconstruction is impossible
- Missing `request_id` prevents correlation between agent-side logs and server-side logs
- No timing data makes it impossible to identify which step in a sequence was slow
- Agents that re-run operations cannot tell if the outcome was from the current run or a cached/prior result

### Solutions

**Request/trace ID in every response:**
```json
{
  "ok": true,
  "meta": {
    "request_id": "req-abc123",
    "trace_id": "trace-xyz789",
    "duration_ms": 4521,
    "timestamp": "2024-03-11T14:30:00Z",
    "command": "deploy",
    "version": "1.2.3"
  }
}
```

**Correlation ID propagation:**
```bash
TOOL_TRACE_ID=agent-session-42-step-7 tool deploy
# All log entries for this call include the trace ID
```

**Structured audit log:**
```bash
$ tool audit-log --since 1h --output jsonl
{"timestamp": "...", "command": "deploy", "params": {...},
 "exit_code": 0, "duration_ms": 4521, "operator": "agent-session-42"}
```

**For framework design:**
- Every response includes `meta.request_id` (server-assigned) and `meta.trace_id` (caller-supplied)
- `TOOL_TRACE_ID` env var propagated automatically
- Framework writes append-only audit log to `~/.local/share/tool/audit.jsonl`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No `request_id`, no timing, no audit log; tool calls cannot be correlated after the fact |
| 1 | `meta.request_id` present on some responses; no `duration_ms`; no audit log |
| 2 | `meta.request_id` and `meta.duration_ms` on all responses; `TOOL_TRACE_ID` env var propagated |
| 3 | `meta.trace_id` accepts caller-supplied value; `tool audit-log --output jsonl` available; append-only audit log written automatically |

**Check:** Supply `TOOL_TRACE_ID=test-123` and run any command — verify `meta.trace_id == "test-123"` in the JSON response.

---

### Agent Workaround

**Signature:** responses lack `meta.request_id`, `duration_ms`, and timestamps; `TOOL_TRACE_ID` not echoed back; no `audit-log` command

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Run `TOOL_TRACE_ID=<session-id> tool <args>`; if that fails, escalate with the command, exit code, stdout, and stderr

**Supply a unique trace ID per agent session and per operation; log `request_id` from every response:**

```python
import subprocess, json, uuid, os, time

# Generate a session-scoped trace ID
SESSION_TRACE_ID = f"agent-session-{uuid.uuid4().hex[:8]}"

def traced_run(cmd: list[str], operation: str) -> dict:
    # Per-operation trace ID for fine-grained correlation
    op_trace_id = f"{SESSION_TRACE_ID}-{operation}-{uuid.uuid4().hex[:4]}"

    env = {**os.environ, "TOOL_TRACE_ID": op_trace_id}
    start = time.monotonic()

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"No JSON from {operation}")

    meta = parsed.get("meta", {})
    request_id = meta.get("request_id", "unknown")
    tool_duration = meta.get("duration_ms", "unknown")

    # Log for post-incident reconstruction
    print(
        f"[TRACE] op={operation} trace={op_trace_id} "
        f"request_id={request_id} "
        f"agent_ms={elapsed_ms} tool_ms={tool_duration}"
    )

    return parsed

result = traced_run(
    ["tool", "deploy", "--env", "staging", "--output", "json"],
    operation="deploy",
)
```

**Query the audit log when reconstructing what happened:**
```python
def get_audit_log(tool: str, since: str = "1h") -> list[dict]:
    result = subprocess.run(
        [tool, "audit-log", "--since", since, "--output", "jsonl"],
        capture_output=True, text=True,
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return [json.loads(l) for l in lines]
```

**Limitation:** If the tool provides no `request_id` and no audit log, the only correlation mechanism is timestamps — log the wall-clock time of every tool call in the agent and compare against server-side logs manually to reconstruct sequences

