# REQ-F-073: Environment Variable Namespace Prefix

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents set environment variables for one tool expecting them not to affect others; unprefixed names like `DEBUG`, `TOKEN`, `PORT`, `HOST` collide across tools in the same agent process

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST require a tool-scoped prefix for all environment variables the tool reads. The prefix MUST be the tool's binary name uppercased with hyphens replaced by underscores, followed by `_`. For example, a tool named `my-tool` uses prefix `MY_TOOL_`. The framework MUST declare in the manifest response every environment variable that supplies a flag's value, in that flag's `env_vars` (ManifestResponse 3.4), every variable that supplies a secret in the command's `secret_env_vars` (REQ-C-016), and every other variable it reads, such as `<TOOLNAME>_DEBUG`, `<PREFIX>AUDIT_LOG`, or `<PREFIX>SESSION_ID` (REQ-O-030), in the manifest's root `env_vars` with a `description` (ManifestResponse 3.5). Each recognized variable has exactly one of these three homes: a secret never appears in a flag's `env_vars`, and a name in root `env_vars` appears in neither. The universal exceptions below are not listed.

Exceptions (read without prefix, per universal convention): `NO_COLOR`, `CI`, `HOME`, `USER`, `PATH`, `SHELL`, `TERM`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME`, `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`.

**Declared names without the prefix.** A flag MAY also read a variable outside the prefix and the exceptions, such as a service's established name (`AWS_REGION`) or one shared across a family of tools (`CLOUDFALL_PROJECT`), only when the manifest declares that name in the flag's `env_vars` and the tool-prefixed name is also listed and comes first in precedence. Contamination comes from variables a tool reads without saying so; a declared name is visible to the agent, which can set or unset it on purpose, and the prefixed name set for this tool always overrides one set for another. The framework MUST reject a registration that reads an undeclared name without the prefix, or lists one ahead of the prefixed name.

An agent setting `DEBUG=1` to enable verbose output in one tool must not accidentally enable debug mode in every other tool in the same session. Unprefixed env vars are a cross-tool contamination vector in multi-tool agent pipelines.

## Acceptance Criteria

- All tool-specific configuration env vars are documented under the `TOOLNAME_` prefix
- Setting `DEBUG=1` does not affect the tool unless the tool explicitly reads `TOOLNAME_DEBUG`
- The framework rejects (with a warning) any framework plugin that reads an unprefixed custom env var it does not declare in a flag's `env_vars`
- `tool manifest` lists every variable that supplies a flag's value in that flag's `env_vars`, in the order the parser reads them, and every secret variable in the command's `secret_env_vars`
- A flag whose `env_vars` holds a name without the prefix (outside the exceptions) also lists the tool-prefixed name, first; the framework rejects a registration that breaks this
- No name in a command's `secret_env_vars` appears in any flag's `env_vars`
- `tool manifest` lists every other variable the tool reads outside the universal exceptions in root `env_vars`, each with the tool prefix and a `description`; no name there appears in any flag's `env_vars` or any `secret_env_vars`, so every recognized variable appears in exactly one of the three
- Verified: a tool that reads `TOOLNAME_DEBUG` without a `--debug` flag lists it in root `env_vars`
- Verified: with both `TOOL_PROJECT` and `CLOUDFALL_PROJECT` set, `tool deploy` uses `TOOL_PROJECT`; with only `CLOUDFALL_PROJECT` set, it uses that; `--project` overrides both
- Verified: run tool with `env -i TOOLNAME_DEBUG=1 tool --version` — debug output appears; run with `env -i DEBUG=1 tool --version` — no debug output

---

## Schema

**Types:** [`manifest-response.json`](../schemas/manifest-response.json) · [`manifest-response.md`](../schemas/manifest-response.md)

`FlagEntry.env_vars` lists the variables a flag reads when it is not passed, each an `EnvVarEntry` `{name, deprecated?, description?}`, in precedence order. Secret variables stay in `CommandEntry.secret_env_vars`. Root `env_vars` lists every other variable as an `EnvVarEntry` whose `description` is required.

---

## Wire Format

`tool manifest` declares the variables on the flags that read them, the secrets on the command, and the rest at the root:

```json
{
  "schema_version": "3.5",
  "framework_version": "2.4.0",
  "etag": "sha256:51c0de",
  "env_vars": [
    { "name": "MY_TOOL_DEBUG", "description": "1 turns on debug output on stderr, with secrets redacted" },
    { "name": "MY_TOOL_AUDIT_LOG", "description": "1 turns the audit log on, 0 turns it off, an absolute path turns it on at that path" }
  ],
  "commands": {
    "deploy": {
      "description": "Deploy a build to a project",
      "danger_level": "mutating",
      "required_scopes": ["deploy:write"],
      "secret_env_vars": ["MY_TOOL_TOKEN"],
      "flags": {
        "project": {
          "type": "string",
          "required": true,
          "description": "Project to deploy to",
          "env_vars": [{ "name": "MY_TOOL_PROJECT" }, { "name": "CLOUDFALL_PROJECT" }]
        },
        "config": {
          "type": "string",
          "required": false,
          "description": "Config file path",
          "env_vars": [{ "name": "MY_TOOL_CONFIG" }, { "name": "MY_TOOL_CONF", "deprecated": true }]
        }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```

---

## Example

```
# Agent isolating two tools in the same session
MY_TOOL_DEBUG=1 my-tool list     # debug output for my-tool only
OTHER_TOOL_DEBUG=0 other-tool list  # other-tool unaffected

# A family-wide name is honored only because the manifest declares it
CLOUDFALL_PROJECT=web my-tool deploy                         # project: web
MY_TOOL_PROJECT=api CLOUDFALL_PROJECT=web my-tool deploy     # project: api (prefixed name first)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Provides: manifest command that exposes each flag's `env_vars` and the root `env_vars` |
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | C | Composes: secret variables are declared in `secret_env_vars`, never in a flag's `env_vars` |
| [REQ-O-042](o-042-output-format-env-var-default.md) | O | Specializes: `<TOOLNAME>_FORMAT` is the `env_vars` entry of `--format` |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Composes: debug mode is activated via a prefixed env var declared in root `env_vars` when no flag backs it |
| [REQ-O-030](o-030-opt-in-audit-log.md) | O | Composes: `<PREFIX>AUDIT_LOG` and the session variable are declared in root `env_vars` |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Provides: NO_COLOR and CI are universal exceptions to the prefix rule |
