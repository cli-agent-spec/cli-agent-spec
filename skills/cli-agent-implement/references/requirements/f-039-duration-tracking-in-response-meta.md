# REQ-F-039: Duration Tracking in Response Meta

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) · [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Critical (Time) / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST automatically measure wall-clock execution time for every command and inject `meta.duration_ms` (integer milliseconds) into every response. This timing MUST start when the command begins execution (after framework initialization) and MUST end immediately before JSON serialization. The timing MUST be present on both success and failure responses, including timeout and SIGTERM responses.

## Acceptance Criteria

- Every response (success, failure, timeout, cancellation) includes `meta.duration_ms`
- `meta.duration_ms` is a non-negative integer
- For a command that sleeps 1 second, `meta.duration_ms` is between 1000 and 1200

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.duration_ms` is injected by the framework into every response — success, failure, timeout, and cancellation.

---

## Wire Format

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 1247, "timeout_ms": 30000 }
}
```

Timeout failure (duration still present):

```json
{
  "ok": false,
  "data": null,
  "error": { "code": "TIMEOUT", "message": "Command exceeded timeout of 30000ms" },
  "warnings": [],
  "meta": { "exit_code": 10, "duration_ms": 30041, "timeout_ms": 30000 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework wraps every handler in a timer and injects the result before serialization.

```
# Duration present on all responses — no author code required
$ tool deploy --target staging --output json
→ meta.duration_ms: 1247

# Also on fast validation failures
$ tool deploy --target invalid --output json
→ meta.duration_ms: 8
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Composes: `meta.timeout_ms` and `meta.duration_ms` appear together in every response |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Composes: timeout responses include `duration_ms` at the moment of termination |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `duration_ms` belongs in `meta` (volatile), not `data` (stable) |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Composes: both are framework-injected `meta` fields present on every response |
