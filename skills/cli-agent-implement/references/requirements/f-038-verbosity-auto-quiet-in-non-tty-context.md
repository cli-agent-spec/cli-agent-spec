# REQ-F-038: Verbosity Auto-Quiet in Non-TTY Context

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Low / Context: High

---

## Description

When stdout is not a TTY or when `CI` is set, the framework MUST automatically suppress all non-essential prose from stderr (equivalent to `--quiet`). Only the structured JSON output on stdout and explicit errors on stderr MUST remain. Command authors MUST NOT need to check TTY state themselves; the framework's `log()` and `progress()` primitives respect this mode automatically.

## Acceptance Criteria

- In a non-TTY context, `progress()` calls produce no output
- In a non-TTY context, `log()` calls at level INFO and below produce no stderr output
- Error-level `log()` calls are always emitted regardless of TTY state
- Explicitly passing `--verbose` overrides auto-quiet mode

---

## Schema

No dedicated schema type — this requirement governs the framework's output primitives without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework checks `isatty(stdout)` and the `CI` environment variable at startup. In non-TTY or CI contexts, the `progress()` and `log()` primitives are silenced automatically.

```
$ tool build --target all | cat   (stdout is a pipe → non-TTY)
→ no progress bars on stderr
→ no INFO-level log lines on stderr
→ only the JSON response on stdout
→ ERROR-level log lines still appear on stderr

$ CI=true tool build --target all
→ same suppression as non-TTY mode

$ tool build --target all   (interactive terminal)
→ progress bars and INFO logs appear normally on stderr

$ tool build --target all --verbose | cat
→ --verbose overrides auto-quiet; INFO logs are restored
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-interactive mode detection reused to trigger auto-quiet |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: this requirement governs what is emitted on stderr in non-TTY mode |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Composes: ANSI color suppression also activates in non-TTY contexts |
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Composes: auto-update suppression applies the same non-TTY detection |
