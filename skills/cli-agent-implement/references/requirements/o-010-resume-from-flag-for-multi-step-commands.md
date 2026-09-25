# REQ-O-010: --resume-from Flag for Multi-Step Commands

**Tier:** Opt-In | **Priority:** P2

**Source:** [§13 Partial Failure & Atomicity](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Commands that implement the step manifest contract (REQ-C-008) SHOULD support `--resume-from <step-name>` to resume execution from a specific step, skipping all prior steps. Commands that support this declare `resumable: true`. The framework provides the flag parsing; commands implement the skip logic. The `resume_from` value from a partial failure response is intended to be passed directly as `--resume-from` in a retry.

## Acceptance Criteria

- `--resume-from step-3` begins execution at step 3, having skipped steps 1 and 2
- Skipped steps appear in the response's `skipped_steps` array
- The response `effect` correctly reflects only the work done during the resumed execution
- Passing an invalid step name to `--resume-from` exits `2` with a validation error

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Resumed responses include `data.completed_steps`, `data.skipped_steps`, and `data.failed_step` (if applicable) alongside the standard step summary from REQ-C-009.

---

## Wire Format

```bash
$ tool migrate --resume-from step-3 --format json
```

```json
{
  "ok": true,
  "data": {
    "completed_steps": ["step-3", "step-4", "step-5"],
    "skipped_steps": ["step-1", "step-2"],
    "failed_step": null,
    "effect": "mutating"
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 4210 }
}
```

---

## Example

Opt-in per command by declaring `resumable: true` at registration.

```
register command "migrate":
  resumable: true   # enables --resume-from flag

# After a partial failure at step-3, retry from that step:
$ tool migrate --resume-from step-3
→ skipped_steps: [step-1, step-2]
→ completed_steps: [step-3, step-4, step-5]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-008](c-008-multi-step-commands-emit-step-manifest.md) | C | Provides: step names referenced by `--resume-from` |
| [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) | C | Composes: resumed response includes the same step summary fields |
| [REQ-O-011](o-011-rollback-on-failure-flag.md) | O | Composes: rollback and resume are complementary recovery strategies |
