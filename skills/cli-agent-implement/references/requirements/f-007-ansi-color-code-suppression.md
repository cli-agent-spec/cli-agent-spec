# REQ-F-007: ANSI/Color Code Suppression

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§8 ANSI & Color Code Leakage](../challenges/04-critical-output-and-parsing/08-high-ansi-leakage.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Medium

---

## Description

The framework MUST strip all ANSI escape sequences from every string value before JSON serialization, unconditionally in JSON output mode. The strip operation MUST cover: SGR color/style codes (`\x1b[...m`), cursor movement sequences, OSC sequences, and carriage return characters. This stripping MUST apply to all string fields including error messages and values derived from third-party libraries.

## Acceptance Criteria

- No byte in the range `\x1b` appears in the JSON output when in JSON mode
- A string value that was injected with color codes by a third-party dependency is clean in the JSON output
- JSON output passes `jq '.'` without error even when the process was invoked with a TTY

---

## Schema

No dedicated schema type — this requirement governs string sanitization behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework applies ANSI stripping to all string values during JSON serialization, including values produced by third-party libraries.

```
# Third-party library returns a colorized string
raw_value = "\x1b[31mError: file not found\x1b[0m"

# Framework strips ANSI before serialization
serialized = "Error: file not found"

# stdout contains clean JSON
{"ok":false,"data":null,"error":{"code":"NOT_FOUND","message":"Error: file not found"},...}

# Verify: no ESC byte in output
$ tool list --output json | cat -v | grep -c '\^['
0
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: suppression is active whenever JSON mode is active |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Composes: `NO_COLOR` detection prevents ANSI injection at the source |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: stream routing ensures stripped output reaches the correct file descriptor |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: all `ResponseEnvelope` string fields are subject to ANSI stripping |
