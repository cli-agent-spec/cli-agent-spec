# REQ-F-067: Interspersed Option Parsing

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§69 Argument Order Ambiguity](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST configure its argument parser to accept options (flags) interspersed with positional arguments, known as interspersed or permissive option parsing. Command-local options are accepted anywhere after the command path; global options (REQ-F-079) are accepted anywhere, including before the command path. `tool cmd --flag value arg`, `tool cmd arg --flag value`, and, for a global option, `tool --flag value cmd arg` MUST all be treated as equivalent. This eliminates a class of agent retry failures caused by LLMs constructing flag-before-arg or flag-after-arg invocations inconsistently across calls.

Interspersed parsing needs two tie-breakers so that no position changes meaning silently:

- **`--` ends option parsing.** Every token after `--` is a positional, including one that starts with `-`. This is how an agent passes a value such as `-v1` or a negative number as a positional
- **Conflicting repeats are rejected.** A scalar option given more than once with different values exits `2` (`ARG_ERROR`) naming the option, instead of keeping the last value silently. Repeating the same value is accepted; `array` options accumulate

Commands that cannot support interspersed parsing because they forward trailing arguments verbatim to a subprocess MUST declare `option_placement: "strict"` via REQ-C-027 rather than silently misparsing.

## Acceptance Criteria

- `tool cmd positional --flag value` and `tool cmd --flag value positional` produce identical output and exit code
- Options appearing after positional arguments are never silently treated as positional values
- Global options (`--format`, `--quiet`, etc.) are accepted after the command path, including after positionals (REQ-F-079)
- `tool cmd -- -value` passes `-value` as a positional; no option parsing happens after `--`
- `tool --format json cmd --format text` exits `2` with `ARG_ERROR` naming `--format`; `tool --format json cmd --format json` succeeds
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
# argparse: options after positionals are accepted by default. Use
# parse_intermixed_args() only when an nargs="*" positional must also be split
# around options. It does not make root options visible to subparsers; that is
# REQ-F-079 (parent parsers with SUPPRESS defaults)
args = parser.parse_args()

# Click: commands intersperse by default; never set allow_interspersed_args=False
# on a command that is not forwarding arguments
@click.command()

# Commander.js: keep the default; enablePositionalOptions() restricts program
# options to before the subcommand, and passThroughOptions() stops option
# parsing at the first positional
program.command("deploy")

# Cobra (Go): interspersed is the default; never call cmd.Flags().SetInterspersed(false)
```

The conflicting-repeat check runs after parsing, because most parsers keep the last value:

```python
def reject_conflicting_repeats(argv: list[str], scalar_flags: set[str]) -> None:
    # expects argv normalized to "--name value" (no "--name=value", no short aliases)
    seen: dict[str, str] = {}
    tokens = argv[: argv.index("--")] if "--" in argv else argv
    for flag, value in zip(tokens, tokens[1:]):
        if flag.startswith("--") and flag[2:] in scalar_flags:
            if seen.setdefault(flag, value) != value:
                raise UsageError(f"{flag} given twice with different values: {seen[flag]!r}, {value!r}")
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-027](c-027-commands-declare-option-placement.md) | C | Composes: commands that cannot support interspersed parsing declare the constraint here |
| [REQ-F-079](f-079-global-option-scope.md) | F | Composes: global options resolve to the same value in every position |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Extends: option placement is part of the command's declared input schema |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: manifest includes `option_placement` field per command |
