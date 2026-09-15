# REQ-F-058: High-Entropy Field Masking

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§59 High-Entropy String Token Poisoning](../challenges/01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md)

**Addresses:** Severity: High / Token Spend: High / Time: Low / Context: High

---

## Description

The framework MUST automatically detect and mask high-entropy string values in JSON output unless `--unmask` is explicitly passed. Detection criteria: strings matching base64 pattern (`[A-Za-z0-9+/]{40,}={0,2}`), JWT three-part structure (`[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`), or fields declared `high_entropy: true` in the command schema. Masked values MUST be replaced with a semantic summary: for JWTs — `[JWT: sub=<sub>, exp=<exp>]`; for API keys — `[KEY: <first8>...]`; for base64 — `[BASE64: <bytecount> bytes]`. The raw value MUST be accessible via `--unmask`.

## Acceptance Criteria

- A JWT in a response field is replaced with `[JWT: sub=user_123, exp=2024-03-11T15:00:00Z]` by default
- A 256-character base64 string is replaced with `[BASE64: 192 bytes]` by default
- `--unmask` produces the raw value
- Fields declared `high_entropy: true` in the schema are always masked regardless of content pattern

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

High-entropy fields in `data` are replaced with semantic summary strings. The raw value is only emitted when `--unmask` is passed.

---

## Wire Format

```json
{
  "ok": true,
  "data": {
    "token": "[KEY: ghp_abc1...]",
    "session": "[JWT: sub=user_42, exp=2025-01-01T00:00:00Z]",
    "cert_blob": "[BASE64: 1024 bytes]"
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 14 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework scans all `data` fields before serialization and masks values matching high-entropy patterns.

```
# Default — values masked
$ mytool token create --json
{
  "ok": true,
  "data": { "token": "[KEY: ghp_abc1...]" },
  ...
}

# --unmask — raw value emitted
$ mytool token create --json --unmask
{
  "ok": true,
  "data": { "token": "ghp_abc123456789abcdef" },
  ...
}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` `data` field where masking is applied |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Composes: log redaction applies the same high-entropy detection to log output |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Composes: debug/trace mode must also respect masking for high-entropy values |
