# REQ-F-073: Environment Variable Namespace Prefix

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents set environment variables for one tool expecting them not to affect others; unprefixed names like `DEBUG`, `TOKEN`, `PORT`, `HOST` collide across tools in the same agent process

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST require a tool-scoped prefix for all environment variables the tool reads. The prefix MUST be the tool's binary name uppercased with hyphens replaced by underscores, followed by `_`. For example, a tool named `my-tool` uses prefix `MY_TOOL_`. The framework MUST document the full list of environment variables under this prefix in the manifest response.

Exceptions (read without prefix, per universal convention): `NO_COLOR`, `CI`, `HOME`, `USER`, `PATH`, `SHELL`, `TERM`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME`, `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`.

An agent setting `DEBUG=1` to enable verbose output in one tool must not accidentally enable debug mode in every other tool in the same session. Unprefixed env vars are a cross-tool contamination vector in multi-tool agent pipelines.

## Acceptance Criteria

- All tool-specific configuration env vars are documented under the `TOOLNAME_` prefix
- Setting `DEBUG=1` does not affect the tool unless the tool explicitly reads `TOOLNAME_DEBUG`
- The framework rejects (with a warning) any framework plugin that reads an unprefixed custom env var
- `tool manifest` lists all recognized env vars with their prefix
- Verified: run tool with `env -i TOOLNAME_DEBUG=1 tool --version` — debug output appears; run with `env -i DEBUG=1 tool --version` — no debug output

---

## Schema

`manifest-response` — env var entries listed under `environment` field with full prefixed names

---

## Wire Format

In manifest response:

```json
{
  "environment": [
    {"name": "MY_TOOL_TOKEN", "description": "API authentication token", "required": true},
    {"name": "MY_TOOL_DEBUG", "description": "Enable debug logging when set to 1", "required": false},
    {"name": "MY_TOOL_CONFIG", "description": "Override config file path", "required": false}
  ]
}
```

---

## Example

```
# Agent isolating two tools in the same session
MY_TOOL_DEBUG=1 my-tool list     # debug output for my-tool only
OTHER_TOOL_DEBUG=0 other-tool list  # other-tool unaffected
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Provides: manifest command that exposes the env var list |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Composes: debug mode is activated via prefixed env var |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Provides: NO_COLOR and CI are universal exceptions to the prefix rule |
