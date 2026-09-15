# REQ-F-009: Non-Interactive Mode Auto-Detection

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST automatically detect non-interactive execution by checking whether stdin is a TTY (`isatty(stdin)`). When stdin is not a TTY, the framework MUST globally disable all interactive prompts and treat the session as `--non-interactive`. Commands MUST NOT block waiting for stdin input in non-interactive mode; instead, they MUST fail immediately with a structured error (exit code 4) if required input is unavailable.

## Acceptance Criteria

- A command that would prompt for input in TTY mode exits immediately with exit code 4 and a JSON error when stdin is `/dev/null`
- No command hangs waiting for stdin input when `isatty(stdin) == false`
- The JSON error for this condition includes `"code": "INPUT_REQUIRED"` and a `suggestion` field

---

## Schema

No dedicated schema type — this requirement governs TTY detection and prompt suppression without adding new wire-format fields. Failures use the standard `ResponseEnvelope` with `ErrorDetail.code = "INPUT_REQUIRED"`.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework checks `isatty(stdin)` at startup and globally disables interactive prompts.

```
# Non-interactive context: stdin is /dev/null or a pipe
$ echo "" | tool deploy --target prod

# Command would normally prompt: "Confirm? [y/N]"
# Framework detects non-TTY stdin → skips prompt → exits immediately
exit 4, stdout:
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INPUT_REQUIRED",
    "message": "Confirmation required but stdin is not interactive",
    "retryable": true,
    "phase": "validation",
    "suggestion": "Pass --yes to confirm non-interactively"
  },
  "warnings": [],
  "meta": { "duration_ms": 2 }
}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: non-TTY stdout also triggers JSON mode; both checks happen at startup |
| [REQ-F-010](f-010-pager-suppression.md) | F | Composes: pager suppression addresses a parallel class of blocking behavior |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: error response uses the standard `ResponseEnvelope` |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: `INPUT_REQUIRED` error follows the structured error response contract |
