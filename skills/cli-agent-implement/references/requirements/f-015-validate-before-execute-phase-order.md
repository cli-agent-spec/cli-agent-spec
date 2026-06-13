# REQ-F-015: Validate-Before-Execute Phase Order

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§14 Argument Validation Before Side Effects](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST enforce a strict two-phase execution model for every command: all registered `validate()` hooks MUST complete successfully before any registered `execute()` hook is called. The framework MUST make it structurally impossible for a command to initiate a side effect inside a validation hook. Validation errors MUST be collected in full (all errors, not just the first) before reporting.

## Acceptance Criteria

- A command with two validation errors reports both in a single invocation (not one per run).
- A command that fails validation never writes to the filesystem, network, or any external state.
- The framework raises a registration error if a command registers an `execute()` hook that is called before all `validate()` hooks complete.
- Validation failures always exit with code `2`.

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Validation error responses MUST include `"phase": "validation"` in the `error` object, and MUST collect all validation errors before reporting (see `errors` array):

```json
{
  "error": {
    "code": "ARG_ERROR",
    "message": "Validation failed",
    "phase": "validation",
    "errors": [
      { "field": "env",  "message": "Unknown environment: staging2" },
      { "field": "replicas", "message": "Must be a positive integer" }
    ]
  }
}
```

---

## Wire Format

Validation failure response (exit code `2`):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "ARG_ERROR",
    "message": "Validation failed",
    "phase": "validation",
    "errors": [
      { "field": "env",      "message": "Unknown environment: staging2" },
      { "field": "replicas", "message": "Must be a positive integer" }
    ]
  },
  "warnings": [],
  "meta": {
    "request_id": "req_01HZ",
    "command": "deploy",
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework enforces the phase boundary structurally — `execute()` hooks are never called until all `validate()` hooks return success.

```
$ tool deploy --env staging2 --replicas -1
→ exit code: 2
→ stdout: {
    "ok": false,
    "error": {
      "code": "ARG_ERROR",
      "phase": "validation",
      "errors": [
        {"field": "env",      "message": "Unknown environment: staging2"},
        {"field": "replicas", "message": "Must be a positive integer"}
      ]
    }
  }
# No filesystem write occurred — both errors reported in one run
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: exit code `2` guarantee depends on this phase boundary |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ARG_ERROR (2)` and `PARTIAL_FAILURE (3)` constants used in validation errors |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope structure that carries the validation error |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: commands must declare `ARG_ERROR` in their exit code map |
