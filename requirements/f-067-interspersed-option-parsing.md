# REQ-F-067: Interspersed Option Parsing

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§69 Argument Order Ambiguity](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST configure its argument parser to accept options (flags) in any position relative to subcommands and positional arguments — known as interspersed or permissive option parsing. `tool cmd --flag value`, `tool --flag value cmd`, and `tool cmd positional --flag value` MUST all be treated as equivalent. This eliminates a class of agent retry failures caused by LLMs constructing flag-before-arg or flag-after-arg invocations inconsistently across calls.

The requirement applies to all options registered at the framework level (e.g., `--format`, `--timeout`, `--quiet`). Commands that cannot support interspersed parsing because they forward trailing arguments verbatim to a subprocess MUST declare `option_placement: "strict"` via REQ-C-027 rather than silently misparsing.

## Acceptance Criteria

- `tool cmd positional --flag value` and `tool --flag value cmd positional` produce identical output and exit code
- Options appearing after positional arguments are not silently treated as positional values
- Framework-level flags (`--format`, `--timeout`, etc.) are accepted after a subcommand name
- A command that cannot support interspersed parsing declares `option_placement: "strict"` in its manifest (see REQ-C-027) rather than rejecting or misparsing silently

## Schema

No dedicated schema type. The `option_placement` field is part of the command manifest produced by `tool manifest` (REQ-O-041).

## Wire Format

Both invocations must produce the same result:

```bash
$ tool list --limit 5 --format json items
$ tool list items --format json --limit 5
```

```json
{
  "ok": true,
  "data": [{ "id": "item-1" }, { "id": "item-2" }],
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 14, "pagination": { "total": 2, "returned": 2, "truncated": false, "has_more": false, "next_cursor": null } }
}
```

## Example

```python
# argparse — use parse_intermixed_args() instead of parse_args()
args = parser.parse_intermixed_args()

# Click — set context setting
@click.command(context_settings={"allow_interspersed_args": True})

# Commander.js — disable strict positional ordering
program.enablePositionalOptions(false)

# Cobra (Go) — interspersed is the default; no action needed
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-027](c-027-commands-declare-option-placement.md) | C | Composes: commands that cannot support interspersed parsing declare the constraint here |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Extends: option placement is part of the command's declared input schema |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: manifest includes `option_placement` field per command |
