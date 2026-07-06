# REQ-C-001: Command Declares Exit Codes

**Tier:** Command Contract | **Priority:** P0

**Source:** [§1 Exit Codes & Status Signaling](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Low

---

## Description

Every command MUST declare a complete, exhaustive map of all exit codes it may emit, as part of its registration metadata. The framework MUST refuse to register a command that lacks this declaration. The exit code map MUST use the framework's named constants (REQ-F-001). The declared exit codes MUST be exposed in the command's `--schema` output.

## Acceptance Criteria

- Attempting to register a command without an `exit_codes` declaration raises a framework error
- Attempting to register a command whose `exit_codes` map does not include key `"0"` (`SUCCESS`) raises a framework error
- Attempting to register an entry with `retryable: true` and `side_effects` not equal to `"none"` raises a framework error
- The `--schema` output for every command includes an `exit_codes` object keyed by code string, each value conforming to `ExitCodeEntry`
- A command that emits an exit code not in its declared map triggers a framework warning in development mode

---

## Schema

**Types:** [`exit-code-entry.md`](../schemas/exit-code-entry.md) · [`exit-code.md`](../schemas/exit-code.md)

Requirement-specific constraints on top of the base `ExitCodeEntry` schema:

```json
{
  "exit_codes": {
    "type": "object",
    "minProperties": 1,
    "propertyNames": {
      "pattern": "^(0|[1-9][0-9]*)$",
      "description": "Keys are integer exit codes serialized as strings."
    },
    "additionalProperties": { "$ref": "ExitCodeEntry" },
    "required": ["0"],
    "description": "Must include an entry for ExitCode.SUCCESS (key '0')."
  }
}
```

---

## Wire Format

`tool <cmd> --schema` → `.exit_codes`:

```json
{
  "exit_codes": {
    "0":  { "name": "SUCCESS",   "description": "Deployment completed",       "retryable": false, "side_effects": "complete" },
    "2":  { "name": "ARG_ERROR", "description": "Invalid target environment", "retryable": false, "side_effects": "none"     },
    "5":  { "name": "NOT_FOUND", "description": "Target cluster not found",   "retryable": false, "side_effects": "none"     },
    "6":  { "name": "CONFLICT",  "description": "Version already deployed",   "retryable": false, "side_effects": "none"     },
    "10": { "name": "TIMEOUT",   "description": "Deployment timed out — partial writes may have occurred", "retryable": false, "side_effects": "partial"  }
  }
}
```

---

## Example

A command declares every exit code it may emit at registration time. The map key is the `ExitCode` named constant (serialized to its integer string in the wire format). Missing or incomplete declarations are hard errors.

```
register command "deploy":
  exit_codes:
    SUCCESS  (0): description: "Deployment completed",                              retryable: false, side_effects: complete
    ARG_ERROR(2): description: "Invalid target environment",                        retryable: false, side_effects: none
    NOT_FOUND(5): description: "Target cluster not found",                          retryable: false, side_effects: none
    CONFLICT (6): description: "Version already deployed",                          retryable: false, side_effects: none
    TIMEOUT (10): description: "Deployment timed out — partial writes may have occurred", retryable: false, side_effects: partial

register command "no-success":
  exit_codes:
    ARG_ERROR(2): description: "Bad argument", retryable: false, side_effects: none
  → framework error: exit_codes must include SUCCESS (key "0")

register command "bad-invariant":
  exit_codes:
    SUCCESS (0): description: "Done",           retryable: false, side_effects: complete
    TIMEOUT(10): description: "Timed out",      retryable: true,  side_effects: partial
  → framework error: retryable: true requires side_effects: "none"

register command "broken":
  (no exit_codes)
  → framework error: exit_codes declaration is required
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ExitCode` named constants used as map keys and `name` values |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: `ARG_ERROR` guarantees `side_effects: none` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `exit_codes` is part of the `--schema` output |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: error responses reference the codes declared here |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest collects exit code declarations from all commands |
