# REQ-O-009: --validate-only Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§14 Argument Validation Before Side Effects](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide `--validate-only` as a standard flag on every command. When passed, the framework runs Phase 1 (validation) and reports results, then exits without running Phase 2 (execution). Exit `0` means all validation passed and the command would succeed. Exit `2` means validation errors were found, listed in the JSON error response. This flag MUST be registered automatically by the framework; command authors do not implement it.

## Acceptance Criteria

- `--validate-only` with valid args exits `0` with a JSON response indicating validation passed
- `--validate-only` with invalid args exits `2` with all validation errors listed
- `--validate-only` never causes any side effects, even when called with perfectly valid args
- The `--validate-only` flag is present in every command's `--help` output

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When `--validate-only` is passed, the response includes `meta.validation_only: true` and exits `0` on success or `3` on validation failure. No side effects occur.

---

## Wire Format

```bash
$ tool deploy --target staging --validate-only --output json
```

```json
{
  "ok": true,
  "data": null,
  "error": null,
  "warnings": [],
  "meta": { "validation_only": true, "duration_ms": 4 }
}
```

Validation failure:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "ARG_ERROR",
    "message": "Validation failed",
    "errors": [{ "field": "target", "message": "Unknown environment 'invalid'" }]
  },
  "warnings": [],
  "meta": { "validation_only": true, "phase": "validation" }
}
```

---

## Example

Opt-in at the framework level; automatically available on every command.

```
app = Framework("tool")
app.enable_validate_only()   # registers --validate-only on all commands

# Use before destructive operations to confirm args are valid:
$ tool delete --resource-id acme-prod --validate-only
→ ok: true, meta.validation_only: true  # safe to proceed
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: `ARG_ERROR (2)` guarantees zero side effects in validation-only mode |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Provides: the validate-before-execute phase boundary this flag stops at |
| [REQ-C-006](c-006-all-args-validated-in-phase-1.md) | C | Consumes: all declared validations run during `--validate-only` |
| [REQ-O-013](o-013-schema-output-schema-flag.md) | O | Composes: `--schema` reveals what validations `--validate-only` will exercise |
