# REQ-O-025: --warnings-as-errors Flag

**Tier:** Opt-In | **Priority:** P3

**Source:** [§3 Stderr vs Stdout Discipline](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: High

---

## Description

The framework MUST provide `--warnings-as-errors` as a standard flag. When passed, any warning emitted via the framework's `warn()` API causes the command to exit non-zero (exit code `1`) after completing, and the `warnings` array in the JSON response MUST be non-empty. This is useful for strict automated pipelines that must not silently continue past deprecated usage or unexpected conditions.

## Acceptance Criteria

- A command that emits no warnings exits `0` even with `--warnings-as-errors`
- A command that emits one warning exits `1` when `--warnings-as-errors` is passed
- The `warnings` array in the response contains the warning that triggered the exit
- Without `--warnings-as-errors`, warnings are emitted but do not affect exit code

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When `--warnings-as-errors` is active and a warning is emitted, the command exits `1` and the `warnings` array in the response is non-empty. The existing `warnings` field of the envelope is the sole carrier; no new schema fields are added.

---

## Wire Format

Without warnings (exits `0` even with the flag):

```bash
$ tool build --warnings-as-errors
```

```json
{
  "ok": true,
  "data": { "artifact": "build/output.zip" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 120 }
}
```

With a warning (exits `1` when flag is active):

```bash
$ tool build --warnings-as-errors
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "WARNINGS_AS_ERRORS",
    "message": "Command produced warnings; treated as errors due to --warnings-as-errors"
  },
  "warnings": [{ "code": "DEPRECATED_FLAG", "message": "Deprecated flag --old-format used; switch to --format json", "context": { "flag": "--old-format", "replacement": "--format json" } }],
  "meta": { "exit_code": 1, "duration_ms": 118 }
}
```

---

## Example

The `--warnings-as-errors` flag is registered globally once at startup; it works with every command without per-command declaration:

```
app = Framework("tool")
app.enable_warnings_as_errors_flag()

# Every command now accepts --warnings-as-errors
# tool build --warnings-as-errors → exits 1 if any warn() call fires
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `warnings` array in the envelope that this flag elevates to errors |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Enforces: warnings are captured to the JSON envelope, not emitted to stderr |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: the warning-as-error uses the standard structured error shape |
