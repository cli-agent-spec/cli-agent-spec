# REQ-C-011: Commands Declare Filesystem Side Effects

**Tier:** Command Contract | **Priority:** P3

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

Command authors MUST declare all filesystem side effects in the command's registration metadata using the `filesystem_side_effects` array. Each entry MUST specify: `path` (template or glob), `type` (one of: `cache`, `log`, `temp`, `credential`, `config`, `output`), `ttl_seconds` (if applicable), and `clearable_with` (the framework command to clear it; neither applies to `output`). The framework uses this information for `tool status --show-side-effects` and `tool cleanup`.

**Output paths.** `output` is a path the command writes as its product: a generated report, a rendered dashboard, collected evidence. `tool status --show-side-effects` lists it like any other kind, but `tool cleanup` never removes it under any `--scope`, because the user asked for it. An `output` entry carries neither `ttl_seconds` nor `clearable_with`: the product does not go stale and is not the framework's to clear. Declaring a product as `cache` would let `cleanup` delete what the user asked for, and leaving it undeclared hides a write.

**Output paths and `--output`.** An `output` entry declares a location the command chooses itself, fixed or templated, such as `{project_root}/tmp/dashboard/`. A path the caller names per call with `--output <path>` or `--output-dir <path>` is declared by `output_file` (REQ-O-001), not here; declaring both for the same file describes one write twice. When the command writes its product to a default location in the absence of `--output`, that default location is an `output` entry.

**Side effects and `danger_level`.** `cache`, `log`, `temp`, and `output` are not state: a command whose only writes are of these kinds keeps `danger_level: "safe"` (REQ-C-002), and declaring them here is what lets it stay `safe`. `credential` and `config` change state the next invocation reads, so a command that writes them is at least `mutating`.

## Acceptance Criteria

- A command that writes to a cache directory declares that path in `filesystem_side_effects`
- `tool status --show-side-effects` lists all paths declared by registered commands
- `tool cleanup` removes all paths declared as `type: "temp"` or `type: "cache"`
- A command that writes a generated report under a path it chooses declares that path with `type: "output"`
- `tool status --show-side-effects` lists `output` paths with their type and size
- `tool cleanup`, with any `--scope` including `all`, removes no path declared as `type: "output"`
- A `filesystem_side_effects` entry with `type: "output"` and `ttl_seconds` or `clearable_with` fails schema validation
- A command whose only declared writes are `cache`, `log`, `temp`, or `output` may declare `danger_level: "safe"`
- A command whose result file comes only from `--output <path>` declares `output_file`, and no `output` entry for that path

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
        "type":           { "type": "string", "enum": ["cache", "log", "temp", "credential", "config", "output"], "description": "Category of the side effect; output is the command's product" },
        "ttl_seconds":    { "type": "integer", "description": "Seconds until the path is considered stale; omit if permanent" },
        "clearable_with": { "type": "string", "description": "Framework command that removes this path" }
      },
      "if": { "properties": { "type": { "const": "output" } }, "required": ["type"] },
      "then": { "not": { "anyOf": [{ "required": ["ttl_seconds"] }, { "required": ["clearable_with"] }] } }
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

A read-only command that writes a rendered dashboard as its product:

```json
{
  "command": "dashboard.build",
  "danger_level": "safe",
  "filesystem_side_effects": [
    { "path": "{project_root}/tmp/dashboard/", "type": "output" }
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

register command "services.inspect":
  danger_level: safe
  filesystem_side_effects:
    - path: "{project_root}/tmp/evidence/{service}/"
      type: output
  exit_codes:
    SUCCESS(0): description: "Evidence collected", retryable: false, side_effects: complete
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
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Composes: writes of `cache`, `log`, `temp`, and `output` paths leave a command `safe` |
| [REQ-O-001](o-001-output-format-flag.md) | O | Composes: a per-call `--output` path is declared by `output_file`, a command-chosen product path by `type: "output"` |
