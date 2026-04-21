# REQ-F-047: REPL Mode Prohibition in Non-TTY Context

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§37 REPL / Interactive Mode Accidental Triggering](../challenges/01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

When stdin is not a TTY, the framework MUST detect and prevent entry into any interactive REPL, shell, or prompt loop. The framework MUST intercept: commands invoked with no subcommand (if the default behavior would enter an interactive shell), `input()` / `readline()` calls that would block on stdin, and any prompt library invocation. If a would-be-blocking interactive call is detected at runtime in non-TTY mode, the framework MUST immediately exit with code 4 and a structured error: `{"ok": false, "error": {"code": "INTERACTIVE_BLOCKED", "message": "Command requires interactive input but stdin is not a TTY."}}`.

If a CLI chooses to render root help on empty invocation instead of entering a REPL, that empty-invocation path is allowed in non-TTY mode provided it returns immediately and does not prompt, block, or perform side effects.

## Acceptance Criteria

- A command that calls `input()` in non-TTY mode exits with code 4 and structured JSON error, not a hang
- A CLI invoked with no arguments that would drop into REPL mode exits with code 4 in non-TTY mode
- A CLI invoked with no arguments that renders root help in non-TTY mode returns immediately without prompt, block, or side effects
- In TTY mode, interactive prompts are unaffected
- The error message includes specific guidance on which flag to pass to run non-interactively

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When REPL entry is blocked, the framework emits a structured error with `code: "REPL_MODE_PROHIBITED"` before the process would have blocked.

---

## Wire Format

`tool` (no subcommand, non-TTY) → error response (exit 4):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "REPL_MODE_PROHIBITED",
    "message": "Command requires interactive input but stdin is not a TTY",
    "hint": "Pass a subcommand explicitly, e.g. `tool help` to list available commands"
  },
  "warnings": [],
  "meta": {}
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework intercepts would-be-blocking interactive calls in non-TTY mode and exits with code 4.

```
# Non-TTY invocation with no subcommand — would drop into REPL
$ echo "" | tool
→ exit 4: REPL_MODE_PROHIBITED
{"ok":false,"error":{"code":"REPL_MODE_PROHIBITED","message":"Command requires interactive input but stdin is not a TTY","hint":"Pass a subcommand explicitly"}}

# Command that calls input() in non-TTY mode
$ tool prompt --message "Enter name:"
→ exit 4: REPL_MODE_PROHIBITED (intercepted before readline blocks)

# TTY mode — unaffected
$ tool   # in terminal
→ enters interactive REPL as normal
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-046](f-046-pager-environment-variable-suppression.md) | F | Composes: pager suppression is part of the same non-TTY hardening |
| [REQ-F-068](f-068-help-and-version-flag-purity.md) | F | Composes: empty-invocation help follows the same side-effect-free dispatch guarantees as `--help` |
| [REQ-F-055](f-055-editor-and-visual-no-op-in-non-tty-mode.md) | F | Composes: editor trap suppression addresses the same class of interactive-block failure |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `PRECONDITION (4)` is the exit code for blocked interactive mode |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: blocked REPL is reported as a structured JSON error response |
