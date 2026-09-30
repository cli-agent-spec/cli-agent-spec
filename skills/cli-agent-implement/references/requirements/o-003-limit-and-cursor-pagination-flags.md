# REQ-O-003: --limit and --cursor Pagination Flags

**Tier:** Opt-In | **Priority:** P0

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

The framework MUST register `--limit <n>` and `--cursor <token>` as standard flags on all list commands. `--limit` controls maximum items returned. `--cursor` accepts an opaque pagination token from the previous response's `meta.pagination.next_cursor`. The cursor MUST be stateless (self-contained, not dependent on server-side session).

**Invalid cursor.** The framework MUST reject a `--cursor` value it cannot honor with exit `2` (`ARG_ERROR`), error code `INVALID_CURSOR`, `retryable: false`, and a `fix_required` telling the caller to rerun without `--cursor` to start from the first page. This covers a token that fails to decode, fails the framework's integrity check when it has one, or has expired. The rule is the same for every list command, so an agent recovers from any of them the same way. Because exit `2` is raised before any work begins, the rejected call has no side effects.

**Cursor bound to its query.** A token binds the query that produced it: the command's filters and its sort order. Reusing it with a different query (another filter value, an added or removed filter, or a different sort) fails as `INVALID_CURSOR`, never with a page drawn from a different result set. `--limit` is not part of the query: the caller MAY change it between pages, and the next page holds up to the new limit.

## Acceptance Criteria

- `--limit 50` returns at most 50 items
- Passing `meta.pagination.next_cursor` from response N as `--cursor` returns the next page
- A malformed `--cursor` value (for example `--cursor not-a-token`) exits `2` with error code `INVALID_CURSOR`, `retryable: false`, and a `fix_required` that says to rerun without `--cursor`; it never crashes
- An expired token exits `2` with error code `INVALID_CURSOR`
- A `next_cursor` from `tool list-deployments --status failed` passed to `tool list-deployments --status complete --cursor <token>` exits `2` with error code `INVALID_CURSOR`; the same applies when a filter is added or removed, or the sort order changes
- A `next_cursor` from a `--limit 2` call passed with `--limit 10` and the same filters returns the next page of up to 10 items
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

Rejecting a malformed, expired, or mismatched cursor:

```bash
$ tool list-deployments --limit 2 --cursor eyJwYWdlIjoyfQX --format json
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_CURSOR",
    "message": "The --cursor token is malformed, expired, or was issued for a different query",
    "retryable": false,
    "fix_required": "Rerun without --cursor to start from the first page"
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 4 }
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
# tool list-deployments --status failed --cursor <token from an unfiltered call>  →  exit 2, INVALID_CURSOR
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | F | Provides: pagination metadata shape used in `meta` |
| [REQ-F-019](f-019-default-output-limit.md) | F | Provides: default limit applied when `--limit` is absent |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Composes: `--stream` emits pagination metadata as the final JSONL line |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` carrying `meta.cursor` |
