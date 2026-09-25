# REQ-O-027: tool cleanup Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

The framework MUST provide a built-in `tool cleanup` command that removes all known filesystem side effect paths declared by registered commands. The command MUST accept `--scope <type>` (one of: `all`, `temp`, `cache`, `logs`) to limit cleanup to specific categories. The command MUST output a structured JSON summary of what was removed and total disk space reclaimed. The command MUST NOT remove files younger than `--min-age <seconds>` (default: 0).

## Acceptance Criteria

- `tool cleanup --scope temp` removes all paths declared as `type: "temp"` in command schemas
- `tool cleanup --format json` returns a list of removed paths and total bytes freed
- `tool cleanup --min-age 3600` does not remove any file or directory created in the last hour
- `tool cleanup --scope cache` does not affect logs or temp files

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.cleaned` is an array of objects with `path`, `type`, and `bytes_freed` fields.

---

## Wire Format

```bash
$ tool cleanup --scope temp --format json
```

```json
{
  "ok": true,
  "data": {
    "cleaned": [
      { "path": "/tmp/tool-session-abc123/", "type": "temp", "bytes_freed": 1048576 },
      { "path": "/tmp/tool-session-def456/", "type": "temp", "bytes_freed": 524288 }
    ],
    "total_bytes_freed": 1572864
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 28 }
}
```

---

## Example

Opt-in at the framework level.

```
app = Framework("tool")
app.enable_cleanup()

# Clean all declared side-effect paths:
$ tool cleanup --scope all

# Clean only cache files:
$ tool cleanup --scope cache

# Clean only files older than 1 hour:
$ tool cleanup --min-age 3600
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Provides: declarations of paths that `tool cleanup` removes |
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | F | Composes: auto-cleanup handles session temp files; `tool cleanup` handles explicit cleanup |
| [REQ-O-028](o-028-tool-status-built-in-command.md) | O | Composes: `tool status --show-side-effects` lists what `tool cleanup` will remove |
