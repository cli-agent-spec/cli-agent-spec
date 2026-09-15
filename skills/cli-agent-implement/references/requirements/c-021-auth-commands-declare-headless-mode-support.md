# REQ-C-021: Auth Commands Declare Headless Mode Support

**Tier:** Command Contract | **Priority:** P0

**Source:** [§45 Headless Authentication / OAuth Browser Flow Blocking](../challenges/01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Any command that performs authentication or credential acquisition MUST declare `headless_supported: true | false` in its registration metadata. Commands with `headless_supported: false` MUST also declare `token_env_vars: [...]` — the list of environment variable names that can supply a pre-acquired token instead. When a `headless_supported: false` command is invoked in non-TTY mode without a populated token env var, the framework MUST exit with code 4 and a structured error listing the required env vars. Command authors MUST NOT launch browser redirects in non-TTY mode.

## Acceptance Criteria

- A browser-auth command invoked in non-TTY mode without a token env var exits with code 4 and lists the required env vars
- A browser-auth command invoked in non-TTY mode with a valid token in `MY_TOOL_TOKEN` succeeds
- The `--schema` output for auth commands includes `headless_supported` and `token_env_vars`
- A headless-supported auth command (e.g., device code flow) works in non-TTY mode without any token env var

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

Auth commands extend `CommandEntry` with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `headless_supported` | boolean | yes | Whether this command can authenticate in non-TTY mode without a pre-acquired token |
| `token_env_vars` | string[] | when `headless_supported: false` | Env var names that can supply a pre-acquired token |

---

## Wire Format

```bash
$ tool auth login --schema
```
```json
{
  "parameters": {
    "provider": { "type": "enum", "required": false, "default": "oauth", "enum_values": ["oauth", "device", "token"], "description": "Authentication flow to use" }
  },
  "headless_supported": false,
  "token_env_vars": ["MY_TOOL_TOKEN", "MY_TOOL_TOKEN_FILE"],
  "exit_codes": {
    "0": { "name": "SUCCESS",       "description": "Authentication succeeded",                           "retryable": false, "side_effects": "complete" },
    "4": { "name": "NO_TTY",        "description": "Browser auth requires TTY; set MY_TOOL_TOKEN",       "retryable": false, "side_effects": "none"     },
    "8": { "name": "AUTH_REQUIRED", "description": "Token missing, invalid, or expired",                 "retryable": false, "side_effects": "none"     }
  }
}
```

---

## Example

```
register command "auth login":
  headless_supported: false
  token_env_vars: [MY_TOOL_TOKEN, MY_TOOL_TOKEN_FILE]
  parameters:
    provider: type=enum(oauth, device, token), required=false, default=oauth

register command "auth login-device":
  headless_supported: true
  # no token_env_vars required — device code flow works in non-TTY mode

# tool auth login  (non-TTY, MY_TOOL_TOKEN not set)
#  → exit 4: {"code": "NO_TTY", "message": "Set MY_TOOL_TOKEN or MY_TOOL_TOKEN_FILE to authenticate non-interactively"}

# tool auth login  (non-TTY, MY_TOOL_TOKEN=abc123)
#  → exit 0: authentication succeeded via env var token
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | C | Composes: `token_env_vars` names align with the secret env var declarations from REQ-C-016 |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-TTY detection that triggers enforcement of `headless_supported: false` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `headless_supported` and `token_env_vars` are part of the `--schema` output |
| [REQ-F-063](f-063-credential-expiry-structured-error.md) | F | Extends: structured auth errors reference the `token_env_vars` declared here |
