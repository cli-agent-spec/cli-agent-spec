# REQ-C-011: Commands Declare Filesystem Side Effects

**Tier:** Command Contract | **Priority:** P3

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

Command authors MUST declare all filesystem side effects in the command's registration metadata using the `filesystem_side_effects` array. Each entry MUST specify: `path` (template or glob), `type` (one of: `cache`, `log`, `temp`, `credential`, `config`), `ttl_seconds` (if applicable), and `clearable_with` (the framework command to clear it). The framework uses this information for `tool status --show-side-effects` and `tool cleanup`.

## Acceptance Criteria

- A command that writes to a cache directory declares that path in `filesystem_side_effects`
- `tool status --show-side-effects` lists all paths declared by registered commands
- `tool cleanup` removes all paths declared as `type: "temp"` or `type: "cache"`

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

The `filesystem_side_effects` array is declared at registration and appears in the command's `--schema` output.

```json
{
  "filesystem_side_effects": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["path", "type"],
      "properties": {
        "path":           { "type": "string", "description": "Template or glob for paths written by the command" },
        "type":           { "type": "string", "enum": ["cache", "log", "temp", "credential", "config"], "description": "Category of the side effect" },
        "ttl_seconds":    { "type": "integer", "description": "Seconds until the path is considered stale; omit if permanent" },
        "clearable_with": { "type": "string", "description": "Framework command that removes this path" }
      }
    },
    "description": "All filesystem locations the command may write to"
  }
}
```

---

## Wire Format

```bash
$ tool fetch-schema --schema
```

```json
{
  "command": "fetch-schema",
  "filesystem_side_effects": [
    {
      "path": "~/.cache/tool/schemas/",
      "type": "cache",
      "ttl_seconds": 3600,
      "clearable_with": "tool cache clear --scope schemas"
    }
  ]
}
```

---

## Example

A command that writes to a cache directory declares the path, type, TTL, and the command that clears it at registration.

```
register command "fetch-schema":
  danger_level: safe
  filesystem_side_effects:
    - path: "~/.cache/tool/schemas/"
      type: cache
      ttl_seconds: 3600
      clearable_with: "tool cache clear --scope schemas"
  exit_codes:
    SUCCESS(0): description: "Schema fetched and cached", retryable: false, side_effects: complete

register command "process":
  danger_level: mutating
  filesystem_side_effects:
    - path: "/tmp/tool-process-{session_id}/"
      type: temp
      ttl_seconds: 3600
      clearable_with: "tool cleanup --session {session_id}"
    - path: "~/.local/share/tool/logs/{date}.log"
      type: log
      clearable_with: "tool cleanup --logs"
  exit_codes:
    SUCCESS(0): description: "Processing completed", retryable: false, side_effects: complete
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-027](o-027-tool-cleanup-built-in-command.md) | O | Consumes: `clearable_with` commands declared here are aggregated and invoked by `tool cleanup` |
| [REQ-O-028](o-028-tool-status-built-in-command.md) | O | Consumes: `filesystem_side_effects` declarations are listed by `tool status --show-side-effects` |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Provides: framework-managed session temp directory that auto-cleans on session end |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | F | Provides: framework log rotation for paths declared as `type: "log"` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest exposes `filesystem_side_effects` for each command |
