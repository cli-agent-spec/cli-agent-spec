# REQ-C-014: Error Responses Include retryable and retry_after_ms

**Tier:** Command Contract | **Priority:** P1

**Source:** [§19 Retry Hints in Error Responses](../challenges/06-high-errors-and-discoverability/19-high-retry-hints.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

Every error response MUST include `error.retryable` (boolean): `true` only when re-running the identical invocation, unchanged, may succeed and no side effects occurred. Failures the caller can correct (invalid input, expired credentials, unmet preconditions) MUST set `retryable: false` and SHOULD include `error.fix_required` (string) stating the condition to correct before reissuing. For retryable errors, the response SHOULD include `error.retry_after_ms` (integer milliseconds to wait before retrying) and `error.retry_strategy` (one of: `"immediate"`, `"linear_backoff"`, `"exponential_backoff"`). The framework MUST maintain a default `retryable` value for each error code in its error registry, which commands inherit unless overridden.

## Acceptance Criteria

- Every error response includes `error.retryable` as a boolean
- A `RATE_LIMITED` error includes `error.retry_after_ms > 0`
- A `VALIDATION_ERROR` error has `error.retryable: false` and `error.fix_required` present
- A `TIMEOUT` error's `retryable` equals the `retryable` of the command's declared `TIMEOUT` entry; when the entry declares `side_effects: "partial"`, `retryable` MUST be `false`. `side_effects: "none"` permits `retryable: true` but does not imply it
- A command whose run length depends on its input declares `TIMEOUT` with `retryable: false, side_effects: "none"`, and its `TIMEOUT` error carries `error.fix_required` naming a larger `--timeout`
- The framework error registry maps all standard error codes to default `retryable` values

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

This requirement extends `ResponseEnvelope.ErrorDetail` with the following required/recommended fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.retryable` | boolean | yes | Whether the identical unchanged invocation may succeed on re-run; `true` implies no side effects occurred |
| `error.retry_after_ms` | integer | when `retryable: true` | Milliseconds the agent should wait before retrying |
| `error.retry_strategy` | `"immediate"` \| `"linear_backoff"` \| `"exponential_backoff"` | recommended | Backoff strategy to apply |
| `error.fix_required` | string | when the failure is caller-correctable | Condition to correct before reissuing; absent on terminal failures |

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
  "meta": { "exit_code": 11, "duration_ms": 8 }
}
```

Timeout error from a command that declared `TIMEOUT` with `retryable: true, side_effects: "none"` (a transient stall the identical re-run can clear; retryable, no delay):

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
  "meta": { "exit_code": 10, "duration_ms": 30001 }
}
```

Timeout error from a read-only command whose run length depends on its input, declared `TIMEOUT` with `retryable: false, side_effects: "none"` (the identical re-run times out again; raise `--timeout`, then reissue):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "TIMEOUT",
    "message": "Scan of 48213 files exceeded the 30 s timeout",
    "retryable": false,
    "fix_required": "Reissue with a larger --timeout, such as --timeout 300s",
    "phase": "execution"
  },
  "warnings": [],
  "meta": { "exit_code": 10, "duration_ms": 30004, "timeout_ms": 30000 }
}
```

Validation error (identical retry fails; fix the input, then reissue):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_ENVIRONMENT",
    "message": "Unknown target 'prodution'",
    "retryable": false,
    "fix_required": "Correct the target environment argument",
    "phase": "validation",
    "suggestion": "Valid values: prod, staging, dev"
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 3 }
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
    ARG_ERROR(2): retryable: false, side_effects: none

register command "scan":       # read-only; run length grows with the input
  exit_codes:
    TIMEOUT (10): retryable: false, side_effects: none   # same input, same timeout
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Extends: adds `retryable` and `retry_after_ms` to the error object defined there |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Sources: `retryable` default for each error code comes from the exit code declaration |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: standard `TIMEOUT` and `RATE_LIMITED` codes whose default `retryable` values this requirement governs |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `error.retryable` and `error.retry_after_ms` are fields within `ResponseEnvelope.ErrorDetail` |
