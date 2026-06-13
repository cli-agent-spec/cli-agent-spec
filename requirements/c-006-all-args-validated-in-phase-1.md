# REQ-C-006: All Args Validated in Phase 1

**Tier:** Command Contract | **Priority:** P0

**Source:** [§14 Argument Validation Before Side Effects](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Command authors MUST implement all argument and precondition validation within the command's `validate()` hook, not within `execute()`. The `validate()` hook MUST be free of side effects. Validation MUST check all arguments at once, collecting all errors before returning (not fail-fast on the first error). The framework enforces phase ordering (REQ-F-015) but depends on command authors correctly placing validation logic.

## Acceptance Criteria

- A command with multiple invalid arguments reports all validation errors in a single invocation
- A validation hook that attempts to write a file is caught by the framework's side-effect detector (if implemented) or flagged in code review by the framework's linting rules
- The validation phase completes in under 100ms for all commands (no network calls in validate())
- Validation errors reference the specific parameter name and value that failed

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Validation failures exit with code `2` (`ARG_ERROR`) and carry a structured `errors` array. Each entry identifies the failing parameter and reason.

```json
{
  "errors": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["param", "code", "message"],
      "properties": {
        "param":   { "type": "string", "description": "Flag or argument name that failed validation" },
        "code":    { "type": "string", "description": "Machine-readable validation error code" },
        "message": { "type": "string", "description": "Human-readable description of the validation failure" },
        "value":   { "description": "The invalid value that was supplied" }
      }
    },
    "description": "All validation errors collected in a single pass; present when phase is 'validation'"
  }
}
```

---

## Wire Format

```bash
$ tool deploy --env prod --version 1.2.3 --notify-slack "#invalid channel" --workers abc
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "ARG_ERROR",
    "message": "Argument validation failed; no side effects have occurred",
    "phase": "validation"
  },
  "warnings": [],
  "meta": {
    "errors": [
      { "param": "--notify-slack", "code": "INPUT_PARAM_INVALID", "message": "Channel name must start with #", "value": "#invalid channel" },
      { "param": "--workers",      "code": "INPUT_PARAM_INVALID", "message": "Expected integer, got 'abc'",    "value": "abc" }
    ],
    "duration_ms": 4
  }
}
```

Exit code: `2` (`ARG_ERROR`) — guaranteed no side effects.

---

## Example

A command implements validation in its `validate()` hook, collecting all errors before returning. The `execute()` hook is never called if validation fails.

```
register command "deploy":
  danger_level: mutating
  exit_codes:
    SUCCESS  (0): description: "Deployment completed",          retryable: false, side_effects: complete
    ARG_ERROR(2): description: "Argument validation failed",    retryable: true,  side_effects: none

  validate(args) → []error:
    errors = []
    if not valid_env(args.env):
      errors.append(param="--env", code="INPUT_PARAM_INVALID",
                    message="Unknown environment '{}'".format(args.env))
    if not valid_slack_channel(args.notify_slack):
      errors.append(param="--notify-slack", code="INPUT_PARAM_INVALID",
                    message="Channel must start with #")
    return errors   # all errors collected before returning; execute() not called

  execute(args):
    # only reached when validate() returns no errors
    deploy(args.env, args.version)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: framework guarantees `validate()` completes before `execute()` runs |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Provides: `ARG_ERROR (2)` exit code carries the zero-side-effects guarantee |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `ARG_ERROR (2)` must be declared in the command's `exit_codes` map |
| [REQ-O-009](o-009-validate-only-flag.md) | O | Extends: `--validate-only` runs the `validate()` hook in isolation without proceeding to `execute()` |
