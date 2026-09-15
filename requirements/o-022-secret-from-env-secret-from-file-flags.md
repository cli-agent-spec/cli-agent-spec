# REQ-O-022: --secret-from-env / --secret-from-file Flags

**Tier:** Opt-In | **Priority:** P1

**Source:** [§24 Authentication & Secret Handling](../challenges/03-critical-security/24-critical-auth-secrets.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide `--<name>-from-env <VAR_NAME>` and `--<name>-from-file <PATH>` flag patterns for any command parameter declared as a secret. The framework reads the secret value from the environment variable or file at execution time and passes it to the command without the value ever appearing in the process argument list. The framework MUST validate that the env var or file exists before execution (exit `2` if not found).

## Acceptance Criteria

- `--token-from-env MY_TOKEN` reads the token from `$MY_TOKEN` without exposing it in `ps aux`
- `--token-from-file /run/secrets/token` reads the token from the file
- A missing env var or file causes exit `2` with a validation error before any side effects
- The secret value never appears in the audit log (REQ-F-034 redaction applies)

---

## Schema

No dedicated schema type — this requirement governs secret injection behavior without adding new wire-format fields. The secret value is resolved internally and passed to the command handler; the response envelope is unchanged.

---

## Wire Format

```bash
$ tool deploy --token-from-env MY_DEPLOY_TOKEN --target staging
```

```json
{
  "ok": true,
  "data": { "deployed": "staging" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 512 }
}
```

Missing env var:

```bash
$ tool deploy --token-from-env MISSING_VAR --target staging
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "ARG_ERROR",
    "message": "Environment variable MISSING_VAR is not set",
    "context": { "flag": "--token-from-env", "var": "MISSING_VAR" }
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 1 }
}
```

---

## Example

Opt-in at parameter declaration — the framework generates `--<name>-from-env` and `--<name>-from-file` variants for any parameter marked `secret: true`:

```
register command "deploy":
  parameters:
    token:
      type: string
      secret: true
      # framework auto-generates:
      #   --token-from-env <VAR_NAME>
      #   --token-from-file <PATH>
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | C | Enforces: base rule that secrets must not appear on the argument list |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Provides: redaction applied to all secret fields in audit logs |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: env var / file existence is checked in the validation phase |
| [REQ-O-026](o-026-tool-doctor-built-in-command.md) | O | Consumes: `doctor` may verify that expected secret env vars are accessible |
