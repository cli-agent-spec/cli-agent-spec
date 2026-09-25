# REQ-C-027: Commands Declare Option Placement Convention

**Tier:** Command Contract | **Priority:** P1

**Source:** [§69 Argument Order Ambiguity](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Commands that cannot support interspersed option parsing (typically because they forward trailing arguments verbatim to a subprocess) MUST declare `option_placement: "strict"` in their manifest registration. Commands that support interspersed parsing (the default per REQ-F-067) declare `option_placement: "any"` or omit the field. This allows agents to construct invocations correctly without probing.

`strict` has one meaning: every option, global or local, precedes the first positional argument. Options may follow the command path; they need not precede it. Parsing stops at the first positional or at `--`, whichever comes first, and every later token reaches the child process unparsed. An option the agent places after that point is not an error; it is forwarded to the child, which is why the declaration is required rather than discovered.

The declaration is consumed by `tool manifest` (REQ-O-041) and `--schema` (REQ-O-013).

## Acceptance Criteria

- Commands forwarding args to a subprocess declare `option_placement: "strict"` at registration
- `tool manifest` includes an `option_placement` field for every command
- Commands without the declaration default to `"any"` (interspersed accepted)
- Under `strict`, `tool run --format json ./script --child-flag` parses `--format` and forwards `--child-flag`; `tool run --format json -- ./script` treats `./script` as the first positional
- Under `strict`, an option placed after the first positional reaches the child process verbatim and is never also parsed by the tool

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) — `option_placement` is a string enum (`"any"` | `"strict"`) on `CommandEntry`; absent means `"any"`

## Wire Format

```bash
$ tool manifest --format json
```

```json
{
  "ok": true,
  "data": {
    "schema_version": "3.0",
    "framework_version": "2.1.0",
    "etag": "sha256:7c1e0b",
    "commands": {
      "run": {
        "description": "Run a target, forwarding trailing arguments verbatim to the target process",
        "danger_level": "mutating",
        "required_scopes": [],
        "option_placement": "strict",
        "flags": {},
        "exit_codes": { "0": { "name": "SUCCESS", "description": "Target process exited 0", "retryable": false, "side_effects": "complete" } }
      },
      "list": {
        "description": "List available targets",
        "danger_level": "safe",
        "required_scopes": [],
        "option_placement": "any",
        "flags": {},
        "exit_codes": { "0": { "name": "SUCCESS", "description": "Targets listed", "retryable": false, "side_effects": "none" } }
      }
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 9 }
}
```

## Example

```python
# Command author declares strict placement for a subprocess-forwarding command
@app.command(option_placement="strict")
def run(target: str, extra_args: list[str]):
    """Runs target, forwarding extra_args verbatim."""
    subprocess.run([target, *extra_args])

# Agent consults manifest before constructing the call:
# option_placement == "strict" → every option before the first positional
# tool --format json run ./my-script --child-flag   ✓
# tool run --format json ./my-script --child-flag   ✓ (same parse)
# tool run ./my-script --format json                ✗ (--format forwarded to the child)
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-067](f-067-interspersed-option-parsing.md) | F | Composes: this declaration is the exception to the interspersed default |
| [REQ-F-079](f-079-global-option-scope.md) | F | Extends: global options follow the same placement rule on a strict command |
| [REQ-C-019](c-019-subprocess-invoking-commands-declare-argument-sche.md) | C | Extends: subprocess-invoking commands also declare their argument schema |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: manifest is the primary consumer of this declaration |
| [REQ-O-013](o-013-schema-output-schema-flag.md) | O | Exposes: `--schema` output includes `option_placement` for the command |
