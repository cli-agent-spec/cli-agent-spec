# REQ-F-051: Debug and Trace Mode Secret Redaction

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§42 Debug / Trace Mode Secret Leakage](../challenges/01-critical-ecosystem-runtime-agent-specific/42-critical-debug-secret-leakage.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: Low / Context: Medium

---

## Description

When `--debug`, `--trace`, `--verbose`, or any elevated verbosity flag is active, the framework MUST apply the same secret redaction rules defined in REQ-F-034 to ALL output, including HTTP request/response dumps, environment variable listings, and argument echoing. The framework MUST redact: HTTP headers matching `Authorization`, `Cookie`, `X-Api-Key`, `X-Auth-Token`, `Proxy-Authorization`; environment variables matching `*_KEY`, `*_SECRET`, `*_TOKEN`, `*_PASSWORD`, `*_PASS`, `API_*`, `AUTH_*`; and any argument declared as `secret: true` in the command schema. Redacted values MUST be replaced with `[REDACTED]`.

## Acceptance Criteria

- An HTTP request log in debug mode shows `Authorization: [REDACTED]`, not the actual token
- Environment variable dumps in trace mode show `AWS_SECRET_ACCESS_KEY=[REDACTED]`
- An argument declared as `secret: true` is never echoed in any verbosity level
- The redaction applies to both stderr debug output and any audit log entries created during debug mode

---

## Schema

No dedicated schema type — this requirement governs debug output filtering without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework intercepts all debug output and applies the redaction rules before writing.

```
# Command author declares a secret argument
register argument "api_key":
  type: string
  secret: true

# Debug mode output — values automatically redacted
$ tool deploy --api-key "sk-abc123" --debug
[DEBUG] HTTP POST https://api.example.com/deploy
[DEBUG]   Authorization: [REDACTED]
[DEBUG]   X-Api-Key: [REDACTED]
[DEBUG] env: AWS_SECRET_ACCESS_KEY=[REDACTED]
[DEBUG] args: api_key=*** target=prod

# Without --debug, no sensitive output is emitted at all
$ tool deploy --api-key "sk-abc123"
→ {"ok":true,"data":{...}}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Provides: base secret redaction rules that this requirement extends to debug/trace mode |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Enforces: audit log entries written during debug mode are also redacted |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | F | Composes: redacted debug output is written to the rotated log files |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Enforces: error responses must not include secret values even in debug mode |
