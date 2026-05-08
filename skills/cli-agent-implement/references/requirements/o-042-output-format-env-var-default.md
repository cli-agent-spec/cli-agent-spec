# REQ-O-042: Output Format Environment Variable Default

**Tier:** Opt-In | **Priority:** P2

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MAY honor a tool-scoped environment variable named `<TOOLNAME>_OUTPUT` as the default value for `--output` when the flag is not passed explicitly. The environment variable name MUST be derived from the executable name in uppercase with non-alphanumeric characters converted to underscores, for example `TOOL_OUTPUT` or `MY_TOOL_OUTPUT`. The framework MUST NOT read a generic variable such as `_OUTPUT` or `OUTPUT`.

If both `--output` and `<TOOLNAME>_OUTPUT` are present, `--output` MUST take precedence. If neither is present, the framework applies its normal auto-detection behavior from REQ-F-003 and the TTY default behavior from REQ-O-001. Unsupported values in `<TOOLNAME>_OUTPUT` MUST fail exactly as an unsupported `--output` value would fail.

## Acceptance Criteria

- `TOOL_OUTPUT=table tool list` produces the same output as `tool list --output table`
- `TOOL_OUTPUT=table tool list --output json` produces JSON because the explicit flag wins
- `_OUTPUT=table tool list` has no effect on output format selection
- `TOOL_OUTPUT=bogus tool list` fails with the same validation error shape and exit code as `tool list --output bogus`
- Help and configuration discovery surfaces the exact env var name that the tool honors

---

## Schema

No dedicated schema type — this requirement defines process-level default selection and precedence without adding new wire-format fields

---

## Wire Format

```bash
$ TOOL_OUTPUT=table tool list
```

Human-readable table output is selected as if `--output table` had been passed explicitly.

```bash
$ TOOL_OUTPUT=table tool list --output json
```

```json
{
  "ok": true,
  "data": [{ "id": "1", "name": "alice" }],
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 12 }
}
```

---

## Example

Opt-in at the framework level; the framework derives the env var name from the executable name and applies it only when `--output` is absent.

```
app = Framework("tool")
app.enable_output_flag(formats=["json", "jsonl", "tsv", "plain", "table"])
app.enable_output_env_default()

# Process-wide default for a shell session:
export TOOL_OUTPUT=table
$ tool list
# → same as: tool list --output table

# Explicit invocation still wins:
$ tool list --output json
# → JSON envelope on stdout
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-001](o-001-output-format-flag.md) | O | Extends: `<TOOLNAME>_OUTPUT` provides a process-level default for the canonical `--output` flag |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: auto-JSON still applies only when neither flag nor env var selected a format |
| [REQ-O-016](o-016-no-config-flag.md) | O | Composes: `--no-config` still permits env var overrides including output-format defaults |
