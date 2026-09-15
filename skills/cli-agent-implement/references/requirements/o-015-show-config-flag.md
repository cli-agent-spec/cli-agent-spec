# REQ-O-015: --show-config Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§28 Config File Shadowing & Precedence](../challenges/05-high-environment-and-state/28-high-config-shadowing.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST provide `tool --show-config` as a built-in invocation that outputs the effective resolved configuration, with per-key source attribution. The output MUST be JSON and MUST include: `effective_config` (resolved key-value map), `sources` (per-key source: which file or env var provided the value), and `precedence_order` (the canonical list of config sources in precedence order). This MUST reflect the state for the given invocation context (CWD, env vars at invocation time).

## Acceptance Criteria

- `tool --show-config --output json | python -c "import json,sys; json.load(sys.stdin)"` succeeds
- Each key in `sources` maps to the file path or env var name that provided its value
- `precedence_order` is present and lists all config layers in order
- The output reflects the actual resolved state, including any env var overrides

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`--show-config` returns a response with `data.effective_config`, `data.sources`, and `data.precedence_order`.

---

## Wire Format

```bash
$ tool --show-config --output json
```

```json
{
  "ok": true,
  "data": {
    "effective_config": { "region": "us-east-1", "output": "json", "timeout": 30 },
    "sources": {
      "region": "env:TOOL_REGION",
      "output": "file:/home/user/.config/tool/config.json",
      "timeout": "default"
    },
    "precedence_order": ["cli-flags", "env-vars", "/home/user/.config/tool/config.json", "defaults"]
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 12, "cwd": "/project" }
}
```

---

## Example

Opt-in at the framework level; automatically reflects the invocation context.

```
app = Framework("tool")
app.enable_show_config()   # registers --show-config globally

# Diagnose unexpected config before a critical operation:
$ tool --show-config
→ shows which file or env var set each key
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Provides: the config source data that `--show-config` exposes |
| [REQ-O-016](o-016-no-config-flag.md) | O | Composes: `--no-config` causes `sources` to be empty; `--show-config` verifies this |
| [REQ-O-024](o-024-context-config-override-flag.md) | O | Composes: `--context` and `--config` changes are reflected in `--show-config` output |
