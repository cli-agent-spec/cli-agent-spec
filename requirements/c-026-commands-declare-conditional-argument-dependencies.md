# REQ-C-026: Commands Declare Conditional Argument Dependencies

**Tier:** Command Contract | **Priority:** P1

**Source:** [§54 Conditional / Dependent Argument Requirements](../challenges/01-critical-ecosystem-runtime-agent-specific/54-high-conditional-args.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: Low

---

## Description

Commands MUST declare all conditional argument requirements in their registration metadata using a `requires` clause, rather than discovering them at runtime. The `requires` clause specifies: when flag A has value V, flag B is required; when flag A is present, flag B is prohibited (mutual exclusion); when flag A is absent, flag B has a different default. The framework validates all declared `requires` relationships during the validate-before-execute phase (Phase 1), before any side effects. The `--schema` output MUST include the full `requires` graph so agents can construct valid calls without trial-and-error discovery.

## Acceptance Criteria

- A command with `requires: [{if: "--format=csv", then: "--separator"}]` exits 2 with a structured error when `--format csv` is passed without `--separator`
- The `--schema` output includes the full conditional dependency graph
- Mutually exclusive flags are enforced in Phase 1: passing both produces exit 2 before any I/O
- An agent calling `--schema` can determine all required flags for a given combination of values without making a failing call first

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

`CommandEntry` is extended with a `requires` array:

| Field | Type | Description |
|-------|------|-------------|
| `requires` | `ConditionalRule[]` | Ordered list of conditional argument dependency rules |

Each `ConditionalRule` has one of the following shapes:

| Shape | Fields | Meaning |
|-------|--------|---------|
| `if_value` | `if_flag`, `if_value`, `then_required` | When `if_flag` equals `if_value`, flags in `then_required` become required |
| `if_present` | `if_flag`, `prohibited` | When `if_flag` is present, flags in `prohibited` are forbidden |
| `default_when_absent` | `if_flag`, `target_flag`, `default` | When `if_flag` is absent, `target_flag` uses this `default` instead of its declared default |

---

## Wire Format

```bash
$ tool export --schema
```
```json
{
  "parameters": {
    "format":    { "type": "enum",    "required": true,  "enum_values": ["csv", "json", "parquet"], "description": "Output format" },
    "separator": { "type": "string",  "required": false, "description": "Field separator for CSV output" },
    "compress":  { "type": "boolean", "required": false, "default": false, "description": "Compress output" },
    "output":    { "type": "string",  "required": false, "description": "Output file path" },
    "stdout":    { "type": "boolean", "required": false, "default": false, "description": "Write to stdout instead of file" }
  },
  "requires": [
    { "if_flag": "format", "if_value": "csv", "then_required": ["separator"] },
    { "if_flag": "output", "prohibited": ["stdout"] }
  ],
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Export completed",                 "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Conditional argument rule violated", "retryable": false, "side_effects": "none"     }
  }
}
```

---

## Example

```
register command "export":
  parameters:
    format:    type=enum(csv, json, parquet), required=true
    separator: type=string, required=false
    compress:  type=boolean, required=false, default=false
    output:    type=string,  required=false
    stdout:    type=boolean, required=false, default=false
  requires:
    - if format == "csv" → separator is required
    - if output present  → stdout is prohibited (mutually exclusive)

# tool export --format csv
#  → exit 2: ARG_ERROR: --format csv requires --separator

# tool export --format json --output report.json --stdout
#  → exit 2: ARG_ERROR: --output and --stdout are mutually exclusive
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `requires` graph is part of the `--schema` output that agents read |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: `requires` rules are evaluated in Phase 1 before any side effects |
| [REQ-C-006](c-006-all-args-validated-in-phase-1.md) | C | Specializes: conditional dependency validation is one category of Phase 1 argument validation |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: `requires` violations exit with code 2 (`ARG_ERROR`) |
