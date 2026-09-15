# REQ-F-011: Default Timeout Per Command

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST apply a default wall-clock timeout to every command execution. The default value MUST be configurable at the framework level and overridable per command. A command that exceeds its timeout MUST be terminated by the framework, not left to run indefinitely. The timeout MUST be enforced even if the command itself does not implement any timeout logic.

## Acceptance Criteria

- A command that sleeps indefinitely exits within `default_timeout + 5s` without manual intervention
- The framework's timeout mechanism works even if the command's code is blocked on I/O
- The timeout value used for each execution is recorded in `meta.timeout_ms`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The `ResponseMeta` object carries `timeout_ms` to record the configured limit for the execution. This field is always populated by the framework, regardless of whether the timeout was reached.

---

## Wire Format

`meta.timeout_ms` appears in every response, recording the configured timeout for that execution:

```json
{
  "ok": true,
  "data": { "status": "synced", "records": 42 },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 1240,
    "timeout_ms": 30000
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework wraps every command invocation in a timeout enforcer and records the configured limit in `meta`.

```
# Framework-level default (e.g., 30s)
app = Framework("tool", default_timeout_ms=30000)

# Per-command override at registration
register command "import":
  timeout_ms: 300000   # 5 minutes for long-running import

# Every response includes the active timeout limit
meta.timeout_ms = 300000   # import command
meta.timeout_ms = 30000    # all other commands
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Specializes: defines the error response and exit code when the timeout fires |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: `timeout_ms` is added to `ResponseMeta` in the standard envelope |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `TIMEOUT (10)` is the exit code emitted when the limit is exceeded |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: commands that can time out must declare `TIMEOUT (10)` in their exit code map |
