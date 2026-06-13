# REQ-F-002: Exit Code 2 Reserved for Validation Failures

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§1 Exit Codes & Status Signaling](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) · [§14 Argument Validation Before Side Effects](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Low

---

## Description

The framework MUST ensure that exit code `2` is emitted if and only if command execution was aborted during input validation, before any side effect occurred. The framework MUST guarantee this by enforcing the validate-before-execute phase boundary (see REQ-F-015). A command that exits `2` MUST be safe to retry without any cleanup or rollback.

## Acceptance Criteria

- A command that exits `2` has provably caused zero filesystem, network, or state mutations.
- No command in the framework exits `2` after any side effect has been initiated.
- The JSON error response for exit `2` MUST include `"phase": "validation"`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`exit-code.md`](../schemas/exit-code.md)

The `ErrorDetail.phase` field carries `"validation"` to guarantee the agent that no side effect occurred and the command is safe to retry after correcting the input.

---

## Wire Format

JSON error response for a command that exits `2` (`ARG_ERROR`) — `phase` field confirms validation-only failure:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "Flag --count must be a positive integer",
    "retryable": true,
    "phase": "validation",
    "suggestion": "Provide a value greater than 0"
  },
  "warnings": [],
  "meta": { "duration_ms": 3 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework enforces the validate-before-execute phase boundary and sets `phase: "validation"` automatically whenever validation fails before execution begins.

```
# Command receives --count foo (invalid integer)
# Framework phase: VALIDATION
# No I/O or state mutation has occurred
→ exit 2, error.phase = "validation", error.retryable = true

# Command receives --count 5 (valid), begins writing to database
# Framework phase: EXECUTION
# A partial failure here cannot use ARG_ERROR
→ exit 3 (PARTIAL_FAILURE), error.phase = "execution"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Specializes: enforces reserved semantics for `ARG_ERROR (2)` — zero side effects guarantee |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: phase boundary that makes the `ARG_ERROR` guarantee enforceable |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Consumes: `ARG_ERROR` must appear in every command's declared exit code map |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: error response carries `phase` field alongside `code` and `message` |
