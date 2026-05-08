# REQ-C-029: Command Declares Required Scopes

**Tier:** Command Contract | **Priority:** P0

**Source:** [§74 Credential Scope Declaration Absence](../challenges/03-critical-security/74-critical-credential-scope-declaration.md)

**Addresses:** Severity: Critical / Token Spend: Low / Time: Medium / Context: Low

---

## Description

Every command that authenticates with an external service MUST declare a `required_scopes` field as part of its registration metadata — an ordered list of minimal permission strings needed to execute the command successfully. The framework MUST refuse to register an auth-requiring command without this declaration. Commands that require no external authentication MUST declare `required_scopes: []` explicitly. Over-declaration (listing scopes not actually needed) is a spec violation; the list MUST be the minimum necessary.

`required_scopes` values are service-specific strings (e.g., `"repo:read"` for GitHub, `"s3:GetObject"` for AWS, `"storage.objects.get"` for GCP). The framework does not validate their format — it enforces only that the field is present and non-null.

## Acceptance Criteria

- Attempting to register an auth-requiring command without `required_scopes` raises a framework error
- `required_scopes` is present in the `--schema` output for every registered command
- Commands requiring no external auth declare `required_scopes: []`
- `required_scopes` lists only permissions actually invoked; blanket admin or owner scopes are not permitted unless provably required and documented in the command's description

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

`required_scopes` is added as a required field on `CommandEntry`. The field is an ordered array of strings — order implies priority: earlier entries are the most critical.

```json
{
  "required_scopes": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Minimal permission strings the command needs from the active credential"
  }
}
```

---

## Wire Format

```bash
$ gh issue list --schema
```

```json
{
  "command": "issue list",
  "danger_level": "safe",
  "required_scopes": ["repo:read"],
  "flags": {
    "repo": { "type": "string", "required": true, "description": "Repository in owner/name format" },
    "limit": { "type": "integer", "required": false, "default": 30, "description": "Maximum number of issues to return" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Issue list returned",        "retryable": false, "side_effects": "none" },
    "8": { "name": "AUTH_ERROR","description": "Credential missing or invalid","retryable": false, "side_effects": "none" }
  }
}
```

A command requiring no authentication:

```json
{
  "command": "version",
  "danger_level": "safe",
  "required_scopes": [],
  "flags": {},
  "exit_codes": {
    "0": { "name": "SUCCESS", "description": "Version printed", "retryable": false, "side_effects": "none" }
  }
}
```

---

## Example

Declaring scopes at registration — the framework enforces presence and surfaces the value in schema output:

```
register command "issue list":
  danger_level: safe
  required_scopes: ["repo:read"]
  exit_codes:
    SUCCESS(0): description: "Issue list returned", retryable: false, side_effects: none
    AUTH_ERROR(8): description: "Credential missing or invalid", retryable: false, side_effects: none

register command "repo delete":
  danger_level: destructive
  required_scopes: ["delete_repo"]
  exit_codes:
    SUCCESS(0): description: "Repository deleted", retryable: false, side_effects: complete
    AUTH_ERROR(8): description: "Credential missing or lacks delete_repo scope", retryable: false, side_effects: none

register command "version":
  danger_level: safe
  required_scopes: []        # no external auth needed
  exit_codes:
    SUCCESS(0): description: "Version printed", retryable: false, side_effects: none
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Composes: `required_scopes` and `danger_level` together form the command's security profile |
| [REQ-O-047](o-047-tool-check-permissions-built-in-command.md) | O | Consumes: `check-permissions` reads `required_scopes` to compute over-privilege and coverage reports |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest exposes `required_scopes` for every registered command |
| [REQ-F-063](f-063-credential-expiry-structured-error.md) | F | Extends: credential errors (expiry, missing scope) share the same `AUTH_ERROR` exit code space |
