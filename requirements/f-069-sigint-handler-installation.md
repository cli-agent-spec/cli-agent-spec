# REQ-F-069: SIGINT Handler Installation

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** Silent assumption — agents send SIGINT to cancel running commands and expect exit code 130 (128 + SIGINT), not 1

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST install a SIGINT signal handler for every command at startup. On SIGINT, the handler MUST: invoke the command's registered `cleanup()` hook, release any framework-managed locks, emit a cancellation JSON object to stdout (with `"ok": false`, `"error": {"code": "CANCELLED", "signal": "SIGINT"}`), flush stdout, and exit with code `130` (128 + SIGINT). The handler MUST be re-entrant safe — a second SIGINT during cleanup exits immediately without a double-write.

Agents that enforce time budgets by sending SIGINT (Ctrl+C equivalent) rely on exit code `130` to distinguish "I cancelled this" from "this failed" (exit `1`). An uncaught SIGINT that produces exit `1` causes the agent to retry the cancelled operation, compounding side effects.

## Acceptance Criteria

- `kill -INT <pid>` on a running command produces a valid JSON cancellation response on stdout
- Exit code after SIGINT is exactly `130`
- All framework-managed lock files are released after SIGINT
- A second SIGINT during cleanup exits immediately with `130`, no duplicate JSON output
- The framework adds `"130"` to every command's `exit_codes` map with `retryable: false` and `side_effects: "partial"`; signal exits are the only sanctioned use of the shell-reserved range (REQ-F-001)

---

## Schema

No dedicated schema type — cancellation response uses `response-envelope` with `"ok": false`

---

## Wire Format

Cancellation response emitted to stdout on SIGINT:

```json
{
  "ok": false,
  "data": { "partial": true },
  "error": {
    "code": "CANCELLED",
    "message": "Command cancelled by SIGINT",
    "retryable": false,
    "phase": "execution",
    "context": { "signal": "SIGINT" }
  },
  "warnings": [],
  "meta": {
    "exit_code": 130,
    "duration_ms": 12,
    "request_id": "req_01HZ",
    "command": "deploy",
    "timestamp": "2026-04-01T12:00:00Z"
  }
}
```

---

## Example

```
$ tool deploy --env prod &
[1] 12345
$ kill -INT 12345
→ stdout: {"ok":false,"partial":true,"data":null,"error":{"code":"CANCELLED","signal":"SIGINT"},...}
→ exit code: 130
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Specializes: SIGTERM handler; SIGINT follows identical pattern with exit code 130 instead of 143 |
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | F | Extends: SIGINT must also forward to tracked child processes |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: exit code 130 (128 + SIGINT) as a framework-defined constant |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope used by the cancellation JSON output |
