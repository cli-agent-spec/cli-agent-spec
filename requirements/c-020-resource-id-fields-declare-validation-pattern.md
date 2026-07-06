# REQ-C-020: Resource ID Fields Declare Validation Pattern

**Tier:** Command Contract | **Priority:** P1

**Source:** [§35 Agent Hallucination Input Patterns](../challenges/01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

Any command argument declared as a resource identifier (e.g., ID, slug, name, key) MUST include an explicit validation pattern in its schema: either a regex, an enum of allowed values, or a reference to a built-in pattern type (`alphanumeric_id`, `uuid`, `semver`, `filepath`, `url`). Arguments using a built-in pattern type automatically receive the hallucination pattern checks from REQ-F-045. Arguments using a custom regex MUST use anchored patterns (`^...$`). The framework MUST apply the declared pattern in Phase 1 validation before any execution.

## Acceptance Criteria

- A command argument declared as type `alphanumeric_id` automatically rejects inputs containing `/`, `.`, `?`, `#`, and `%`
- A command argument with a custom regex `^[a-z0-9-]{3,64}$` rejects inputs that do not match
- A command argument with no declared pattern for a resource ID field triggers a framework registration warning
- Pattern validation failures exit with code 2 and include the argument name and the expected pattern in the error

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

Resource ID arguments extend `FlagEntry` with validation fields:

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | Anchored regex (`^...$`) the value must match |
| `pattern_type` | `"alphanumeric_id"` \| `"uuid"` \| `"semver"` \| `"filepath"` \| `"url"` | Built-in pattern preset; mutually exclusive with `pattern` |

---

## Wire Format

```bash
$ tool deploy --schema
```
```json
{
  "parameters": {
    "cluster-id": {
      "type": "string",
      "required": true,
      "description": "Target cluster identifier",
      "pattern_type": "alphanumeric_id"
    },
    "version": {
      "type": "string",
      "required": true,
      "description": "Artifact version to deploy",
      "pattern_type": "semver"
    },
    "ticket-ref": {
      "type": "string",
      "required": false,
      "description": "Change ticket reference",
      "pattern": "^[A-Z]{2,8}-[0-9]{1,6}$"
    }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Deployment completed",                "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Resource ID failed pattern validation", "retryable": false, "side_effects": "none"     }
  }
}
```

---

## Example

```
register command "deploy":
  parameters:
    cluster-id:  type=string, required=true,  pattern_type=alphanumeric_id,
                 description="Target cluster identifier"
    version:     type=string, required=true,  pattern_type=semver,
                 description="Artifact version to deploy"
    ticket-ref:  type=string, required=false, pattern="^[A-Z]{2,8}-[0-9]{1,6}$",
                 description="Change ticket reference"

# tool deploy --cluster-id "prod/../evil" --version 1.2.3
#  → exit 2: cluster-id: value does not match alphanumeric_id pattern (no / or . allowed)

# tool deploy --cluster-id "prod-east-1" --version "not-semver"
#  → exit 2: version: value does not match semver pattern
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-045](f-045-agent-hallucination-input-pattern-rejection.md) | F | Enforces: built-in `pattern_type` values apply the hallucination rejection rules defined there |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `pattern` and `pattern_type` extend `FlagEntry` in `--schema` output |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: pattern validation runs in Phase 1 before any side effects |
| [REQ-C-019](c-019-subprocess-invoking-commands-declare-argument-sche.md) | C | Composes: `user_controlled_args` that are resource IDs also carry pattern declarations |
