# Guide: The No-Args Entry Point

> **The principle:** A multi-command CLI must exit 0 and show its root help when invoked with no arguments. This is the agent's first-contact probe — every agent-compatibility feature is unreachable if the entry point fails.

Agents do not start with `--help`. They run the bare binary first. It is cheaper, faster, and tells them whether the tool is accessible before committing tokens to per-command discovery. A non-zero exit on that probe short-circuits the entire session. The agent logs a failure, may retry, and may give up — never reaching the `--schema` flag, the JSON output mode, or the structured error codes that the CLI author built.


---

## The Discovery Gap

A CLI can invest in advanced agent features and still be unreachable. The bare-invocation probe is the first thing an agent runs — if it fails, nothing else matters:

```
$ poly
usage: poly [-h] [--schema] [--output FORMAT] [--json] [-v] COMMAND ...
poly: error: the following arguments are required: COMMAND
exit code: 2
```

`poly` has `--schema`, `--output FORMAT`, and `--json` — none of it reachable. Contrast with:

```
$ polymarket
Polymarket CLI

Usage: polymarket [OPTIONS] <COMMAND>

Commands:
  markets  Interact with markets
  events   Interact with events
  clob     Interact with the CLOB
  wallet   Manage wallet and authentication
  ...

Options:
  -o, --output <OUTPUT>  [default: table] [possible values: table, json]
  -h, --help
```

`polymarket` has no `--schema` flag. Agents can still discover and use it because the entry point works.

Discovery layers are orthogonal. Both dimensions matter. The entry point is the prerequisite.

---

## The Two argparse Anti-Patterns

`add_subparsers()` defaults to `required=False`. On bare invocation, argparse returns silently with no output — the caller receives `Namespace(command=None)` and no error. This is itself a failure for agents, who expect a command list on stdout.

**Anti-pattern 1 — default: returns silently with no output**

```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")  # required=False by default
args = parser.parse_args()
# bare invocation: parse_args() returns Namespace(command=None), prints nothing
# calling args.func(args) here raises AttributeError — no set_defaults handler exists
```

Argparse prints nothing and returns to the caller. The agent receives no command list, no usage. If the dispatch code then calls `args.func(args)` without a registered default, the program crashes with `AttributeError`. Either way, discovery fails — silently or noisily, depending on the dispatch code, which is harder to diagnose than an explicit error.

**Anti-pattern 2 — explicit `required=True`: exits 2**

```python
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command", required=True)
# bare invocation → exit 2, "the following arguments are required: command"
# (lowercase — argparse uses the dest value in the error message)
```

A deliberate choice to force users to provide a subcommand. Reasonable for human callers; fatal for agents. The non-zero exit causes the agent to classify the tool as broken before discovering a single command.

Both break the entry-point contract. The fix addresses both.

---

## The Fix for CLI Authors

### argparse

Both changes are required. `required=False` alone silently does nothing.

```python
import sys, argparse

parser = argparse.ArgumentParser(description="my-tool — brief description")
subparsers = parser.add_subparsers(dest="command", required=False)

# register subcommands here

def _root(args):
    parser.print_help()
    sys.exit(0)

parser.set_defaults(func=_root)

args = parser.parse_args()
args.func(args)
```

### Click

Click's `invoke_without_command=True` provides this correctly:

```python
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        # exit 0 is implicit
```

### clap (Rust)

clap's `arg_required_else_help = true` on the top-level command produces exit 0 with help when no subcommand is given:

```rust
#[derive(Parser)]
#[command(arg_required_else_help = true)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}
```

### Cobra (Go)

Cobra calls the root command's `Run` or `RunE` when no subcommand is given. Set it to print help:

```go
var rootCmd = &cobra.Command{
    Use:   "my-tool",
    Short: "Brief description",
    Run: func(cmd *cobra.Command, args []string) {
        cmd.Help()
    },
}
```

---

## Verification Checklist for CLI Authors

Three checks that must all pass before a CLI is considered agent-accessible:

