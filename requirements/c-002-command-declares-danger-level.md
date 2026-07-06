# REQ-C-002: Command Declares Danger Level

**Tier:** Command Contract | **Priority:** P0

**Source:** [§23 Side Effects & Destructive Operations](../challenges/03-critical-security/23-critical-destructive-ops.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: High / Context: Medium

---

## Description

Every command MUST declare a `danger_level` as part of its registration metadata, chosen from: `safe` (read-only, no side effects), `mutating` (creates or modifies state), or `destructive` (permanently deletes or irreversibly modifies state). The framework MUST refuse to register a command without this declaration. The framework MUST use this declaration to enforce related behaviors (e.g., requiring `--dry-run` for destructive commands per REQ-C-004).

## Acceptance Criteria

- Attempting to register a command without `danger_level` raises a framework error
- The `--schema` output for every command includes `danger_level`
- Commands with `danger_level: "destructive"` trigger framework-level dry-run enforcement (REQ-C-004)
- Commands with `danger_level: "safe"` do not require `--idempotency-key` (REQ-C-007)

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

The `danger_level` field appears on every command entry in `--schema` output and in the manifest. Allowed values: `"safe"` · `"mutating"` · `"destructive"`.

```json
{
  "danger_level": {
    "type": "string",
    "enum": ["safe", "mutating", "destructive"],
    "description": "Indicates the mutation risk level of the command"
  }
}
```

---

## Wire Format

```bash
$ tool delete-account --schema
```

```json
{
  "command": "delete-account",
  "danger_level": "destructive",
  "reversible": false,
  "requires_confirmation": true,
  "flags": {
    "user": { "type": "integer", "required": true, "description": "User ID to delete" },
    "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Validate without deleting" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "User account deleted",    "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Invalid user ID",         "retryable": false, "side_effects": "none"     },
    "5": { "name": "NOT_FOUND", "description": "User not found",          "retryable": false, "side_effects": "none"     }
  }
}
```

---

## Example

A command declares its danger level at registration time. The framework uses this declaration to enforce related behaviors automatically.

```
register command "delete-account":
  danger_level: destructive
  exit_codes:
    SUCCESS (0): description: "User account deleted", retryable: false, side_effects: complete
    NOT_FOUND(5): description: "User not found",      retryable: false, side_effects: none

register command "list-users":
  danger_level: safe
  exit_codes:
    SUCCESS(0): description: "User list returned", retryable: false, side_effects: none

register command "update-email":
  (no danger_level)
  → framework error: danger_level declaration is required
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `danger_level` is part of the same `--schema` output as `exit_codes` |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Extends: `danger_level: mutating/destructive` triggers `effect` field requirement |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Enforces: `danger_level: destructive` requires `--dry-run` support |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Enforces: `danger_level: mutating/destructive` requires `--idempotency-key` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest exposes `danger_level` for every registered command |
