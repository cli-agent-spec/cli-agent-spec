# REQ-C-028: ALREADY_EXISTS Response Pattern

**Tier:** Command Contract | **Priority:** P1

**Source:** Silent assumption — agents retry failed creates; if create fails because the resource already exists, the agent needs the existing resource returned so it can proceed without a separate get call

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Commands that create resources MUST handle the "resource already exists" case by returning a structured `ALREADY_EXISTS` response — not a generic error. The response MUST include the existing resource in the `data` field (identical to what a `get` command would return), set `"ok": false`, exit `6` (`CONFLICT`) with `error.code: "ALREADY_EXISTS"`, and set `"retryable": false`.

This pattern allows agents that retry failed creates to recover gracefully: they receive the existing resource and can proceed as if the create succeeded. Without this pattern, agents must make a separate `get` call after every create failure to determine whether the failure was a conflict or a genuine error.

The inverse — delete on a non-existent resource — MUST exit `0` with `{"ok": true, "data": {"status": "not_found"}}`.

## Acceptance Criteria

- `tool resource create --name foo` called twice returns the resource on both calls
- Second call: `"ok": false`, exit `6` (`CONFLICT`), `error.code: "ALREADY_EXISTS"`, `data` contains the existing resource
- Agent can use `data` from the second call directly without a follow-up `get`
- Delete of non-existent resource exits `0` with structured `not_found` confirmation
- `CONFLICT (6)` is declared in the command's exit code table with a description naming the already-exists case

---

## Schema

[`exit-code-entry.md`](../schemas/exit-code-entry.md) — commands declare `CONFLICT (6)` for the already-exists case · [`response-envelope.md`](../schemas/response-envelope.md) — `data` carries the existing resource as a declared failure payload

---

## Wire Format

Create called on existing resource:

```json
{
  "ok": false,
  "data": {
    "id": "res_123",
    "name": "foo",
    "created_at": "2026-01-01T00:00:00Z",
    "status": "active"
  },
  "error": {
    "code": "ALREADY_EXISTS",
    "message": "Resource 'foo' already exists",
    "retryable": false,
    "conflict_id": "res_123"
  },
  "warnings": [],
  "meta": { "exit_code": 6, "duration_ms": 41 }
}
```

Delete called on non-existent resource:

```json
{
  "ok": true,
  "data": {"status": "not_found", "id": "res_999"},
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 37 }
}
```

---

## Example

Agent create-or-get pattern:

```python
result = run("tool resource create --name foo")
if result.exit_code == 0:
    resource = result.data          # newly created
elif result.error.code == "ALREADY_EXISTS":
    resource = result.data          # existing — no extra get call needed
else:
    raise result.error              # genuine failure
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Composes: idempotency key prevents ALREADY_EXISTS on intentional retries |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Provides: effect field distinguishes create (non-idempotent) from apply (idempotent) |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Provides: ALREADY_EXISTS exit code must be declared in the command's exit code table |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries the existing resource in data on conflict |
