> **Part II: Execution & Reliability** | Challenge §13

## 13. Partial Failure & Atomicity

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

Multi-step commands can fail mid-execution, leaving the system in an unknown intermediate state. The agent receives a failure but doesn't know what was completed.

**Partial failure with no rollback:**
```bash
$ tool migrate-database
Step 1/4: backup... done
Step 2/4: apply schema changes... done
Step 3/4: migrate data... FAILED (disk full)
Step 4/4: (not reached)
exit 1
```
Agent retries. Step 2 runs again. Now schema is applied twice → error.

**Batch operations with partial success:**
```bash
$ tool send-notifications --users 1,2,3,4,5
Sent to user 1: ok
Sent to user 2: ok
Sent to user 3: FAILED (invalid email)
Sent to user 4: ok
Sent to user 5: FAILED (rate limited)
exit 1
```
Exit code 1 tells agent "failed" but 3/5 succeeded. Retry sends duplicates to 1, 2, 4.

### Impact

- Retry causes double execution of already-completed steps
- Agent cannot determine safe recovery path
- Manual intervention required to resolve unknown state

### Solutions

**Structured partial failure output:**
```json
{
  "ok": false,
  "partial": true,
  "completed_steps": ["backup", "apply_schema"],
  "failed_step": "migrate_data",
  "error": {"code": "DISK_FULL", "message": "..."},
  "resume_from": "migrate_data",
  "rollback_available": true
}
```

**Batch result per item:**
```json
{
  "ok": false,
  "partial": true,
  "results": [
    {"id": 1, "ok": true,  "effect": "sent"},
    {"id": 2, "ok": true,  "effect": "sent"},
    {"id": 3, "ok": false, "error": {"code": "INVALID_EMAIL"}},
    {"id": 4, "ok": true,  "effect": "sent"},
    {"id": 5, "ok": false, "error": {"code": "RATE_LIMITED"}}
  ],
  "summary": {"total": 5, "succeeded": 3, "failed": 2}
}
```

**Resumable commands:**
```bash
tool migrate-database --resume-from migrate_data
# Only runs remaining steps
```

**For framework design:**
- All multi-step commands emit a step manifest at start
- Each step emits its result as it completes (streaming JSON lines)
- Final summary always includes `completed`, `failed`, `skipped` counts
- `--rollback-on-failure` flag as standard option

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Multi-step command exits 1 on mid-execution failure with no indication of what completed |
| 1 | Completed steps mentioned in stderr text but not structured; no resume or rollback support |
| 2 | Structured `completed_steps` / `failed_step` in JSON output; exit code distinguishes partial failure |
| 3 | Per-item results for batch commands; `resume_from` token; `--rollback-on-failure` flag; step manifest emitted at start |

**Check:** Trigger a deliberate mid-run failure (e.g., bad step 3 of 5) — the response must contain `partial: true`, list completed steps, and identify where to resume.

---

### Agent Workaround

**Signature:** `exit 1` from a multi-step or batch command whose output shows some steps or items succeeded (`done`, `ok`) before a failure line

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** do not retry the multi-step command; escalate with the command, exit code, stdout, and stderr

**Parse structured partial failure output to determine safe retry scope:**

```python
result = run(["tool", "migrate-database"])
parsed = json.loads(result.stdout)

if parsed.get("partial"):
    completed = parsed.get("completed_steps", [])
    resume_from = parsed.get("resume_from")
    rollback_available = parsed.get("rollback_available", False)

    if rollback_available:
        # Roll back to clean state before retrying from scratch
        run(["tool", "migrate-database", "--rollback"])
    elif resume_from:
        # Resume from the failed step only
        run(["tool", "migrate-database", f"--resume-from={resume_from}"])
    else:
        # No structured resume info — do not retry; requires manual investigation
        raise RuntimeError(f"Partial failure at unknown step. Completed: {completed}")
```

**For batch commands, collect failed IDs and retry only those:**
```python
results = parsed.get("results", [])
failed_ids = [r["id"] for r in results if not r["ok"]]
# Retry only failed items
run(["tool", "send-notifications", "--users", ",".join(map(str, failed_ids))])
```

**Limitation:** If the tool emits only a text error with no structured step information, the agent cannot determine what succeeded — do not retry the full operation without verifying current state first, as re-running completed steps may cause duplicate side effects
