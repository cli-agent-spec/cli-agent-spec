# REQ-O-013: --schema / --output-schema Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§21 Schema & Help Discoverability](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Medium / Context: Medium

---

## Description

The framework MUST provide `tool --schema` (full manifest of all commands) and `tool <cmd> --output-schema` (JSON Schema for the `data` field of a specific command's response). `tool --print-schema` MUST be accepted as a compatibility alias for `tool --schema`, while `--schema` remains the canonical spelling used in documentation and examples. All schema-discovery outputs MUST produce valid, machine-parseable JSON. The schemas MUST be generated automatically from command registration metadata (REQ-C-015). The full manifest MUST include: command name, description, danger level, parameters, output schema, exit codes, and stability tier per field.

## Acceptance Criteria

- `tool --schema | python -c "import json,sys; json.load(sys.stdin)"` succeeds
- `tool --print-schema | python -c "import json,sys; json.load(sys.stdin)"` succeeds and returns the same payload as `tool --schema`
- The schema includes `parameters`, `output_schema`, `exit_codes`, and `danger_level` for each command
- `tool <cmd> --output-schema` is a valid JSON Schema that the command's `data` field conforms to
- The schema output is stable (does not change between invocations absent registration changes)

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

`tool --schema` returns a full `ManifestResponse`. `tool --print-schema` is a compatibility alias for the same response. `tool <cmd> --output-schema` returns only the JSON Schema for that command's `data` field, wrapped in a `ResponseEnvelope`.

---

## Wire Format

```bash
$ tool deploy --output-schema
```

```json
{
  "ok": true,
  "data": {
    "type": "object",
    "properties": {
      "deployed": { "type": "boolean", "description": "Whether deployment succeeded" },
      "url": { "type": "string", "description": "Deployed endpoint URL" }
    },
    "required": ["deployed"]
  },
  "error": null,
  "warnings": [],
  "meta": { "schema_version": "1.0" }
}
```

---

## Example

Opt-in at the framework level; auto-generated from command registration metadata.

```
app = Framework("tool")
app.enable_schema_flag()   # registers --schema, --print-schema, and --output-schema globally

# Full manifest of all commands:
$ tool --schema | jq '.data.commands | keys'

# JSON Schema for a single command's output:
$ tool deploy --output-schema | jq '.data'
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: the schema declarations this flag surfaces |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Extends: `tool manifest` is the structured equivalent of `tool --schema` |
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Composes: `meta.schema_version` appears in the schema output response |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Provides: `exit_codes` map exposed in `--schema` output |
