# REQ-C-015: Commands Declare Input and Output Schema

**Tier:** Command Contract | **Priority:** P1

**Source:** [§21 Schema & Help Discoverability](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Medium / Context: Medium

---

## Description

Every command MUST declare a complete input schema (all parameters: name, type, required, default, enum values if applicable, description) and output schema (JSON Schema for the `data` field of the response envelope). The framework MUST auto-generate `--schema` output from these declarations. Command authors MUST NOT write `--schema` output manually; it MUST be derived from the declaration. A passthrough command ([REQ-C-031](c-031-passthrough-commands-delegate-to-another-parser.md)) is exempt from the input schema: its arguments belong to the delegated tool, so it declares no flags or positionals, and `--schema` shows `arguments: "passthrough"` instead.

**Structured flag values.** A flag whose value is a JSON object SHOULD declare `type: "object"` and the value's JSON Schema in `FlagEntry.schema` rather than `type: "string"` with the shape described in prose, because an agent cannot see the shape it must build otherwise. A flag declared `type: "object"` MUST carry `schema`. The caller passes the value as one argv token of JSON text, as `--raw-payload` takes its payload ([REQ-O-032](o-032-raw-payload-flag-for-mutating-commands.md)): `--filter '{"status":"open"}'`. An `array` flag whose items are objects puts the item schema in `schema`, and each item it receives is one such token. For a flag declared `type: "object"` (or an `array` flag with `schema`), the framework MUST parse and validate the value against `schema` during Phase 1 ([REQ-F-015](f-015-validate-before-execute-phase-order.md)) and exit `2` (`ARG_ERROR`) when the text is not valid JSON or does not match, before any side effect. `schema` appears only on `object` and `array` flags.

## Acceptance Criteria

- `tool <cmd> --schema` returns valid JSON containing `parameters` and `output_schema`
- `tool --schema` returns a manifest of all commands with their parameter and output schemas
- Adding a parameter to a command automatically appears in `--schema` without separate documentation effort
- Positional arguments appear in the command's `positionals` array in call order, never only in its `description`
- The `output_schema` is a valid JSON Schema object
- A flag declared `type: "object"` carries a `schema`; `--filter '{"status":"open"}'` passes when the text matches that schema
- On a flag declared `type: "object"`, `--filter 'status=open'` (not JSON) and `--filter '{"status":3}'` (does not match `schema`) both exit `2` with an `ARG_ERROR` naming the flag, before any side effect

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

The `--schema` output for a command is a `CommandEntry` (from `ManifestResponse.commands`) extended with an `output_schema` field:

| Field | Type | Description |
|-------|------|-------------|
| `parameters` | `Record<string, FlagEntry>` | Identical to `CommandEntry.flags` — one entry per declared option |
| `positionals` | `PositionalEntry[]` | Identical to `CommandEntry.positionals` — positional arguments in call order |
| `output_schema` | JSON Schema object | Describes the shape of `ResponseEnvelope.data` on success |

---

## Wire Format

```bash
$ tool deploy --schema
```
```json
{
  "parameters": {
    "target":  { "type": "enum",    "required": true,  "enum_values": ["prod", "staging", "dev"], "description": "Target environment" },
    "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Validate without executing" },
    "timeout": { "type": "integer", "required": false, "default": 300,   "description": "Seconds before abort" },
    "labels":  { "type": "object",  "required": false, "description": "Labels to attach as JSON text",
                 "schema": { "type": "object", "additionalProperties": { "type": "string" } } }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "deployment_id": { "type": "string" },
      "status":        { "type": "string", "enum": ["pending", "running", "complete", "failed"] },
      "started_at":    { "type": "string", "format": "date-time" }
    },
    "required": ["deployment_id", "status"]
  },
  "exit_codes": {
    "0":  { "name": "SUCCESS",   "description": "Deployment completed",       "retryable": false, "side_effects": "complete" },
    "2":  { "name": "ARG_ERROR", "description": "Invalid target environment", "retryable": false, "side_effects": "none"     },
    "10": { "name": "TIMEOUT",   "description": "Deployment timed out",       "retryable": false, "side_effects": "partial"  }
  }
}
```

---

## Example

Command authors declare input parameters and output shape at registration time. The framework derives `--schema` from these declarations automatically:

```
register command "deploy":
  parameters:
    target:  type=enum(prod, staging, dev), required=true,  description="Target environment"
    dry-run: type=boolean, required=false, default=false,   description="Validate without executing"
    timeout: type=integer, required=false, default=300,     description="Seconds before abort"
    labels:  type=object,  required=false, schema={type: object, additionalProperties: {type: string}},
             description="Labels to attach as JSON text"
  output_schema:
    type: object
    required: [deployment_id, status]
    properties:
      deployment_id: { type: string }
      status:        { type: string, enum: [pending, running, complete, failed] }
      started_at:    { type: string, format: date-time }

# tool deploy --schema  →  derived automatically; no manual schema writing
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `exit_codes` appears alongside `parameters` and `output_schema` in `--schema` output |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest collects `parameters` and `output_schema` declarations from all commands |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: declared `parameters` drive Phase 1 validation before execution |
| [REQ-C-026](c-026-commands-declare-conditional-argument-dependencies.md) | C | Extends: conditional `requires` graph is part of the `--schema` output |
| [REQ-O-032](o-032-raw-payload-flag-for-mutating-commands.md) | O | Composes: an `object` flag takes JSON text on argv the same way `--raw-payload` does |
| [REQ-C-031](c-031-passthrough-commands-delegate-to-another-parser.md) | C | Specializes: a passthrough command declares no input schema |
