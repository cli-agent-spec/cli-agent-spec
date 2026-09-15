# REQ-F-033: Lock Acquisition with Timeout and retry_after_ms

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§15 Race Conditions & Concurrency](../challenges/02-critical-execution-and-reliability/15-high-race-conditions.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

When a command acquires a framework-managed advisory lock, the framework MUST enforce a configurable acquisition timeout. If the lock cannot be acquired within the timeout, the framework MUST emit a structured JSON error containing `"code": "LOCK_HELD"`, the PID and age of the lock holder, and a `retry_after_ms` value. Lock files MUST be released by the framework's exit and SIGTERM handlers.

## Acceptance Criteria

- A command waiting for a held lock exits with a `LOCK_HELD` JSON error after the configured timeout
- The error includes `retry_after_ms`
- The lock is released when the holding process exits normally
- The lock is released when the holding process receives SIGTERM

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

Lock contention errors use `ErrorDetail` with `retry_after_ms` as an additional field in the `error` object

---

## Wire Format

Lock contention error response:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "LOCK_HELD",
    "message": "Resource lock held by PID 9001 (age: 12s) — acquisition timed out after 10s",
    "retryable": true,
    "retry_after_ms": 3000,
    "detail": "lock_file=/tmp/mytool/locks/deploy.lock holder_pid=9001 holder_age_ms=12048"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 10002, "request_id": "req_01HZ" }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework wraps any lock acquisition declared by the command with a configurable timeout. On timeout, the framework emits the `LOCK_HELD` error and exits with `PRECONDITION (4)`.

```
$ tool deploy --env prod &   (acquires lock, PID 9001)
$ tool deploy --env prod     (second instance — lock contention)
→ waits up to configured timeout (default 10s)
→ lock not acquired within 10s
→ exit code: 4
→ stdout:
  {"ok":false,"data":null,"error":{"code":"LOCK_HELD","message":"...","retryable":true,"retry_after_ms":3000},...}

$ kill 9001   (lock holder exits)
→ lock file removed by framework exit handler
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM handler releases locks before forwarding to children |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Composes: lock files may reside in or alongside the session temp directory |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope structure carrying the `LOCK_HELD` error |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `PRECONDITION (4)` exit code used for lock timeout |
