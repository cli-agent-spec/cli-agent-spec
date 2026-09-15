# REQ-F-025: TOOL_TRACE_ID Environment Variable Propagation

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST read `TOOL_TRACE_ID` from the environment at startup and associate it with the current invocation. The framework MUST also pass `TOOL_TRACE_ID` to all child processes spawned during the command. All internal framework log entries written to stderr and the audit log MUST include the trace ID when set.

## Acceptance Criteria

- A child process spawned by the framework inherits `TOOL_TRACE_ID`
- Framework-emitted log lines (stderr) include the trace ID when `TOOL_TRACE_ID` is set
- Audit log entries include the trace ID

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.trace_id` in the response envelope reflects the value propagated from `TOOL_TRACE_ID`. This requirement additionally governs child process environment inheritance and log entry formatting, which have no wire-format counterpart beyond `meta.trace_id`.

---

## Wire Format

Response showing `meta.trace_id` propagated from the `TOOL_TRACE_ID` environment variable:

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id":   "01HZ5PQRS",
    "trace_id":     "span-pipeline-42",
    "command":      "deploy",
    "timestamp":    "2024-06-01T12:00:00Z",
    "tool_version": "2.4.1"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework reads `TOOL_TRACE_ID` at startup and propagates it to all child processes and log entries automatically.

```
$ TOOL_TRACE_ID=span-pipeline-42 tool deploy --env prod
→ meta.trace_id: "span-pipeline-42"
→ stderr log: [TRACE span-pipeline-42] deploy: starting execution
→ child process inherits TOOL_TRACE_ID=span-pipeline-42

# Child process spawned by the framework
$ env | grep TOOL_TRACE_ID
TOOL_TRACE_ID=span-pipeline-42

# Audit log entry
{"timestamp":"...","command":"deploy","trace_id":"span-pipeline-42","request_id":"01HZ5PQRS",...}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: captures `TOOL_TRACE_ID` into `meta.trace_id`; this requirement extends propagation to children and logs |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Consumes: audit log entries include the trace ID propagated by this requirement |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Provides: child process tracking used to pass `TOOL_TRACE_ID` to spawned processes |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `trace_id` is a volatile field and belongs in `meta` |
