> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §69

## 69. Argument Order Ambiguity

**Source:** FP

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

An invocation has four kinds of token: global options (accepted by every command), the command path, command-local options, and positionals. Parsers disagree on where each may appear, and on which flags are global at all. Agents construct invocations in whatever order feels natural to the model, and the order varies across retries, prompt variations, and models. The result is outright rejection, silent misparsing, or a silently wrong value depending on the parser.

Four distinct failure modes exist:

**Mode 1: global option rejected after the command path.** argparse options defined on the root parser, Click group options, and Cobra non-persistent root flags are unknown to the subcommand:
```bash
$ tool --format json deploy staging   # works
$ tool deploy staging --format json   # fails: --format not registered on the subcommand
Error: unrecognized arguments: --format json
```

**Mode 2: local option rejected before the command path.** The mirror image, and what an agent gets when it "front-loads all flags" as a defensive habit:
```bash
$ tool list --limit 10                # works
$ tool --limit 10 list                # fails: --limit belongs to list, not to the root
Error: unrecognized arguments: --limit
```

**Mode 3: option silently treated as a positional.** A parser that stops option parsing at the first positional (Cobra with `SetInterspersed(false)`, getopt under `POSIXLY_CORRECT`, a Click command with `allow_interspersed_args=False`, an argparse `REMAINDER` positional) passes later options through as operands:
```bash
$ tool list items --format json
# "--format" and "json" become the second and third positional values
# no error; wrong result silently returned in plain text
```

**Mode 4: global option value silently overwritten or duplicated.** The option parses, but the value that takes effect is not the one the agent sent:
```bash
# argparse: global options copied onto each subparser with a real default;
# the subparser's default overwrites the root parser's value
$ tool --format json list             # exit 0, plain text

# the same option in two positions: most parsers keep the last one silently
$ tool --format json list --format text
```

Agents cannot predict which mode applies without probing. Modes 1 and 2 fail loudly but contradict each other, so neither "flags first" nor "flags last" is safe everywhere. Modes 3 and 4 exit `0`, which makes them the hardest to detect.

### Impact

- Silent misparse (Modes 3 and 4) returns an incorrect result with exit code `0`; nothing signals a retry
- Retry loops from inconsistent flag placement across invocations of the same command
- Fixing Mode 1 by front-loading every flag triggers Mode 2 for local flags, so the agent oscillates between two errors
- Agent must learn per-CLI ordering rules through trial and error, spending tokens and round trips
- A command-local flag that reuses a global option's name or short alias (`-f` for `--format` globally, `--force` locally) changes meaning with position

### Solutions

**Accept every option in any position after the command path, and global options anywhere:**

`tool --format json deploy staging`, `tool deploy --format json staging`, and `tool deploy staging --format json` are equivalent. Local options are accepted anywhere after the command path; they cannot precede it because the parser does not yet know which command they belong to.

**Register global options once, on every command, without default overwrite:**

```python
# argparse: parent parser with SUPPRESS defaults, applied to the root and every subparser
common = argparse.ArgumentParser(add_help=False)
common.add_argument("--format", choices=["json", "text"], default=argparse.SUPPRESS)
root = argparse.ArgumentParser(parents=[common])
sub = root.add_subparsers(dest="command", required=True)
sub.add_parser("list", parents=[common])
args = root.parse_args()
fmt = getattr(args, "format", "json")    # default applied once, after parsing
```

```go
// Cobra: persistent flags on the root are inherited by every subcommand;
// interspersed parsing is the default, so do not call SetInterspersed(false)
rootCmd.PersistentFlags().String("format", "json", "Output representation")
```

```python
# Click: group options are invisible to subcommands. Declare the option on the group and
# on every command with default=None, then resolve it once: a conflict is a usage error,
# otherwise the given value wins, then the real default
format_option = click.option("--format", type=click.Choice(["json", "text"]), default=None)

def resolve_format(ctx: click.Context, local: str | None) -> str:
    root = ctx.find_root().params["format"]
    if root and local and root != local:
        raise click.UsageError(f"--format given twice with different values: {root}, {local}")
    return local or root or "json"

@click.group()
@format_option
def cli(format): ...

@cli.command()
@format_option
@click.pass_context
def ls(ctx, format):
    fmt = resolve_format(ctx, format)
```

**Reject ambiguity instead of resolving it silently:**
- A command-local flag that reuses a global option's long name or short alias fails registration at startup
- A scalar option given more than once with different values exits `2`; repeating the same value is accepted
- `--` ends option parsing; every token after it is a positional, even one that starts with `-`

**For commands that forward trailing arguments verbatim, declare the constraint in the manifest:**

```json
{
  "option_placement": "strict"
}
```

Under `strict`, every option (global or local) precedes the first positional, and everything from the first positional on reaches the child process unparsed.

**Framework design:**
- Default parser configuration MUST accept options interspersed with positionals (REQ-F-067)
- Global options MUST be listed once in the manifest's root `flags` map, accepted on every command, and never shadowed by a local flag (REQ-F-079)
- A command that forwards trailing arguments MUST declare `option_placement: "strict"` (REQ-C-027)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | An option after a positional or a global option after the command path is silently misparsed (Mode 3), or a global option value set before the command path is silently replaced (Mode 4) |
| 1 | Misplaced options are rejected with a clear error and exit `2`; no interspersed support; no manifest declaration of the ordering rule |
| 2 | Interspersed options accepted for most commands; global options fail after some command paths, or global options are not distinguishable from local flags in the manifest |
| 3 | Global options accepted in every position on every command path and listed in the manifest root `flags`; local options accepted anywhere after the command path; conflicting repeats exit `2`; forwarding commands declare `option_placement: "strict"` |

**Check:**
1. `tool <cmd> <positional> --format json` and `tool --format json <cmd> <positional>` both succeed with identical output and exit code
2. `tool --format json <cmd>` emits JSON (catches the subparser default overwrite)
3. `tool <cmd> <positional> --<local-flag> <value>` takes effect (catches Mode 3)
4. `tool --format json <cmd> --format text` exits `2`

---

### Agent Workaround

**Signature:** `unrecognized arguments` or `unknown flag` naming a flag that exists in the manifest or `--help`; the same flag succeeds in another position; or `exit 0` with plain-text output despite `--format json`

**Tier:** B (one observable check, then one command)

**Classify each flag as global or local, then emit the canonical order:**

`tool <global options> <command path> <local options> [--] <positionals>`

Global options go before the command path, which every parser accepts. Local options go right after the command path and before any positional, which also satisfies `option_placement: "strict"`. A positional that starts with `-` goes after `--`.

```python
def build_argv(tool: str, manifest: dict, path: list[str], flags: dict[str, str | bool], positionals: list[str]) -> list[str]:
    """Order tokens so that every common parser mode accepts them; True is a bare switch, False omits it."""
    global_names = set(manifest.get("flags", {}))
    global_args: list[str] = []
    local_args: list[str] = []
    for name, value in flags.items():
        if value is False:
            continue
        tokens = [f"--{name}"] if value is True else [f"--{name}", value]
        (global_args if name in global_names else local_args).extend(tokens)
    separator = ["--"] if any(p.startswith("-") for p in positionals) else []
    return [tool, *global_args, *path, *local_args, *separator, *positionals]
```

Without a manifest root `flags` map, treat the output, verbosity, and color flags (`--format`, `--quiet`, `--verbose`, `--no-color`) as global and every other flag as local. Pass each option once.

**Limitation:** A CLI that supports neither `--` nor global options after the command path may reject parts of the canonical order, and without a manifest the global/local split is a guess; one failed call confirms which flags belong to the root
