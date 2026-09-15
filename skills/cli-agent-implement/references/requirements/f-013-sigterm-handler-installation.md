# REQ-F-013: SIGTERM Handler Installation

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§16 Signal Handling & Graceful Cancellation](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST install a SIGTERM signal handler for every command at startup. On SIGTERM, the handler MUST: invoke the command's registered `cleanup()` hook, release any framework-managed locks, emit a partial-result JSON object to stdout (with `"ok": false`, `"partial": true`, `"error": {"code": "CANCELLED"}`), flush stdout, and exit with code `143` (128 + SIGTERM). The handler MUST be re-entrant safe (a second SIGTERM during cleanup MUST not cause a double-write).

## Acceptance Criteria

- `kill -TERM <pid>` on a running command causes stdout to contain a valid JSON cancellation response
- Exit code after SIGTERM is exactly `143`
- All framework-managed lock files are released after SIGTERM
- A second SIGTERM during cleanup does not produce duplicate JSON output

---

## Schema

No dedicated schema type — this requirement governs signal handler installation and cancellation response behavior without adding new wire-format fields beyond what `response-envelope.md` already defines

---

## Wire Format

Cancellation response emitted to stdout on SIGTERM:

```json
{
  "ok": false,
  "data": { "partial": true },
  "error": {
    "code": "CANCELLED",
    "message": "Command cancelled by SIGTERM",
    "retryable": false,
    "phase": "execution"
  },
  "warnings": [],
  "meta": {
    "exit_code": 143,
    "duration_ms": 12,
    "request_id": "req_01HZ",
    "command": "deploy",
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework installs a SIGTERM handler before dispatching the command. On receipt of `SIGTERM`, the framework invokes the command's registered `cleanup()` hook, releases locks, emits the cancellation JSON, flushes stdout, and exits with code `143`.

```
$ tool deploy --env prod &
[1] 12345
$ kill -TERM 12345
→ stdout: {"ok":false,"partial":true,"data":null,"error":{"code":"CANCELLED","message":"Command cancelled by SIGTERM"},...}
→ exit code: 143
```

A second SIGTERM during cleanup is ignored — the handler sets a guard flag on first invocation.

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | F | Extends: forwards SIGTERM to all tracked child processes before emitting cancellation JSON |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Provides: session tracking that the SIGTERM handler uses to find children to signal |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope structure used by the cancellation JSON output |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: exit code `143` (128 + SIGTERM) is a framework-defined constant |
