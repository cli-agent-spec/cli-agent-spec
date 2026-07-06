# REQ-C-015: Commands Declare Input and Output Schema

**Tier:** Command Contract | **Priority:** P1

**Source:** [§21 Schema & Help Discoverability](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Medium / Context: Medium

---

## Description

Every command MUST declare a complete input schema (all parameters: name, type, required, default, enum values if applicable, description) and output schema (JSON Schema for the `data` field of the response envelope). The framework MUST auto-generate `--schema` output from these declarations. Command authors MUST NOT write `--schema` output manually; it MUST be derived from the declaration.

## Acceptance Criteria

- `tool <cmd> --schema` returns valid JSON containing `parameters` and `output_schema`
- `tool --schema` returns a manifest of all commands with their parameter and output schemas
- Adding a parameter to a command automatically appears in `--schema` without separate documentation effort
- The `output_schema` is a valid JSON Schema object

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

The `--schema` output for a command is a `CommandEntry` (from `ManifestResponse.commands`) extended with an `output_schema` field:

| Field | Type | Description |
|-------|------|-------------|
| `parameters` | `Record<string, FlagEntry>` | Identical to `CommandEntry.flags` — one entry per declared argument |
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
    "timeout": { "type": "integer", "required": false, "default": 300,   "description": "Seconds before abort" }
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
