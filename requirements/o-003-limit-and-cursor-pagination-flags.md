# REQ-O-003: --limit and --cursor Pagination Flags

**Tier:** Opt-In | **Priority:** P0

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

The framework MUST register `--limit <n>` and `--cursor <token>` as standard flags on all list commands. `--limit` controls maximum items returned. `--cursor` accepts an opaque pagination token from the previous response's `meta.pagination.next_cursor`. The cursor MUST be stateless (self-contained, not dependent on server-side session). The framework MUST reject `--cursor` values that are expired or invalid with a structured error.

## Acceptance Criteria

- `--limit 50` returns at most 50 items
- Passing `meta.pagination.next_cursor` from response N as `--cursor` returns the next page
- An invalid `--cursor` value returns a structured error, not a crash
- Cursor tokens are URL-safe strings (base64url or similar encoding)

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

Pagination metadata appears in `meta.pagination` (REQ-F-018): `next_cursor` holds the next-page token, `total` holds the total item count when known, and `returned` reflects the items in this page.

---

## Wire Format

First page:

```bash
$ tool list-deployments --limit 2 --format json
```

```json
{
  "ok": true,
  "data": [
    { "id": "d1", "status": "complete" },
    { "id": "d2", "status": "running" }
  ],
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 55, "pagination": { "total": 47, "returned": 2, "truncated": true, "has_more": true, "next_cursor": "eyJwYWdlIjoyfQ" } }
}
```

Next page:

```bash
$ tool list-deployments --limit 2 --cursor eyJwYWdlIjoyfQ --format json
```

```json
{
  "ok": true,
  "data": [
    { "id": "d3", "status": "failed" },
    { "id": "d4", "status": "complete" }
  ],
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 48, "pagination": { "total": 47, "returned": 2, "truncated": true, "has_more": true, "next_cursor": "eyJwYWdlIjozfQ" } }
}
```

---

## Example

The framework registers `--limit` and `--cursor` on list commands at opt-in time.

```
app = Framework("tool")
app.enable_pagination_flags(default_limit=20, max_limit=100)

# tool list-deployments --limit 10  →  first 10 items + meta.pagination.next_cursor
# tool list-deployments --limit 10 --cursor <token>  →  next 10 items
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | F | Provides: pagination metadata shape used in `meta` |
| [REQ-F-019](f-019-default-output-limit.md) | F | Provides: default limit applied when `--limit` is absent |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Composes: `--stream` emits pagination metadata as the final JSONL line |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` carrying `meta.cursor` |
