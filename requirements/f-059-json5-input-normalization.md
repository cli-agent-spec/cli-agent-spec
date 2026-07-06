# REQ-F-059: JSON5 Input Normalization

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§67 Agent-Generated Input Syntax Rejection](../challenges/01-critical-ecosystem-runtime-agent-specific/67-high-json5-input.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: Low

---

## Description

The framework MUST use a forgiving JSON parser for all structured input flags (`--config`, `--filter`, `--data`, `--raw-payload`, and any flag declared with `type: json`). The parser MUST accept: trailing commas in objects and arrays, single-line `//` comments, block `/* */` comments, and unquoted keys. When strict JSON parsing is required (e.g., for schema validation), the framework MUST normalize the input to strict JSON first. If normalization fails, the error MUST include a `corrected_input` field showing the normalized form that would have been accepted.

## Acceptance Criteria

- `--config '{"key": "value",}'` (trailing comma) is accepted and parsed correctly
- `--config '{"key": "value" /* comment */}'` is accepted and parsed correctly
- A malformed input that cannot be normalized produces an error with `corrected_input` showing the closest valid form
- Normalized inputs pass JSON schema validation identically to equivalent strict JSON

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

When normalization fails, the framework emits an `ARG_ERROR (2)` response with `error.code: "INVALID_JSON"` and a `corrected_input` field in `error.detail` or as a top-level extension.

---

## Wire Format

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_JSON",
    "message": "Input could not be normalized to valid JSON",
    "retryable": false,
    "fix_required": "Reissue with the corrected_input value",
    "phase": "validation",
    "corrected_input": "{\"key\": \"value\"}",
    "suggestion": "Use the corrected_input value to retry"
  },
  "warnings": [],
  "meta": { "duration_ms": 3 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework substitutes its forgiving JSON parser for all flags declared `type: json`.

```
# Trailing comma — accepted
$ mytool deploy --config '{"env": "prod",}' --json
{ "ok": true, "data": { ... }, ... }

# Block comment — accepted
$ mytool deploy --config '{"env": /* staging */ "prod"}' --json
{ "ok": true, "data": { ... }, ... }

# Unrecoverable syntax — corrected_input provided
$ mytool deploy --config '{env prod}' --json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_JSON",
    "message": "Input could not be normalized to valid JSON",
    "corrected_input": "{\"env\": \"prod\"}",
    "retryable": false,
    "fix_required": "Reissue with the corrected_input value",
    "phase": "validation"
  },
  ...
}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` shape used to return the `INVALID_JSON` error |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: `ARG_ERROR (2)` exit code guarantees zero side effects for parse failures |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Composes: JSON normalization runs during the validation phase, before execution |
| [REQ-F-045](f-045-agent-hallucination-input-pattern-rejection.md) | F | Composes: hallucination pattern rejection applies after JSON normalization succeeds |
