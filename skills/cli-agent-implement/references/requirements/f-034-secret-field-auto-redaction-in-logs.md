# REQ-F-034: Secret Field Auto-Redaction in Logs

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§24 Authentication & Secret Handling](../challenges/03-critical-security/24-critical-auth-secrets.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST automatically redact any argument or field whose name matches a secret pattern (case-insensitive substrings: `token`, `secret`, `password`, `key`, `credential`, `auth`) before writing to the audit log or stderr. Redaction MUST replace the value with `"[REDACTED]"`. This MUST apply to: command-line argument values, environment variable values echoed in diagnostics, and JSON response fields that match the pattern.

## Acceptance Criteria

- An argument `--api-token abc123` appears as `--api-token [REDACTED]` in the audit log
- A response field `"password": "secret"` appears as `"password": "[REDACTED]"` in the audit log
- The actual command execution is not affected by redaction (redaction is log-layer only)
- Redaction applies to field names matched case-insensitively

---

## Schema

No dedicated schema type — this requirement governs log-layer redaction behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only. Redaction is applied only to log output (audit log, stderr diagnostics); the command's JSON response on stdout is not modified.

---

## Example

Framework-Automatic: no command author action needed. The framework's log and audit-write layers scan field names before serialization and replace matching values with `"[REDACTED]"`.

```
$ tool auth login --api-token abc123 --password hunter2
→ stdout (command response, unredacted):
  {"ok":true,"data":{"user":"alice"},...}

→ audit.jsonl entry (redacted):
  {"command":"auth login","args":{"api-token":"[REDACTED]","password":"[REDACTED]"},"exit_code":0,...}

→ stderr debug output (redacted):
  DEBUG args: --api-token [REDACTED] --password [REDACTED]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Consumes: every audit log entry passes through the redaction layer defined here |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Extends: applies the same redaction patterns to debug and trace mode output |
| [REQ-F-058](f-058-high-entropy-field-masking.md) | F | Composes: high-entropy field masking works alongside named-pattern redaction |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: stdout response envelope is not modified — redaction is log-layer only |
