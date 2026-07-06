# REQ-F-012: Timeout Exit Code and JSON Error

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

When the framework's timeout fires, it MUST emit a structured JSON error to stdout before terminating the process, and MUST exit with code `10` (`TIMEOUT`). The error MUST include `"code": "TIMEOUT"`, the configured timeout value, and any partial progress information available from the command's registered state. The `error.retryable` value MUST be sourced from the command's declared `TIMEOUT` `ExitCodeEntry`: `true` only when the entry declares `side_effects: "none"`. The framework MUST never produce an empty stdout on timeout.

## Acceptance Criteria

- A timed-out command's stdout is valid JSON containing `"ok": false` and `"error": {"code": "TIMEOUT"}`
- Exit code is exactly `10` after timeout
- `meta.duration_ms` is populated with the actual elapsed time
- If the command emitted a step manifest (see REQ-C-008), `completed_steps` is included in the timeout error

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`exit-code.md`](../schemas/exit-code.md)

The framework emits a `ResponseEnvelope` with `ok: false` and `error.code = "TIMEOUT"` before terminating the process. Exit code is `TIMEOUT (10)` from the standard table.

---

## Wire Format

JSON error response emitted to stdout before the process exits with code `10`. Here the command declared `TIMEOUT` with `side_effects: "none"` (read-only), so the framework sets `retryable: true`:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "TIMEOUT",
    "message": "Command exceeded timeout of 30000ms",
    "retryable": true,
    "phase": "execution"
  },
  "warnings": [],
  "meta": {
    "duration_ms": 30012,
    "timeout_ms": 30000
  }
}
```

With partial step progress (when REQ-C-008 step manifest was emitted). Partial writes occurred, so `retryable` is `false` — the agent inspects `completed_steps` and resumes instead of blindly re-running:

```json
{
  "ok": false,
  "data": { "completed_steps": ["validate", "download"], "pending_steps": ["install", "activate"] },
  "error": {
    "code": "TIMEOUT",
    "message": "Command exceeded timeout of 30000ms",
    "retryable": false,
    "phase": "execution"
  },
  "warnings": [],
  "meta": { "duration_ms": 30015, "timeout_ms": 30000 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework's timeout watchdog fires, writes the JSON error to stdout, then terminates the process.

```
# Command is mid-execution when the 30s timeout fires
Framework timeout watchdog:
  1. Collect any completed_steps from command state
  2. Write JSON error to stdout (before terminating)
  3. Exit with code 10 (TIMEOUT)

# Agent receives:
exit code: 10
stdout: {"ok":false,"data":null,"error":{"code":"TIMEOUT",...},...}

# Agent knows:
# - error.retryable mirrors the command's TIMEOUT declaration:
#     true  → side_effects: "none" declared; re-run directly after back-off
#     false → partial writes possible; inspect state (completed_steps) first
# - error.phase: "execution" → the timeout fired mid-operation
# - meta.duration_ms → actual elapsed time before termination
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Provides: the default timeout value that triggers this error |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `TIMEOUT (10)` constant used as the process exit code |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: timeout error uses the standard `ResponseEnvelope` |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Consumes: commands must declare `TIMEOUT (10)` if they can be subject to the timeout |
