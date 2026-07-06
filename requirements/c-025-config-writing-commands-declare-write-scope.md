# REQ-C-025: Config-Writing Commands Declare Write Scope

**Tier:** Command Contract | **Priority:** P0

**Source:** [§65 Global Configuration State Contamination](../challenges/01-critical-ecosystem-runtime-agent-specific/65-high-global-config-contamination.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

Any command that writes to a configuration file MUST declare `config_write_scope: "local" | "global" | "session"` in its registration metadata. Commands with `config_write_scope: "global"` MUST require an explicit `--global` flag from the caller and MUST emit a `GLOBAL_CONFIG_MODIFIED` warning in the JSON response. The framework defaults all config writes to `local` scope (nearest `.tool-config` in the directory hierarchy). Global config writes MUST use atomic rename to prevent partial-write corruption and MUST acquire an advisory lock before writing.

## Acceptance Criteria

- A config-write command without `--global` writes to `./.tool-config`, not `~/.config/tool/`
- `--global` causes a write to `~/.config/tool/` AND emits `GLOBAL_CONFIG_MODIFIED` in `warnings[]`
- Omitting `config_write_scope` from a config-writing command raises a framework registration warning
- A global config write interrupted mid-way leaves the previous config intact (atomic rename)

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Config-writing commands extend `CommandEntry` with:

| Field | Type | Description |
|-------|------|-------------|
| `config_write_scope` | `"local"` \| `"global"` \| `"session"` | Scope of config files this command may write |

`ResponseEnvelope.warnings` includes a standard warning code when a global write occurs:

| Warning code | Condition |
|---|---|
| `GLOBAL_CONFIG_MODIFIED` | A global-scope config file was written during this invocation |

---

## Wire Format

```bash
$ tool config set --schema
```
```json
{
  "config_write_scope": "local",
  "parameters": {
    "key":    { "type": "string",  "required": true,  "description": "Config key to set" },
    "value":  { "type": "string",  "required": true,  "description": "Value to assign" },
    "global": { "type": "boolean", "required": false, "default": false, "description": "Write to global config instead of local" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Config value written",                    "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Key or value failed validation",           "retryable": false, "side_effects": "none"     }
  }
}
```

Global write response:

```json
{
  "ok": true,
  "data": { "key": "output.format", "value": "json", "scope": "global", "path": "/Users/alice/.config/tool/config.toml" },
  "error": null,
  "warnings": ["GLOBAL_CONFIG_MODIFIED: wrote to /Users/alice/.config/tool/config.toml"],
  "meta": { "duration_ms": 18 }
}
```

---

## Example

```
register command "config set":
  config_write_scope: local   # default; --global flag upgrades to global scope at runtime
  parameters:
    key:    type=string,  required=true
    value:  type=string,  required=true
    global: type=boolean, required=false, default=false, description="Write to global config"

# tool config set output.format json          → writes ./.tool-config
# tool config set output.format json --global → writes ~/.config/tool/config.toml
#                                               + emits GLOBAL_CONFIG_MODIFIED in warnings[]
#                                               + uses atomic rename (write to .tmp, then rename)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `config_write_scope` is part of the `--schema` output |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `GLOBAL_CONFIG_MODIFIED` warning is emitted in `ResponseEnvelope.warnings` |
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Composes: `meta` config source tracking reflects the scope written by this command |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: exit codes for config-write commands include `side_effects: complete` on success |
