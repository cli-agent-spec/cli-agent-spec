# REQ-F-026: Append-Only Audit Log

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST write an append-only audit log entry for every command invocation to a JSONL file at a well-known, configurable path (default: `~/.local/share/<toolname>/audit.jsonl`). Each entry MUST include: timestamp, command name, sanitized arguments (with secret fields redacted), exit code, duration_ms, trace_id, and request_id. The audit log MUST be written regardless of whether the command succeeded or failed.

## Acceptance Criteria

- After any command invocation, the audit log file contains a new JSONL entry
- The entry for a command invoked with a secret argument does not contain the secret value
- The audit log is valid JSONL (one JSON object per line, newline-delimited)
- The audit log is written even when the command exits non-zero

---

## Schema

No dedicated schema type — this requirement governs audit log file writes without adding new wire-format fields to the response envelope beyond `meta.audit_log_path`

---

## Wire Format

`meta.audit_log_path` in the response envelope when the log is active:

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 412,
    "request_id": "req_01HZ",
    "audit_log_path": "/home/user/.local/share/mytool/audit.jsonl"
  }
}
```

Corresponding JSONL entry written to the audit log:

```json
{"timestamp":"2024-06-01T12:00:00Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,"duration_ms":412,"trace_id":"trace_abc","request_id":"req_01HZ"}
```

---

## Example

Framework-Automatic: no command author action needed. The framework opens the audit log file in append mode before dispatching any command and writes one JSONL entry after the command exits, regardless of exit code.

```
$ tool deploy --env prod --token abc123
→ audit.jsonl appended:
  {"timestamp":"2024-06-01T12:00:00Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,"duration_ms":412,...}

$ tool deploy --env bad
→ exit code: 3
→ audit.jsonl appended:
  {"timestamp":"2024-06-01T12:00:01Z","command":"deploy","args":{"env":"bad"},"exit_code":3,"duration_ms":5,...}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret fields are redacted in every audit log entry |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Provides: `duration_ms` value written to each audit log entry |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `request_id` and `trace_id` values written to each audit log entry |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: `meta.audit_log_path` is an extension of the standard response meta |
