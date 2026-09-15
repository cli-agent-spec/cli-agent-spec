# REQ-F-064: Output Truncation Detection and Warning

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§55 Silent Data Truncation](../challenges/01-critical-ecosystem-runtime-agent-specific/55-high-silent-truncation.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST detect and report data truncation rather than silently returning a truncated value. When a field value is truncated (by a backend API, database column limit, or framework response size cap from REQ-F-052), the framework MUST: set `meta.truncated: true` in the response, include a `TRUNCATION` entry in `warnings[]` with the field path and byte counts (`original_bytes` if known, `returned_bytes`), and ensure the truncated value is clearly terminated (e.g., appended with a truncation marker). Commands that write to size-limited fields MUST declare `max_bytes: N` per field in their schema; the framework validates write payloads against these limits before submission and exits 2 if exceeded.

## Acceptance Criteria

- Writing a 500-byte value to a field declared `max_bytes: 255` exits 2 with a structured error before writing
- Reading a pre-truncated value from a backend produces `meta.truncated: true` and a `FIELD_TRUNCATED` warning
- The warning `context` includes `field`, `truncated_length`, and (where known) `original_length`
- `json.loads(stdout)` succeeds even when truncation is present — the response envelope is always complete

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

Truncation is signaled via `meta.truncated: true` and a `FIELD_TRUNCATED` entry in `warnings[]` carrying the field path and byte counts.

---

## Wire Format

```json
{
  "ok": true,
  "data": {
    "description": "This is a very long description that has been cut off..."
  },
  "error": null,
  "warnings": [
    {
      "code": "FIELD_TRUNCATED",
      "message": "Field value was truncated by the backend",
      "context": { "field": "data.description", "original_length": 8192, "truncated_length": 255 }
    }
  ],
  "meta": {
    "exit_code": 0,
    "duration_ms": 34,
    "truncated": true
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework detects truncation from backends and from its own response size cap, then annotates the response.

```
# Backend returns a pre-truncated field
$ mytool issue get 42 --json
{
  "ok": true,
  "data": { "body": "First 255 chars of the issue body..." },
  "error": null,
  "warnings": [{ "code": "FIELD_TRUNCATED", "message": "Field value was truncated by the backend", "context": { "field": "data.body", "original_length": 4200, "truncated_length": 255 } }],
  "meta": { "exit_code": 0, "duration_ms": 34, "truncated": true }
}
→ agent knows data.body is incomplete; can paginate or fetch full field

# Write payload exceeds declared max_bytes: 255
$ mytool issue update 42 --body "$(python3 -c 'print("x"*500)')" --json
{ "ok": false, "data": null, "error": { "code": "FIELD_TOO_LARGE", "phase": "validation" }, ... }
→ exits 2 before writing
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` `warnings` array and `meta.truncated` field |
| [REQ-F-052](f-052-response-size-hard-cap-with-truncation-indicator.md) | F | Composes: response size cap is the primary source of framework-side truncation |
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | F | Composes: truncated list results should use pagination rather than field truncation |
| [REQ-F-019](f-019-default-output-limit.md) | F | Composes: default output limits interact with field-level truncation detection |
