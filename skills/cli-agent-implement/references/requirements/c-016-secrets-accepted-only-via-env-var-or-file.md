# REQ-C-016: Secrets Accepted Only via Env Var or File

**Tier:** Command Contract | **Priority:** P1

**Source:** [§24 Authentication & Secret Handling](../challenges/03-critical-security/24-critical-auth-secrets.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Commands MUST NOT declare parameters intended to receive secret values (tokens, passwords, keys) as positional or named command-line arguments. Secrets MUST be accepted via environment variable references only. The framework MUST provide `--secret-from-env VAR_NAME` and `--secret-from-file PATH` as standard flag templates that command authors use instead of bare `--password` style flags. The framework MUST reject command registrations that declare a parameter matching the secret field pattern (REQ-F-034) as a direct CLI argument.

## Acceptance Criteria

- No framework-based command accepts `--password`, `--token`, or `--api-key` as a direct argument containing the secret value
- Commands that need a secret declare it via `--token-from-env` or `--token-from-file` pattern
- The framework raises a registration error if a command declares a secret-named argument as a direct value argument
- Environment variable names used for secrets are documented in the command's `--schema` output

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

Secret parameters appear in `CommandEntry.flags` using the `--x-from-env` / `--x-from-file` naming pattern. A `secret_env_vars` field in the schema lists all accepted environment variable names:

| Field | Type | Description |
|-------|------|-------------|
| `secret_env_vars` | string[] | Environment variable names that supply secret values for this command |

---

## Wire Format

```bash
$ tool login --schema
```
```json
{
  "parameters": {
    "token-from-env":  { "type": "string", "required": false, "description": "Env var name holding the API token" },
    "token-from-file": { "type": "string", "required": false, "description": "Path to file containing the API token" }
  },
  "secret_env_vars": ["MY_TOOL_TOKEN", "MY_TOOL_TOKEN_FILE"],
  "exit_codes": {
    "0": { "name": "SUCCESS",       "description": "Authentication succeeded",       "retryable": false, "side_effects": "complete" },
    "8": { "name": "AUTH_REQUIRED", "description": "Token missing, invalid, or expired", "retryable": false, "side_effects": "none" }
  }
}
```

---

## Example

The command author uses the framework's secret flag templates instead of bare value flags:

```
register command "login":
  # CORRECT — secret arrives via env var reference, never as a direct value
  flag: --token-from-env  type=string, description="Env var name holding the API token"
  flag: --token-from-file type=string, description="Path to file containing the API token"
  secret_env_vars: [MY_TOOL_TOKEN, MY_TOOL_TOKEN_FILE]

  # INCORRECT — framework raises a registration error
  flag: --token type=string, description="API token value"
  #  → framework error: 'token' matches secret field pattern; use --token-from-env instead
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret field pattern used to reject direct-value declarations |
| [REQ-C-021](c-021-auth-commands-declare-headless-mode-support.md) | C | Composes: `token_env_vars` from headless auth declaration mirrors `secret_env_vars` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `secret_env_vars` is part of the `--schema` output |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Enforces: secret values read from env are redacted in debug/trace output |
