# REQ-F-018: Pagination Metadata on List Commands

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

The framework MUST automatically inject a `meta.pagination` object into the response envelope for every command declared as a list command. The `pagination` object MUST always contain: `total` (total count if known, or null), `returned` (count of items in this response), `truncated` (boolean), `has_more` (boolean), and `next_cursor` (opaque string token, or null if no more results). This metadata MUST be present even when the result is a complete set (with `truncated: false`).

## Acceptance Criteria

- Every list command response includes `meta.pagination`; the envelope's five top-level keys never change
- When results are truncated, `truncated: true` and `next_cursor` is non-null
- When results are complete, `truncated: false` and `next_cursor` is null
- Passing `next_cursor` from response N as `--cursor` in the next call returns the subsequent page

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The `Pagination` object is defined in `response-envelope.json` and injected as `meta.pagination`:

```json
{
  "pagination": {
    "total":       "<integer or null>",
    "returned":    "<integer>",
    "truncated":   "<boolean>",
    "has_more":    "<boolean>",
    "next_cursor": "<string or null>"
  }
}
```

---

## Wire Format

List command response with pagination metadata (partial result):

```json
{
  "ok": true,
  "data": [
    { "id": "user-1", "name": "Alice" },
    { "id": "user-2", "name": "Bob" }
  ],
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "pagination": {
      "total": 47,
      "returned": 2,
      "truncated": true,
      "has_more": true,
      "next_cursor": "eyJsYXN0X2lkIjoidXNlci0yMCJ9"
    },
    "request_id": "req_04EF",
    "command": "list-users",
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

Complete result (`truncated: false`):

```json
{
  "meta": {
    "pagination": {
      "total": 3,
      "returned": 3,
      "truncated": false,
      "has_more": false,
      "next_cursor": null
    }
  }
}
```

---

## Example

Framework-Automatic: no command author action needed beyond declaring the command as a list command. The framework injects the `pagination` object into every response.

```
$ tool list-users
→ pagination.total: 47, pagination.returned: 20, pagination.truncated: true

$ tool list-users --cursor eyJsYXN0X2lkIjoidXNlci0yMCJ9
→ pagination.total: 47, pagination.returned: 20, pagination.truncated: true

$ tool list-users --cursor eyJsYXN0X2lkIjoidXNlci00MCJ9
→ pagination.total: 47, pagination.returned: 7, pagination.truncated: false, pagination.next_cursor: null
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-019](f-019-default-output-limit.md) | F | Composes: default limit drives the `returned` and `truncated` values in this object |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that the `pagination` key extends |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `pagination` is framework-volatile; it MUST NOT be placed in `data` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: list command declaration that triggers automatic pagination injection |
