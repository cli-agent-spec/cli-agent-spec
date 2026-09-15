# REQ-C-013: Error Responses Include Code and Message

**Tier:** Command Contract | **Priority:** P0

**Source:** [§18 Error Message Quality](../challenges/06-high-errors-and-discoverability/18-high-error-quality.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: High

---

## Description

Every error response MUST include an `error` object with: `code` (string, `DOMAIN_NOUN_CONDITION` format, machine-readable), `message` (string, human-readable, complete sentence), and optionally `cause` (the underlying system error), `suggestion` (an actionable next step), `docs_url` (a URL to documentation), and `context` (an object of relevant key-value pairs). Stack traces MUST NOT appear in `error.message` or any stdout field; they MUST be sent only to stderr or a log file.

## Acceptance Criteria

- Every non-zero exit code response includes a non-null `error` object
- `error.code` matches the pattern `[A-Z][A-Z0-9_]+`
- `error.message` is a complete human-readable sentence
- No stack trace text appears anywhere in stdout output
- `error.suggestion` is present for all errors the command author classifies as recoverable

---

## Schema

**Types:** [`exit-code.md`](../schemas/exit-code.md) · [`response-envelope.md`](../schemas/response-envelope.md) — `error.code` is a stable domain code that may equal an `ExitCode` name (`NOT_FOUND`) or refine it (`CONNECTION_REFUSED`); the exit code itself travels in `meta.exit_code`. The full error object is defined in `ResponseEnvelope.ErrorDetail`

---

## Wire Format

```bash
$ tool connect --host db.example.com
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "CONNECTION_REFUSED",
    "message": "Cannot connect to database at db.example.com:5432.",
    "cause": "Connection refused (ECONNREFUSED)",
    "suggestion": "Verify the database is running: `tool db status`",
    "docs_url": "https://docs.example.com/errors/CONNECTION_REFUSED",
    "context": {
      "host": "db.example.com",
      "port": 5432,
      "timeout_ms": 5000
    }
  },
  "warnings": [],
  "meta": { "exit_code": 12, "duration_ms": 5003 }
}
```

Exit code: `12` (`UNAVAILABLE`). No stack trace in `stdout`.

---

## Example

A command author maps internal exceptions to structured error objects, providing `code`, `message`, and — for recoverable errors — `suggestion` and `context`.

```
register command "connect":
  danger_level: safe
  has_network_io: true
  exit_codes:
    SUCCESS   (0):  description: "Connection established",             retryable: false, side_effects: none
    UNAVAILABLE(12): description: "Remote host could not be reached",  retryable: true,  side_effects: none
    AUTH_REQUIRED(8): description: "Credentials missing or expired",   retryable: true,  side_effects: none

  execute(args):
    try:
      connect(args.host, args.port)
    except ConnectionRefused as e:
      raise StructuredError(
        code="CONNECTION_REFUSED",
        message="Cannot connect to database at {}:{}.".format(args.host, args.port),
        cause=str(e),
        suggestion="Verify the database is running: `tool db status`",
        docs_url="https://docs.example.com/errors/CONNECTION_REFUSED",
        context={"host": args.host, "port": args.port, "timeout_ms": args.timeout_ms},
        exit_code=UNAVAILABLE,
      )
    except AuthError as e:
      raise StructuredError(
        code="AUTH_TOKEN_EXPIRED",
        message="Credentials are missing or expired.",
        suggestion="Run `tool login` to refresh your credentials",
        exit_code=AUTH_REQUIRED,
      )
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope.ErrorDetail` is the schema type carrying all fields defined here |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ExitCode` names that `error.code` may reuse for well-known failure categories |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: the exit code in `meta.exit_code` must be declared in the command's `exit_codes` map |
| [REQ-C-014](c-014-error-responses-include-retryable-and-retry-after-.md) | C | Extends: adds `retryable` and `retry_after_ms` fields to the error object defined here |
