# REQ-O-029: tool changelog Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§22 Schema Versioning & Output Stability](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST provide a built-in `tool changelog` command that outputs a structured history of schema changes. The output MUST include: version, release date, list of added fields, list of removed fields, list of changed field types, and whether each version is a breaking change. The command MUST accept `--since <version>` to filter. This enables callers to determine what changed since the version they were built against.

## Acceptance Criteria

- `tool changelog --format json` returns a valid JSON array of version entries
- Each entry includes `version`, `date`, `breaking` (boolean), `added`, `removed`, `changed`
- `--since 1.0.0` returns only entries for versions after `1.0.0`
- Breaking changes are correctly flagged as `"breaking": true`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.entries` is an array of version change objects with `version`, `date`, `breaking`, `added`, `removed`, and `changed` fields.

---

## Wire Format

```bash
$ tool changelog --since 1.0.0 --format json
```

```json
{
  "ok": true,
  "data": {
    "entries": [
      {
        "version": "2.0.0",
        "date": "2026-01-15",
        "breaking": true,
        "added": ["data.deployed_url"],
        "removed": ["data.url"],
        "changed": []
      },
      {
        "version": "1.1.0",
        "date": "2025-11-01",
        "breaking": false,
        "added": ["meta.duration_ms"],
        "removed": [],
        "changed": []
      }
    ]
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 2 }
}
```

---

## Example

Opt-in at the framework level; framework reads changelog from a registered changelog file or embedded metadata.

```
app = Framework("tool")
app.enable_changelog(source="./CHANGELOG.schema.json")

# Agent checks for breaking changes since its last known version:
$ tool changelog --since 1.0.0 --format json | jq '[.data.entries[] | select(.breaking)]'
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Provides: `meta.schema_version` in each response — changelog tracks changes to this |
| [REQ-F-023](f-023-tool-version-in-every-response.md) | F | Provides: `meta.tool_version` — changelog entries align with tool versions |
| [REQ-O-014](o-014-schema-version-compatibility-flag.md) | O | Composes: changelog reveals which schema versions have breaking changes |
