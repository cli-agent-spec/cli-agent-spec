# REQ-F-005: Locale-Invariant Serialization

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework's JSON serializer MUST always use invariant formatting: period (`.`) as decimal separator, no thousands separator, ISO 8601 format for all dates and datetimes (e.g., `2024-03-11T14:30:00Z`), JSON `true`/`false` for booleans (never `yes`/`no`/`1`/`0`). The serializer MUST NOT be influenced by the `LC_*` or `LANG` environment variables.

## Acceptance Criteria

- Output produced on a `de_DE` locale system is byte-for-byte identical to output on an `en_US` system for the same inputs
- All date fields in output match the regex `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}`
- Numeric fields in output contain no comma thousands separators
- Boolean fields in output are exactly `true` or `false`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

No dedicated schema type — this requirement governs serialization behavior without adding new wire-format fields. All numeric and date values within any `ResponseEnvelope` field are subject to these formatting rules.

---

## Wire Format

JSON with invariant number and date formatting — identical output regardless of host locale:

```json
{
  "ok": true,
  "data": {
    "price": 1234.56,
    "count": 1000000,
    "ratio": 0.075,
    "created_at": "2024-03-11T14:30:00Z",
    "updated_at": "2024-11-01T09:00:00Z",
    "active": true
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 22 }
}
```

Note: `1234.56` not `1.234,56`; `1000000` not `1,000,000`; dates in ISO 8601; booleans as `true`/`false` not `yes`/`1`.

---

## Example

Framework-Automatic: no command author action needed. The framework's serializer is pinned to invariant formatting and ignores `LC_*` and `LANG` at the point of JSON encoding.

```
# Host locale: de_DE (comma decimal, dot thousands)
$ LC_ALL=de_DE tool report --output json
{"ok":true,"data":{"price":1234.56,"count":1000000},...}
# NOT {"price":"1.234,56","count":"1.000.000"}

# Host locale: en_US
$ LC_ALL=en_US tool report --output json
{"ok":true,"data":{"price":1234.56,"count":1000000},...}
# Output is byte-for-byte identical
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: all `ResponseEnvelope` fields are subject to invariant serialization |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: locale-invariant output is produced whenever JSON mode is active |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: error messages may contain numbers and dates that must also be invariant |
