# REQ-O-030: tool audit-log Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST provide a built-in `tool audit-log` command that queries the audit log (REQ-F-026). The command MUST accept `--since <duration or ISO datetime>`, `--command <name>`, `--trace-id <id>`, `--output jsonl`, and `--limit <n>`. Each returned entry MUST contain: timestamp, command, sanitized parameters, exit code, duration_ms, trace_id, request_id, and operator (session identifier if available).

## Acceptance Criteria

- `tool audit-log --since 1h --output jsonl` returns all invocations from the past hour, one per line
- `tool audit-log --trace-id abc123` returns only entries with that trace ID
- Secret field values are redacted in all audit log query results
- `--limit 100` returns at most 100 entries

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.entries` is an array of audit log entry objects with `timestamp`, `command`, `parameters`, `exit_code`, `duration_ms`, `trace_id`, and `request_id`.

---

## Wire Format

```bash
$ tool audit-log --since 1h --output jsonl
```

```
{"timestamp":"2026-03-17T14:00:01Z","command":"deploy","parameters":{"target":"staging"},"exit_code":0,"duration_ms":1247,"trace_id":"abc123","request_id":"req-001"}
{"timestamp":"2026-03-17T14:05:22Z","command":"delete","parameters":{"resource_id":"***"},"exit_code":5,"duration_ms":8,"trace_id":"def456","request_id":"req-002"}
```

---

## Example

Opt-in at the framework level; requires REQ-F-026 (append-only audit log) to be active.

```
app = Framework("tool")
app.enable_audit_log()   # requires f-026 audit log

# Query last hour of activity for a specific trace:
$ tool audit-log --since 1h --trace-id abc123 --output jsonl

# Verify no secrets leaked into audit log parameters:
$ tool audit-log --since 24h | jq '.data.entries[] | .parameters'
# → secret fields appear as "***"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Provides: the audit log that this command queries |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `trace_id` and `request_id` values stored in the audit log |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret fields are redacted in audit log entries |
