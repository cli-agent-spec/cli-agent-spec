# REQ-C-009: Multi-Step Commands Report completed/failed/skipped

**Tier:** Command Contract | **Priority:** P1

**Source:** [§13 Partial Failure & Atomicity](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Any command that operates on a batch of items MUST include a `summary` object in its response containing `total`, `succeeded`, and `failed` integer counts. For each individual item that failed, the response MUST include per-item error details within `results[]`. This MUST allow a caller to determine exactly which items succeeded and which failed, enabling safe retry of only the failed items.

## Acceptance Criteria

- A batch command response includes `summary.total`, `summary.succeeded`, `summary.failed`
- Each item in `results[]` includes `ok: true/false` and, when false, an `error` object
- The item-level `error` object follows the standard error structure (code, message, retryable)
- The exit code for a partial batch success is non-zero (not `0`)

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Batch commands include a `summary` object and a `results` array in the response `data`.

```json
{
  "summary": {
    "type": "object",
    "required": ["total", "succeeded", "failed"],
    "properties": {
      "total":     { "type": "integer", "description": "Total number of items in the batch" },
      "succeeded": { "type": "integer", "description": "Items that completed successfully" },
      "failed":    { "type": "integer", "description": "Items that failed" }
    },
    "description": "Aggregate counts for the batch operation"
  },
  "results": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["id", "ok"],
      "properties": {
        "id":    { "description": "Identifier of the item" },
        "ok":    { "type": "boolean", "description": "Whether this item succeeded" },
        "error": { "description": "Error detail when ok is false; follows standard error structure" }
      }
    },
    "description": "Per-item results enabling safe retry of only the failed items"
  }
}
```

---

## Wire Format

```bash
$ tool send-notifications --users 1,2,3,4,5
```

```json
{
  "ok": false,
  "data": {
    "partial": true,
    "summary": { "total": 5, "succeeded": 3, "failed": 2 },
    "results": [
      { "id": 1, "ok": true,  "effect": "sent" },
      { "id": 2, "ok": true,  "effect": "sent" },
      { "id": 3, "ok": false, "error": { "code": "INVALID_EMAIL",  "message": "Invalid email address", "retryable": false } },
      { "id": 4, "ok": true,  "effect": "sent" },
      { "id": 5, "ok": false, "error": { "code": "RATE_LIMITED",   "message": "Rate limit exceeded",   "retryable": true  } }
    ]
  },
  "error": { "code": "PARTIAL_FAILURE", "message": "2 of 5 notifications failed" },
  "warnings": [],
  "meta": { "duration_ms": 312 }
}
```

Exit code: `3` (`PARTIAL_FAILURE`).

---

## Example

A batch command iterates items, captures per-item errors, and always returns the structured summary even on partial success.

```
register command "send-notifications":
  danger_level: mutating
  exit_codes:
    SUCCESS        (0): description: "All notifications sent",       retryable: false, side_effects: complete
    PARTIAL_FAILURE(3): description: "Some notifications failed",    retryable: false, side_effects: partial
    ARG_ERROR      (2): description: "Invalid --users value",        retryable: false, side_effects: none

  execute(args):
    results = []
    for user_id in args.users:
      try:
        send(user_id)
        results.append(id=user_id, ok=True, effect="sent")
      except Exception as e:
        results.append(id=user_id, ok=False, error=classify(e))
    failed = [r for r in results if not r.ok]
    exit_code = PARTIAL_FAILURE if failed else SUCCESS
    return response(exit_code, partial=bool(failed),
                    summary={total: len(results), succeeded: len(results)-len(failed), failed: len(failed)},
                    results=results)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-008](c-008-multi-step-commands-emit-step-manifest.md) | C | Composes: `completed_steps`/`failed_step` for sequential multi-step commands; `summary`/`results` for batch commands |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Enforces: per-item `error` objects follow the same structure as top-level error responses |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `PARTIAL_FAILURE (3)` is the correct exit code for partial batch success |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `summary` and `results` are carried inside `ResponseEnvelope.data` |
