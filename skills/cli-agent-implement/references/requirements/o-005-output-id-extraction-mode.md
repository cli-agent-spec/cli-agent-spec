# REQ-O-005: --output id Extraction Mode

**Tier:** Opt-In | **Priority:** P3

**Source:** [§6 Command Composition & Piping](../challenges/04-critical-output-and-parsing/06-medium-command-composition.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST support `--output id` as a format option on any command that returns a primary identifier. In this mode, stdout MUST contain only the bare identifier string (no JSON, no newline except the terminal one). Commands declare their primary identifier field; the framework extracts and emits it. This mode is designed for shell piping: `tool get-user --name Alice --output id | tool send-email --user-id -`.

## Acceptance Criteria

- `--output id` on a command that returns `{"data": {"id": 42}}` produces `42\n` on stdout
- The output is directly pipeable to another command's stdin
- No JSON structure, no whitespace beyond the terminal newline, is present in the output

---

## Schema

No dedicated schema type — this requirement governs stdout content format. The command's declared primary identifier field determines what is extracted; no new envelope fields are added.

---

## Wire Format

```bash
$ tool get-user --name alice --output id
```

```
u-4821
```

For list commands, one ID per line:

```bash
$ tool list-users --output id
```

```
u-4821
u-4822
u-4823
```

---

## Example

Commands declare their primary identifier field at registration time. The framework extracts and emits it.

```
app = Framework("tool")
app.enable_id_output_mode()

register command "get-user":
  primary_id_field: "id"

# tool get-user --name alice --output id  →  "u-4821\n"
# tool list-users --output id  →  one id per line
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-001](o-001-output-format-flag.md) | O | Extends: `id` is a value of the `--output` flag |
| [REQ-O-006](o-006-stdin-as-id-source.md) | O | Composes: `--output id` output is consumed by `-` stdin piping |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: id is extracted from the `data` field of the `ResponseEnvelope` |