| Check | Command | Expected result |
|-------|---------|-----------------|
| Bare invocation | `your-tool` | Exit 0, subcommand list on stdout |
| Clean environment | `HOME=/tmp/empty your-tool` | Exit 0, no files created, no network calls |
| Non-TTY pipe | `your-tool \| cat` | Help text still appears on stdout |

The clean environment check is not optional — REQ-F-068 requires that the empty-invocation path follows the same purity guarantees as `--help`. No config directory creation, no schema migration, no credential check.

---

## For Agent Builders

Agents cannot control whether the CLIs they use follow this spec. The defensive first-contact probe handles both the clean case and the error case:

```python
import subprocess, re

def probe_cli(tool: str) -> dict:
    # Attempt 1 — bare invocation
    result = subprocess.run(
        [tool],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,  # never inherit agent stdin (§50)
        timeout=10,
    )

    if result.returncode == 0 and result.stdout.strip():
        commands = re.findall(r'^\s{2,4}(\w[\w-]*)\s', result.stdout, re.MULTILINE)
        return {"ok": True, "commands": commands, "source": "bare"}

    # Attempt 2 — explicit --help flag
    fallback = subprocess.run(
        [tool, "--help"],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
    if fallback.returncode == 0:
        commands = re.findall(r'^\s{2,4}(\w[\w-]*)\s', fallback.stdout, re.MULTILINE)
        return {"ok": True, "commands": commands, "source": "help_flag"}

    return {"ok": False, "commands": [], "source": "none"}
```

`stdin=subprocess.DEVNULL` must be set on every invocation — not just the probe. Without it, the subprocess inherits the agent's own stdin. Any tool that silently falls back to stdin (§50) will consume it, corrupting the agent's input stream.

**Limitation:** The `--help` fallback is not guaranteed. Some tools run credential or config checks before argument parsing and exit non-zero even on `--help`. If both probes fail, classify the tool as "unknown interface" and surface the failure to the caller rather than proceeding with guessed invocations.

---

## For AI Agents

Use this decision table when encountering an unfamiliar CLI:

| Step | Command | Exit 0 + output? | Next step |
|------|---------|-----------------|-----------|
| 1 | `<tool>` | Yes | Parse subcommand list; try `--schema` |
| 1 | `<tool>` | No | Try step 2 |
| 2 | `<tool> --help` | Yes | Parse subcommand list; try `--schema` |
| 2 | `<tool> --help` | No | Tool is not usable; stop |
| 3 | `<tool> --schema --output json` | Yes, valid JSON | Use as authoritative schema |
| 3 | `<tool> --schema --output json` | No | Fall back to per-command `--help` |

Additional signals to watch for:

- Exit 0 with no output on bare invocation: go directly to `--help`
- A `shell` or `repl` entry in the subcommand list: REPL risk (§37) — never invoke these subcommands without a TTY
- Non-zero exit on `--help`: tool runs initialization before argument parsing — treat as partially broken; try per-command `<tool> <command> --help` directly

---

## Related

| Document | Relationship |
|----------|-------------|
| [§21 Schema & Help Discoverability](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md) | Enforces: bare-invocation exit 0 now a prerequisite to §21 scoring |
| [§1 Exit Codes & Status Signaling](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) | Enforces: exit-code contract that bare invocation must satisfy |
| [§52 Recursive Command Tree Discovery Cost](../challenges/01-critical-ecosystem-runtime-agent-specific/52-medium-command-tree-discovery.md) | Composes: schema export assumes entry-point works |
| [§37 REPL / Interactive Mode Accidental Triggering](../challenges/01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md) | Composes: `shell` subcommands visible in root help pose REPL risk |
| [§50 Stdin Consumption Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) | Provides: reason `stdin=DEVNULL` is required in the probe pattern |
| [REQ-F-068](../requirements/f-068-help-and-version-flag-purity.md) | Enforces: empty-invocation purity — no side effects, exit 0 |
| [REQ-F-009](../requirements/f-009-non-interactive-mode-auto-detection.md) | Provides: non-TTY detection that governs the empty-invocation path |
| [research/argparse.md](../research/argparse.md) | Sources: required-subcommand anti-pattern documented in framework research |
