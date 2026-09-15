# REQ-F-048: Help Output Routing to Stderr in Non-TTY Mode

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§3 Stderr vs Stdout Discipline](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: High

---

## Description

When stdout is not a TTY, the framework MUST redirect all `--help` output to stderr. In non-TTY mode, `--help` MUST additionally emit a minimal structured JSON object to stdout: `{"ok": true, "data": null, "meta": {"help": true, "schema_ref": "<command> --schema"}}`. This ensures that callers reading stdout always receive valid JSON, and agents that accidentally invoke `--help` get a machine-parseable redirect indicator rather than help text on stdout that breaks JSON parsing.

## Acceptance Criteria

- In non-TTY mode, `command --help` produces valid JSON on stdout
- In non-TTY mode, the help text itself appears only on stderr
- In TTY mode, `command --help` produces help text on stdout (unchanged from standard behavior)
- `json.loads(stdout_output)` succeeds on `--help` invocations in non-TTY mode

---

## Schema

No dedicated schema type — this requirement governs output stream routing without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework routes `--help` text to stderr and emits a minimal JSON indicator to stdout in non-TTY mode.

```
# Non-TTY mode
$ tool deploy --help 2>/dev/null
{"ok":true,"data":null,"meta":{"help":true,"schema_ref":"deploy --schema"}}

$ tool deploy --help 1>/dev/null
Usage: tool deploy [OPTIONS]
  Deploy the application to the target cluster.
  ...   (full help text on stderr)

# TTY mode — unchanged from standard behavior
$ tool deploy --help
Usage: tool deploy [OPTIONS]
  Deploy the application to the target cluster.
  ...   (help text on stdout as normal)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: the stdout JSON indicator follows the response envelope shape |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Composes: quiet mode and help routing are both applied at the same non-TTY detection point |
| [REQ-F-047](f-047-repl-mode-prohibition-in-non-tty-context.md) | F | Composes: REPL prohibition and help routing are both non-TTY hardening measures |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: `--schema` flag is the machine-readable complement to `--help` |
