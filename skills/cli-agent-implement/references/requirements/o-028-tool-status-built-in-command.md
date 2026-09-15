# REQ-O-028: tool status Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§26 Stateful Commands & Session Management](../challenges/05-high-environment-and-state/26-high-session-management.md) · [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide a built-in `tool status` command with subflags `--show-config` (alias for REQ-O-015), `--show-side-effects` (inventory of all filesystem side effect paths with sizes), and `--show-state-files` (list of all global state files with their current values). Each flag produces a structured JSON output. The command MUST be safe (no side effects, `danger_level: "safe"`).

## Acceptance Criteria

- `tool status --show-side-effects --output json` returns paths, types, and sizes for all declared side effects
- `tool status --show-state-files --output json` returns paths and summaries of all global state files (e.g., current context, cached tokens)
- The command exits `0` and produces valid JSON regardless of what state exists
- All path values in the output are absolute

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data` contains structured session state: `logged_in`, `current_context`, `token_expires`, and `state_files` depending on the subflags passed.

---

## Wire Format

```bash
$ tool status --show-state-files --output json
```

```json
{
  "ok": true,
  "data": {
    "logged_in": true,
    "current_context": "production",
    "token_expires": "2026-03-18T07:00:00Z",
    "state_files": [
      { "path": "/home/user/.config/tool/auth.json", "purpose": "authentication token" },
      { "path": "/home/user/.config/tool/context.json", "purpose": "active context" }
    ]
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 5 }
}
```

---

## Example

Opt-in at the framework level.

```
app = Framework("tool")
app.enable_status()

# Pre-flight check before a session-sensitive operation:
$ tool status --output json | jq '.data.current_context'
"production"

# Discover all global state files for isolation:
$ tool status --show-state-files --output json
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-015](o-015-show-config-flag.md) | O | Composes: `--show-config` is aliased as a subcommand of `tool status` |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Provides: side-effect declarations surfaced by `--show-side-effects` |
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Provides: config source data shown by `tool status` |
