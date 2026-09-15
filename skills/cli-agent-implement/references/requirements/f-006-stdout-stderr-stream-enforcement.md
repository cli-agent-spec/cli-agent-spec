# REQ-F-006: Stdout/Stderr Stream Enforcement

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§3 Stderr vs Stdout Discipline](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: High

---

## Description

The framework MUST provide separate output primitives: `output()` writes to stdout and `log()` / `progress()` / `warn()` write to stderr. The framework MUST route all internal framework messages (progress, debug, timing) to stderr. Command authors MUST NOT be able to accidentally write prose to stdout using the framework's API. Any unhandled exception caught by the framework MUST be serialized to stderr, not stdout.

## Acceptance Criteria

- When a command is run with `1>/dev/null`, no data output is lost
- When a command is run with `2>/dev/null`, the structured result is still received on stdout
- Stack traces from uncaught exceptions appear only on stderr, never on stdout
- A command that calls only `log()` and `output()` produces valid JSON stdout with zero prose contamination

---

## Schema

No dedicated schema type — this requirement governs stream routing behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework provides distinct output primitives; routing is enforced at the API level.

```
# stdout — structured result only
{"ok":true,"data":{"imported":1500},"error":null,"warnings":[],"meta":{"duration_ms":820}}

# stderr — all diagnostic text
[INFO]  Connecting to database...
[INFO]  Processing batch 1/3...
[WARN]  Row 42 skipped: duplicate key
[INFO]  Done

# Command author API
output({"imported": 1500})   → stdout (JSON envelope)
log("Connecting...")         → stderr (plain text)
warn("Row 42 skipped: ...")  → stderr (plain text)
progress("batch 1/3")        → stderr (plain text)

# Unhandled exception — framework catches and routes to stderr
Traceback (most recent call last): ...  → stderr only, never stdout
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: stdout contains only JSON when non-TTY mode is active |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: `output()` emits a `ResponseEnvelope` to stdout |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Composes: ANSI suppression applies to both streams in JSON mode |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: structured error responses go to stdout, not stderr |
