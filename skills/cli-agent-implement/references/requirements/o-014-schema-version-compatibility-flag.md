# REQ-O-014: --schema-version Compatibility Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§22 Schema Versioning & Output Stability](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

Commands that have undergone breaking schema changes SHOULD support `--schema-version <major>` to request output in a prior major version format. The framework provides the flag; commands implement compatibility shims for supported historical versions. Commands MUST declare the minimum supported `--schema-version` in their registration. Callers using a pinned schema version receive a deprecation warning in `meta.warnings` when using a version below the current.

## Acceptance Criteria

- `--schema-version 1` on a v2 command produces output conforming to the v1 schema
- A `SCHEMA_DEPRECATED` warning appears in `warnings[]` when using an old schema version
- Requesting a schema version below the minimum supported raises a structured error
- The current and minimum supported schema versions are included in `--schema` output

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Pinned-version responses include `meta.schema_version` matching the requested version, and a deprecation warning in `warnings[]` when using a version below the current.

---

## Wire Format

```bash
$ tool deploy --target staging --schema-version 1 --format json
```

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [
    { "code": "SCHEMA_DEPRECATED", "message": "Schema version 1.0 is deprecated; current is 2.0", "context": { "current_version": "2.0", "requested_version": "1.0" } }
  ],
  "meta": { "exit_code": 0, "schema_version": "1.0", "duration_ms": 832 }
}
```

---

## Example

Opt-in per command by declaring `min_schema_version` and implementing compatibility shims.

```
register command "deploy":
  min_schema_version: 1   # supports back to v1
  schema_version: 2       # current
  compat:
    v1: v1_compat_shim    # function to transform v2 output to v1 shape

# Agent pins schema version to avoid breaking changes:
$ tool deploy --target staging --schema-version 1
→ meta.schema_version: "1.0"
→ warnings: [SCHEMA_DEPRECATED]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Provides: `meta.schema_version` field this flag overrides |
| [REQ-O-013](o-013-schema-output-schema-flag.md) | O | Exposes: min and current schema versions are visible in `--schema` output |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Consumes: schema declarations provide the version metadata |
