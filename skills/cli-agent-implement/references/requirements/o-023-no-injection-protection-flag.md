# REQ-O-023: --no-injection-protection Flag

**Tier:** Opt-In | **Priority:** P3

**Source:** [§25 Prompt Injection via Output](../challenges/03-critical-security/25-critical-prompt-injection.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: High

---

## Description

The framework's external data trust tagging (REQ-F-035) MAY be bypassed for a specific invocation by passing `--no-injection-protection`. This escape hatch is intended for trusted sources (e.g., reading internal configuration authored by the operator). When this flag is passed, external data is not wrapped with trust markers. The framework MUST add an `INJECTION_PROTECTION_DISABLED` warning to `warnings[]` whenever the flag is used, so the audit log (REQ-O-030), when enabled, records it in the entry's `warnings`. The flag MUST require explicit acknowledgment in non-interactive mode.

## Acceptance Criteria

- `--no-injection-protection` causes external data to be returned without `_trusted: false` tagging
- `--no-injection-protection` adds an `INJECTION_PROTECTION_DISABLED` warning to `warnings[]`
- With the audit log enabled, the entry for that invocation has `INJECTION_PROTECTION_DISABLED` in its `warnings`
- The flag is documented with a security warning in `--help` output

---

## Schema

No dedicated schema type — this requirement disables trust tagging behavior (REQ-F-035) without adding new wire-format fields. When the flag is active, external data fields are returned as plain values rather than wrapped with `_trusted: false` markers.

---

## Wire Format

Without `--no-injection-protection` (default behavior, trust tagging applied):

```bash
$ tool fetch --url https://api.example.com/data
```

```json
{
  "ok": true,
  "data": {
    "content": { "_value": "Hello world", "_trusted": false }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 88 }
}
```

With `--no-injection-protection`:

```bash
$ tool fetch --url https://internal.corp/config --no-injection-protection
```

```json
{
  "ok": true,
  "data": {
    "content": "Hello world"
  },
  "error": null,
  "warnings": [{ "code": "INJECTION_PROTECTION_DISABLED", "message": "--no-injection-protection was active; external data returned without trust markers" }],
  "meta": { "exit_code": 0, "duration_ms": 91, "injection_protection": false }
}
```

---

## Example

The flag is available on all commands once the framework's injection-protection feature is enabled at application startup:

```
app = Framework("tool")
app.enable_injection_protection()

# flag is automatically registered on every command:
# tool fetch --no-injection-protection ...
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-035](f-035-external-data-trust-tagging.md) | F | Provides: trust tagging that this flag disables |
| [REQ-O-030](o-030-opt-in-audit-log.md) | O | Consumes: `INJECTION_PROTECTION_DISABLED` is recorded in the entry's `warnings` when the log is enabled |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: warning about bypass is included in the standard `warnings` array |
