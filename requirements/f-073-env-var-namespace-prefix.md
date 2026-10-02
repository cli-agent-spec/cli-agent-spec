# REQ-F-073: Environment Variable Namespace Prefix

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents set environment variables for one tool expecting them not to affect others; unprefixed names like `DEBUG`, `TOKEN`, `PORT`, `HOST` collide across tools in the same agent process

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST require a tool-scoped prefix for all environment variables the tool reads. The prefix MUST be the tool's binary name uppercased with hyphens replaced by underscores, followed by `_`. For example, a tool named `my-tool` uses prefix `MY_TOOL_`. The framework MUST declare in the manifest response every environment variable the tool reads outside the universal exceptions below, in one of four homes:

1. `token_env_vars` of an auth command (REQ-C-021): a variable that supplies a pre-acquired token in place of the command's interactive authentication
2. `secret_env_vars` (REQ-C-016): any other variable that supplies a secret. A secret every command reads, such as a tool-wide API key, goes in the manifest's root `secret_env_vars` (ManifestResponse 3.13); a secret only some commands read goes in each of those commands' `secret_env_vars`
3. A flag's `env_vars` (ManifestResponse 3.4): a variable that supplies that flag's value when the flag is not passed
4. The manifest's root `env_vars` with a `description` (ManifestResponse 3.5): every other variable, such as `<TOOLNAME>_DEBUG`, `<PREFIX>AUDIT_LOG`, or `<PREFIX>SESSION_ID` (REQ-O-030)

When a variable fits two homes, the first in this order wins: a token an auth command accepts sits in its `token_env_vars` and not in that command's `secret_env_vars`; a secret never sits in a flag's `env_vars`, even when it backs a `--x-from-env` flag; a variable that backs a flag never sits in root `env_vars`. Root homes are exclusive: a name in root `env_vars` appears nowhere else in the manifest, and a name in root `secret_env_vars` appears in no command's `secret_env_vars` and no flag's `env_vars`. The one overlap allowed is a root secret that an auth command also accepts as a pre-acquired token, which that command still names in `token_env_vars` because REQ-C-021 requires the list. The universal exceptions are listed in no home.

