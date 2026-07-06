> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §69

## 69. Argument Order Ambiguity

**Source:** FP

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

CLI parsers differ on whether options (flags) may appear after positional arguments or subcommands. Agents construct invocations in whatever order feels natural to the LLM — and the order varies across retries, prompt variations, and models. The result is silent misparsing or outright rejection depending on which parser mode the framework uses.

Three distinct failure modes exist:

**Mode 1 — Option rejected after positional arg (POSIX strict mode):**
```bash
$ tool deploy staging --output json
# argparse default: "staging" consumed as positional, "--output" rejected as unrecognised
Error: unrecognised arguments: --output json
```

**Mode 2 — Option silently treated as positional value:**
```bash
$ tool list --limit 10 --output json
# some parsers: "--output" becomes the second positional arg value
# no error; wrong result silently returned in plain text
```

**Mode 3 — Global option not accepted after subcommand:**
```bash
$ tool --output json deploy staging   # works
$ tool deploy staging --output json   # fails: --output not registered on subcommand
Error: unknown flag: --output
```

Agents cannot reliably predict which mode applies without probing, and the errors are inconsistent — Mode 2 fails silently, making it the hardest to detect.

### Impact

- Silent misparse (Mode 2) causes incorrect results with exit code 0 — no retry signal
- Retry loops from inconsistent flag placement across invocations of the same command
- Agent must learn per-CLI ordering rules through trial and error, spending tokens and round trips
- Global flags (e.g., `--output`, `--timeout`) registered at root level silently ignored when placed after subcommand

### Solutions

**Enforce interspersed option parsing at the framework level:**

Options are accepted in any position relative to subcommands and positional arguments. `tool cmd --flag arg`, `tool --flag cmd arg`, and `tool cmd arg --flag` are all equivalent.

```python
# argparse
parser = argparse.ArgumentParser()
parser.parse_intermixed_args()  # allows interspersed options

# Click
@click.command(context_settings={"allow_interspersed_args": True})

# Commander.js
program.enablePositionalOptions(false)  # disable strict positional ordering
```

**For global flags that must precede subcommands, declare this constraint in the manifest:**

```json
{
  "option_placement": "strict",
  "note": "Global options must appear before the subcommand"
}
```

**Framework design:**
- Default parser configuration MUST use interspersed/permissive option parsing
- If a command passes remaining args verbatim to a subprocess (e.g., a wrapper), it MUST declare `option_placement: "strict"` in its manifest so agents know to front-load flags
- The manifest's `--schema` output MUST include the effective `option_placement` value

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Options after positional args silently misparsed or rejected; no manifest declaration of ordering constraint |
| 1 | Consistent rejection with a clear error message; no interspersed support; no manifest declaration |
| 2 | Interspersed options accepted for most commands; global flags may still fail after subcommand |
| 3 | Full interspersed option parsing enforced framework-wide; exceptions declared in manifest with `option_placement: "strict"` |

**Check:** Invoke `tool subcommand positional-arg --global-flag value` and `tool --global-flag value subcommand positional-arg` — both must succeed with identical output.

---

### Agent Workaround

**Signature:** `unrecognised arguments` or `unknown flag` when a flag follows a positional; same invocation with the flag front-loaded succeeds; or `exit 0` with plain-text output

**Tier:** A (one safe command, no branching)

**Front-load all flags before positional arguments and subcommands:**

```python
def normalize_arg_order(flags: dict, subcommand: list[str], positionals: list[str]) -> list[str]:
    """Place all flags first to avoid parser mode ambiguity."""
    flag_args = []
    for k, v in flags.items():
        flag_args.extend([f"--{k}", str(v)])
    return flag_args + subcommand + positionals
```

**Limitation:** Front-loading flags fails for commands that pass trailing args verbatim to a subprocess (e.g., `tool run -- --child-flag`), and does not help when global flags are not registered on subcommands — check `--schema` for `option_placement` before constructing the invocation
