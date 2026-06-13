# REQ-C-014: Error Responses Include retryable and retry_after_ms

**Tier:** Command Contract | **Priority:** P1

**Source:** [§19 Retry Hints in Error Responses](../challenges/06-high-errors-and-discoverability/19-high-retry-hints.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

Every error response MUST include `error.retryable` (boolean or the string `"maybe"`) indicating whether the same invocation with identical arguments is safe to retry. For retryable errors, the response SHOULD include `error.retry_after_ms` (integer milliseconds to wait before retrying) and `error.retry_strategy` (one of: `"immediate"`, `"linear_backoff"`, `"exponential_backoff"`). The framework MUST maintain a default `retryable` value for each error code in its error registry, which commands inherit unless overridden.

## Acceptance Criteria

- Every error response includes `error.retryable`
- A `RATE_LIMITED` error includes `error.retry_after_ms > 0`
- A `VALIDATION_ERROR` error has `error.retryable: true`
- A `TIMEOUT` error has `error.retryable: true` by default; commands that declare `side_effects: "partial"` for `TIMEOUT` MUST override to `retryable: false`
- The framework error registry maps all standard error codes to default `retryable` values

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

This requirement extends `ResponseEnvelope.ErrorDetail` with the following required/recommended fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.retryable` | boolean \| `"maybe"` | yes | Whether the identical invocation is safe to retry |
| `error.retry_after_ms` | integer | when `retryable: true` | Milliseconds the agent should wait before retrying |
| `error.retry_strategy` | `"immediate"` \| `"linear_backoff"` \| `"exponential_backoff"` | recommended | Backoff strategy to apply |

---

## Wire Format

```bash
$ tool deploy --target prod
```
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit reached — too many requests in the last 60 seconds",
    "retryable": true,
    "retry_after_ms": 30000,
    "retry_strategy": "exponential_backoff"
  },
  "warnings": [],
  "meta": { "duration_ms": 8 }
}
```

Timeout error (retryable, no delay):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "OPERATION_TIMEOUT",
    "message": "Command exceeded the 30 s timeout",
    "retryable": true,
    "retry_after_ms": 0,
    "retry_strategy": "immediate"
  },
  "warnings": [],
  "meta": { "duration_ms": 30001 }
}
```

Validation error (retryable after correcting input):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_ENVIRONMENT",
    "message": "Unknown target 'prodution'",
    "retryable": true,
    "phase": "validation",
    "suggestion": "Valid values: prod, staging, dev"
  },
  "warnings": [],
  "meta": { "duration_ms": 3 }
}
```

---

## Example

The command author explicitly declares exit code behavior at registration time, overriding framework defaults where appropriate:

```
register command "deploy":
  exit_codes:
    SUCCESS  (0): retryable: false, side_effects: complete
    TIMEOUT (10): retryable: false, side_effects: partial
    RATE_LIMITED(11): retryable: true, side_effects: none,
                      retry_after_ms: 30000, retry_strategy: exponential_backoff
    ARG_ERROR(2): retryable: true,  side_effects: none
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Extends: adds `retryable` and `retry_after_ms` to the error object defined there |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Sources: `retryable` default for each error code comes from the exit code declaration |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: standard `TIMEOUT` and `RATE_LIMITED` codes whose default `retryable` values this requirement governs |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `error.retryable` and `error.retry_after_ms` are fields within `ResponseEnvelope.ErrorDetail` |
