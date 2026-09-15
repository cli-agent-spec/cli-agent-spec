# REQ-F-052: Response Size Hard Cap with Truncation Indicator

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§43 Tool Output Result Size Unboundedness](../challenges/01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md)

**Addresses:** Severity: Critical / Token Spend: Critical / Time: High / Context: Critical

---

## Description

The framework MUST enforce a maximum output size for all command responses. The default cap MUST be 1 MB (1,048,576 bytes) for JSON output and configurable via `TOOL_MAX_OUTPUT_BYTES` environment variable. When a response exceeds the cap, the framework MUST truncate the `data` array or string value, set `meta.truncated = true`, populate `meta.total_count` (total available items), `meta.returned_count` (items actually returned), and include a `meta.truncation_hint` field with the exact flag to pass (e.g., `--limit N --cursor <token>`) to retrieve the remaining data. The framework MUST NOT silently omit data without these indicators.

## Acceptance Criteria

- A command that returns 10,000 items is automatically truncated at the cap with `meta.truncated: true`
- `meta.truncation_hint` contains a valid command invocation to retrieve the next page
- A response under the cap does not include `meta.truncated` or includes it as `false`
- Setting `TOOL_MAX_OUTPUT_BYTES=5242880` raises the cap to 5 MB for all commands

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When a response is truncated, `meta.truncated` is set to `true`, `meta.total_count` reports the full result set size, `meta.returned_count` reports items actually returned, and `meta.truncation_hint` provides the exact command to retrieve the next page.

---

## Wire Format

`tool list` → truncated response with `meta` indicators:

```json
{
  "ok": true,
  "data": [
    { "id": "item-001", "name": "First item" },
    { "id": "item-002", "name": "Second item" }
  ],
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "truncated": true,
    "total_count": 10000,
    "returned_count": 2,
    "truncation_hint": "tool list --limit 100 --cursor eyJpZCI6Iml0ZW0tMDAyIn0="
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework enforces the cap and injects truncation metadata before serialization.

```
# Default cap: 1 MB
$ tool records list
→ returns first N records that fit within 1 MB
→ meta.truncated: true, meta.total_count: 10000, meta.returned_count: 47

# Raise cap via environment variable
$ TOOL_MAX_OUTPUT_BYTES=5242880 tool records list
→ returns more records, up to 5 MB

# Response under cap — no truncation metadata
$ tool records get --id item-001
→ meta.truncated: false   (or meta field absent)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-019](f-019-default-output-limit.md) | F | Specializes: default output limit is the primary mechanism; this requirement adds a byte-level hard cap |
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | F | Composes: `meta.truncation_hint` references pagination cursor fields defined by this requirement |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: truncation indicators appear in `meta`, not `data` |
| [REQ-F-053](f-053-stdout-unbuffering-in-non-tty-mode.md) | F | Composes: unbuffered stdout ensures truncated responses are flushed atomically |
