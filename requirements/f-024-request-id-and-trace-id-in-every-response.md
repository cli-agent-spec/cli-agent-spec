# REQ-F-024: Request ID and Trace ID in Every Response

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST generate a unique `meta.request_id` for every command invocation. The framework MUST read `TOOL_TRACE_ID` from the environment and propagate it as `meta.trace_id`. Both values MUST appear in every response. The framework MUST include `meta.command` (the command name) and `meta.timestamp` (ISO 8601 invocation time) in every response.

## Acceptance Criteria

- Every response includes `meta.request_id`, which is unique across all invocations
- When `TOOL_TRACE_ID=abc123` is set, every response includes `meta.trace_id: "abc123"`
- `meta.command` matches the name of the command that was invoked
- `meta.timestamp` is a valid ISO 8601 datetime

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.request_id`, `meta.trace_id`, `meta.command`, and `meta.timestamp` are injected by the framework into every response's `meta` object. `meta.trace_id` is only present when `TOOL_TRACE_ID` is set in the environment.

---

## Wire Format

Response `meta` with request ID, trace ID, command, and timestamp:

```json
{
  "ok": true,
  "data": { "id": "cluster-7" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id":     "01HZ3VWKP8Q7RXTGB5M2N6CDEF",
    "trace_id":       "trace-abc-123",
    "command":        "get-cluster",
    "timestamp":      "2024-06-01T12:00:00.000Z",
    "schema_version": "1.0",
    "tool_version":   "2.4.1"
  }
}
```

When `TOOL_TRACE_ID` is not set, `trace_id` is absent:

```json
{
  "meta": {
    "request_id": "01HZ3VWKP8Q7RXTGB5M2N6CDEF",
    "command":    "get-cluster",
    "timestamp":  "2024-06-01T12:00:00.000Z"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework generates a unique `request_id` per invocation and reads `TOOL_TRACE_ID` from the environment at startup.

```
$ TOOL_TRACE_ID=trace-abc-123 tool get-cluster --id 7
→ meta.request_id: "01HZ3VWKP8Q7RXTGB5M2N6CDEF"  ← unique per invocation
→ meta.trace_id:   "trace-abc-123"                 ← propagated from env
→ meta.command:    "get-cluster"
→ meta.timestamp:  "2024-06-01T12:00:00.000Z"

$ tool get-cluster --id 7
→ meta.request_id: "01HZ4NEWDIFFERENTID"
# meta.trace_id absent — TOOL_TRACE_ID not set
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-025](f-025-tool-trace-id-environment-variable-propagation.md) | F | Extends: trace ID propagation to child processes and log entries builds on the value captured here |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `request_id` and `trace_id` are volatile fields and belong in `meta` |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Consumes: audit log entries include `request_id` and `trace_id` from each invocation |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope whose `meta` carries these observability fields |
