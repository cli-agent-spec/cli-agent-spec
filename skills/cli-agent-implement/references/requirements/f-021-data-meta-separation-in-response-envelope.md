# REQ-F-021: Data/Meta Separation in Response Envelope

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§7 Output Non-Determinism](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST place all volatile fields (timestamps, durations, request IDs, tool version, config hash) into the `meta` object of the response envelope, and MUST keep the `data` object free of volatile fields. The framework MUST document that `data` is safe for caching and change-detection, and that `meta` is not. Commands MUST NOT place timestamps or random values directly in `data`; the framework MUST enforce this via the schema declaration mechanism.

## Acceptance Criteria

- Two responses for the same operation with the same arguments have byte-identical `data` objects (absent business-state changes)
- All `meta` fields are volatile by definition and are excluded from diff-based change detection
- A command that attempts to put a timestamp directly in `data` triggers a framework validation warning at registration time

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The envelope's structural guarantee: `data` contains only stable, deterministic fields; `meta` contains all volatile framework-injected fields.

---

## Wire Format

Response showing stable `data` alongside volatile `meta`:

```json
{
  "ok": true,
  "data": {
    "id":     "user-42",
    "name":   "Alice",
    "role":   "admin",
    "active": true
  },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "request_id":     "req_06IJ",
    "trace_id":       "trace-abc",
    "command":        "get-user",
    "timestamp":      "2024-06-01T12:00:05Z",
    "duration_ms":    18,
    "tool_version":   "2.4.1",
    "schema_version": "1.0"
  }
}
```

Two calls with identical arguments and identical business state produce byte-identical `data` objects regardless of differing `meta.timestamp`, `meta.request_id`, or `meta.duration_ms` values.

---

## Example

Framework-Automatic: no command author action needed. The framework routes all timestamp, duration, version, and ID fields into `meta` automatically. Commands that declare volatile fields in `data` receive a registration-time warning.

```
register command "get-user":
  output_schema:
    data:
      id:         string
      name:       string
      fetched_at: timestamp   ← framework warning: volatile field in data
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-020](f-020-stable-array-sorting-in-json-output.md) | F | Composes: stable array sorting is only meaningful because volatile fields are excluded from `data` |
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Provides: `meta.schema_version` is one of the volatile fields kept in `meta` |
| [REQ-F-023](f-023-tool-version-in-every-response.md) | F | Provides: `meta.tool_version` is a volatile field kept in `meta` |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `meta.request_id` and `meta.trace_id` are volatile fields kept in `meta` |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: base envelope structure this requirement specializes |
