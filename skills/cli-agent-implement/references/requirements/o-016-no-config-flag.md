# REQ-O-016: --no-config Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§28 Config File Shadowing & Precedence](../challenges/05-high-environment-and-state/28-high-config-shadowing.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST provide `--no-config` as a standard flag on every command. When passed, the framework MUST skip loading all config files (local `.toolrc`, user `~/.config/tool/config.*`, and system `/etc/tool/config.*`). Environment variable overrides MUST still apply (they are not "config files"). With `--no-config`, behavior MUST depend only on explicit CLI flags and compiled-in defaults, making the invocation fully reproducible regardless of the execution environment's config files.

## Acceptance Criteria

- `--no-config` causes no config file to be read, regardless of what files exist
- Environment variables still take effect with `--no-config`
- `meta.config_sources` is an empty array when `--no-config` is passed
- `--no-config` is present in every command's `--help` output

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When `--no-config` is passed, `meta.config_sources` is an empty array, confirming no config files were loaded.

---

## Wire Format

```bash
$ tool deploy --target staging --no-config --format json
```

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "config_sources": [], "duration_ms": 941 }
}
```

---

## Example

Opt-in at the framework level; automatically available on every command.

```
app = Framework("tool")
app.enable_no_config()   # registers --no-config on all commands

# Reproducible invocation independent of environment config files:
$ tool deploy --target staging --region us-east-1 --no-config
→ meta.config_sources: []  # only CLI flags and env vars apply
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Provides: `meta.config_sources` field that `--no-config` sets to empty |
| [REQ-O-015](o-015-show-config-flag.md) | O | Composes: `--show-config` with `--no-config` confirms no files were loaded |
| [REQ-O-024](o-024-context-config-override-flag.md) | O | Composes: `--context` and `--no-config` may be combined for isolated context |
