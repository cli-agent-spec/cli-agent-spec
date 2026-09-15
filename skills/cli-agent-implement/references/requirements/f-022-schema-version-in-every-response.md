# REQ-F-022: Schema Version in Every Response

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§22 Schema Versioning & Output Stability](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST automatically inject `meta.schema_version` (a `MAJOR.MINOR` string) into every response. The schema version MUST correspond to the version of the response contract for that command, not the overall tool version. Callers MUST be able to detect schema changes by comparing `meta.schema_version` values across responses.

## Acceptance Criteria

- Every response JSON object includes `meta.schema_version` as a `MAJOR.MINOR` string
- When a command's output schema changes in a breaking way, `meta.schema_version` increments the major component; additive changes increment the minor component
- `meta.schema_version` is stable across invocations of the same command version

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.schema_version` is a `MAJOR.MINOR` string injected by the framework into every response's `meta` object.

---

## Wire Format

Response `meta` with `schema_version`:

```json
{
  "ok": true,
  "data": { "id": "user-1", "name": "Alice" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id":     "req_07KL",
    "command":        "get-user",
    "timestamp":      "2024-06-01T12:00:00Z",
    "schema_version": "1.3",
    "tool_version":   "2.4.1"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework reads the schema version declared at command registration and injects it into every response.

```
# Command registered with schema_version "1.3"
$ tool get-user --id 1
→ meta.schema_version: "1.3.0"

# After a breaking schema change — command re-registered with "2.0.0"
$ tool get-user --id 1
→ meta.schema_version: "2.0.0"

# Agent detects the major version bump and re-fetches --schema before proceeding
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `schema_version` is a volatile field and belongs in `meta`, not `data` |
| [REQ-F-023](f-023-tool-version-in-every-response.md) | F | Composes: `tool_version` accompanies `schema_version` in every response `meta` |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope whose `meta` carries `schema_version` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: output schema declaration from which `schema_version` is derived |