Exceptions (read without prefix, per universal convention): `NO_COLOR`, `CI`, `HOME`, `USER`, `PATH`, `PWD`, `SHELL`, `TERM`, `COLUMNS`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME`, `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `ALL_PROXY` and their lowercase forms `http_proxy`, `https_proxy`, `no_proxy`, `all_proxy`, `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `GITHUB_ACTIONS`, `JENKINS_URL`.

**Declared names without the prefix.** A flag MAY also read a variable outside the prefix and the exceptions, such as a service's established name (`AWS_REGION`) or one shared across a family of tools (`CLOUDFALL_PROJECT`), only when the manifest declares that name in the flag's `env_vars` and the tool-prefixed name is also listed and comes first in precedence. Contamination comes from variables a tool reads without saying so; a declared name is visible to the agent, which can set or unset it on purpose, and the prefixed name set for this tool always overrides one set for another. The framework MUST reject a registration that reads an undeclared name without the prefix, or lists one ahead of the prefixed name.

Root `env_vars` follows the same rule. A tool-wide setting MAY also read a declared name without the prefix, such as `LEDGER_FILE` kept for an established ecosystem, only when root `env_vars` also lists the setting's tool-prefixed name (`MY_TOOL_LEDGER`) immediately before it, the tool reads the prefixed name first, and the unprefixed entry's `description` names the prefixed variable that overrides it.

An agent setting `DEBUG=1` to enable verbose output in one tool must not accidentally enable debug mode in every other tool in the same session. Unprefixed env vars are a cross-tool contamination vector in multi-tool agent pipelines.

## Acceptance Criteria

- All tool-specific configuration env vars are documented under the `TOOLNAME_` prefix
- Setting `DEBUG=1` does not affect the tool unless the tool explicitly reads `TOOLNAME_DEBUG`
- The framework rejects (with a warning) any framework plugin that reads an unprefixed custom env var it does not declare in a flag's `env_vars`
- `tool manifest` lists every variable that supplies a flag's value in that flag's `env_vars`, in the order the parser reads them, every token variable of an auth command in its `token_env_vars`, and every other secret variable in root `secret_env_vars` when every command reads it, otherwise in the `secret_env_vars` of each command that reads it
- A flag whose `env_vars` holds a name without the prefix (outside the exceptions) also lists the tool-prefixed name, first; the framework rejects a registration that breaks this
- No name in a command's or the root `secret_env_vars` appears in any flag's `env_vars`; no name in an auth command's `token_env_vars` also appears in that command's `secret_env_vars`; no name in root `secret_env_vars` appears in any command's `secret_env_vars`
- `tool manifest` lists every other variable the tool reads outside the universal exceptions in root `env_vars`, each with a `description`; no name there appears in any flag's `env_vars`, any `secret_env_vars`, or any `token_env_vars`
- Each root `env_vars` entry carries the tool prefix, or is a declared name without it that immediately follows the entry for the same setting's tool-prefixed name; the tool reads the prefixed name first, and the framework rejects a registration that breaks this
- No universal exception appears in any of the four homes
- Verified: a tool that reads `MY_TOOL_API_KEY` for every command lists it in root `secret_env_vars` and in no command's `secret_env_vars`
- Verified: with both `MY_TOOL_LEDGER` and `LEDGER_FILE` set, the tool uses `MY_TOOL_LEDGER`; with only `LEDGER_FILE` set, it uses that
- Verified: a tool that reads `TOOLNAME_DEBUG` without a `--debug` flag lists it in root `env_vars`
- Verified: with both `TOOL_PROJECT` and `CLOUDFALL_PROJECT` set, `tool deploy` uses `TOOL_PROJECT`; with only `CLOUDFALL_PROJECT` set, it uses that; `--project` overrides both
- Verified: run tool with `env -i TOOLNAME_DEBUG=1 tool --version` — debug output appears; run with `env -i DEBUG=1 tool --version` — no debug output

---

## Schema

**Types:** [`manifest-response.json`](../schemas/manifest-response.json) · [`manifest-response.md`](../schemas/manifest-response.md)

`FlagEntry.env_vars` lists the variables a flag reads when it is not passed, each an `EnvVarEntry` `{name, deprecated?, description?}`, in precedence order. Secret variables stay in `CommandEntry.secret_env_vars`, or in the root `secret_env_vars` (a string array of names, ManifestResponse 3.13) when every command reads them; an auth command's pre-acquired token variables stay in `CommandEntry.token_env_vars`. Root `env_vars` lists every other variable as an `EnvVarEntry` whose `description` is required.

---

## Wire Format

`tool manifest` declares the variables on the flags that read them, the tool-wide secret at the root, the command's own secret on the command, and the rest in root `env_vars`:

```json
{
  "schema_version": "3.13",
  "framework_version": "2.4.0",
  "etag": "sha256:51c0de",
  "env_vars": [
    { "name": "MY_TOOL_DEBUG", "description": "1 turns on debug output on stderr, with secrets redacted" },
    { "name": "MY_TOOL_AUDIT_LOG", "description": "1 turns the audit log on, 0 turns it off, an absolute path turns it on at that path" },
    { "name": "MY_TOOL_LEDGER", "description": "Path of the ledger file every command reads" },
    { "name": "LEDGER_FILE", "description": "Path of the ledger file, the ecosystem's established name; MY_TOOL_LEDGER overrides it" }
  ],
  "secret_env_vars": ["MY_TOOL_API_KEY"],
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

# A tool-wide setting keeps the ecosystem's name behind the prefixed one
LEDGER_FILE=main.ledger my-tool list                              # ledger: main.ledger
MY_TOOL_LEDGER=test.ledger LEDGER_FILE=main.ledger my-tool list   # ledger: test.ledger
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Provides: manifest command that exposes each flag's `env_vars` and the root `env_vars` |
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | C | Composes: secret variables are declared in a command's or the root `secret_env_vars`, never in a flag's `env_vars` |
| [REQ-C-021](c-021-auth-commands-declare-headless-mode-support.md) | C | Composes: an auth command's pre-acquired token variables are declared in its `token_env_vars`, the first home |
| [REQ-O-042](o-042-output-format-env-var-default.md) | O | Specializes: `<TOOLNAME>_FORMAT` is the `env_vars` entry of `--format` |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Composes: debug mode is activated via a prefixed env var declared in root `env_vars` when no flag backs it |
| [REQ-O-030](o-030-opt-in-audit-log.md) | O | Composes: `<PREFIX>AUDIT_LOG` and the session variable are declared in root `env_vars` |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Provides: NO_COLOR and CI are universal exceptions to the prefix rule |
