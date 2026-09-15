# REQ-F-056: Terminal Width Wrapping Disabled in JSON Mode

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§63 Terminal Column Width Output Corruption](../challenges/01-critical-ecosystem-runtime-agent-specific/63-medium-column-width-corruption.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Medium

---

## Description

The framework MUST disable all terminal-width-based text wrapping when JSON output mode is active. The framework's JSON serializer MUST NOT inject newlines into string field values regardless of the value of `$COLUMNS`, `shutil.get_terminal_size()`, or `process.stdout.columns`. String values MUST be serialized as single-line JSON strings. When the `--width` flag is set to `0` (the default in non-TTY mode), all prose output on stderr is also unwrapped.

## Acceptance Criteria

- A 200-character URL in a JSON field is serialized as a single unbroken string, not split across lines
- `$COLUMNS=40` does not cause any JSON string value to contain a newline character
- `json.loads(stdout_output)` succeeds on all JSON mode output regardless of terminal width settings
- In TTY mode with `--width=80`, prose output on stderr wraps at 80 characters (unchanged behavior)

---

## Schema

No dedicated schema type — this requirement governs JSON serialization behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework sets `COLUMNS=0` and disables word-wrap when JSON output mode is active.

```
# $COLUMNS=40 set in environment — JSON mode active
$ mytool list-deployments --json
{"ok":true,"data":{"url":"https://example.com/very/long/path/that/exceeds/40/chars/and/would/have/been/wrapped"},"error":null,"warnings":[],"meta":{"duration_ms":12}}
→ single unbroken line; $COLUMNS ignored

# TTY mode — prose wraps normally
$ mytool list-deployments
Deployment completed successfully at
https://example.com/very/long/path
→ wrapped at terminal width
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Provides: JSON output mode activation that triggers wrapping suppression |
| [REQ-F-005](f-005-locale-invariant-serialization.md) | F | Composes: locale-invariant serialization ensures string values are also free of locale-injected whitespace |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: stderr prose wrapping is a separate concern; only stdout JSON serialization is governed here |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Composes: JSON mode suppresses both ANSI codes and line wrapping |
