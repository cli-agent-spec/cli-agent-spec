# REQ-O-011: --rollback-on-failure Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§13 Partial Failure & Atomicity](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Commands that support rollback MUST declare `rollback_available: true` and implement a `rollback()` hook. The framework MUST provide `--rollback-on-failure` as a standard flag for such commands. When this flag is passed and a step fails, the framework invokes the command's `rollback()` hook before exiting. The response MUST indicate whether rollback succeeded via `rollback_status: "completed" | "failed" | "not_attempted"`.

## Acceptance Criteria

- `--rollback-on-failure` with a mid-step failure triggers the `rollback()` hook
- The response includes `rollback_status`
- A rollback failure is reported with `rollback_status: "failed"` and details in the response
- The exit code after a failed step with successful rollback is `3` (not `0`)

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Rollback responses include `data.rollback_status` (`"completed"` | `"failed"` | `"not_attempted"`) and optionally `data.rollback_error` when rollback itself fails.

---

## Wire Format

```bash
$ tool deploy --rollback-on-failure --output json
```

Failed deployment with successful rollback:

```json
{
  "ok": false,
  "data": {
    "completed_steps": ["step-1", "step-2"],
    "failed_step": "step-3",
    "rollback_status": "completed"
  },
  "error": { "code": "PARTIAL_FAILURE", "message": "Deployment failed at step-3; rollback completed" },
  "warnings": [],
  "meta": { "exit_code": 3, "duration_ms": 8320 }
}
```

---

## Example

Opt-in per command by declaring `rollback_available: true` and implementing a `rollback()` hook.

```
register command "deploy":
  rollback_available: true
  rollback: rollback_deploy   # hook function

# Agent retries with rollback safety:
$ tool deploy --rollback-on-failure
→ on failure: rollback() called before exit
→ data.rollback_status: "completed"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-008](c-008-multi-step-commands-emit-step-manifest.md) | C | Provides: step manifest that rollback uses to undo completed steps |
| [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) | C | Composes: step summary in the response indicates what rollback had to undo |
| [REQ-O-010](o-010-resume-from-flag-for-multi-step-commands.md) | O | Composes: resume and rollback are complementary recovery strategies |
