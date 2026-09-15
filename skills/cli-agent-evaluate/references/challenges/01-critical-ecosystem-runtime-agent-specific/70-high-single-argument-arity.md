> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §70

## 70. Single-Argument Arity Forcing Agent Loop Overhead

**Source:** FP

**Severity:** High | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Agents assume that commands operating on resources follow UNIX convention: `rm`, `cp`, `mv`, and similar tools accept one or more positional arguments. When a CLI command like `delete`, `move`, or `tag` only accepts a single positional argument, the agent passes a list and receives `unrecognized arguments` — a parser-level rejection before any work is done.

```bash
# Agent constructs a natural bulk invocation:
$ ws delete /notes/a.md /notes/b.md /notes/c.md
usage: ws [-h] {tree,find,...,delete,...} ...
ws: error: unrecognized arguments: /notes/b.md /notes/c.md

# Agent must now loop — three separate calls instead of one:
$ ws delete /notes/a.md   # exit 0
$ ws delete /notes/b.md   # exit 0
$ ws delete /notes/c.md   # exit 0
```

The problem compounds when the command has side effects: each loop iteration is a separate process launch, authentication check, and network round-trip. Partial failure mid-loop (§13) leaves the set in an inconsistent state with no built-in rollback.

Additionally, the schema never declares whether a command accepts one or many positional arguments (`nargs`), so the agent cannot pre-determine arity without probing — forcing either a trial invocation or a fallback to single-call loops as a defensive default.

### Impact

- N process launches, auth checks, and round trips instead of one
- Partial failure risk proportional to N: early errors leave remaining items unprocessed with no atomic rollback
- Token and time cost grows linearly with batch size — the larger the agent's intended batch, the worse the overhead
- Agent cannot distinguish "single-arg by design" from "single-arg by oversight" without reading source code

### Solutions

**Accept variadic positional arguments for any command whose logic is item-by-item:**

```python
# argparse
parser.add_argument("paths", nargs="+", help="One or more paths to delete")

# Click
@click.argument("paths", nargs=-1, required=True)

# Clap (Rust)
#[arg(num_args = 1..)]
paths: Vec<PathBuf>,

# Cobra (Go)
Args: cobra.MinimumNArgs(1),
```

**Report per-item results so the agent can detect partial failure:**

```json
{
  "ok": true,
  "results": [
    {"path": "/notes/a.md", "ok": true},
    {"path": "/notes/b.md", "ok": false, "error": {"code": "NOT_FOUND", "message": "Path does not exist"}}
  ]
}
```

**Declare arity in the schema manifest so agents can pre-determine call structure:**

```json
{
  "name": "delete",
  "args": [
    {"name": "paths", "nargs": "+", "description": "Paths to delete"}
  ]
}
```

**For framework design:**
- Commands that perform the same stateless operation per item MUST accept `nargs="+"` (one or more) positional arguments
- Per-item results MUST be returned as an array even when a single path is passed, so the agent can parse the response uniformly
- The manifest's `args` array MUST include `nargs` (`"1"`, `"?"`, `"*"`, `"+"`); absence of `nargs` MUST be treated as `"1"` by agents
- Partial success MUST be reported per-item with a top-level `ok: false` when any item fails; the agent must not have to infer failure count from missing output

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Single positional only; variadic invocation rejected with `unrecognized arguments`; no `nargs` in schema |
| 1 | Multiple paths accepted via `--file` flag repeated (`--file a --file b`); positional variadic still not supported |
| 2 | Variadic positional accepted (`nargs="+"`); `nargs` absent from schema; per-item result array returned |
| 3 | Variadic positional with `nargs` declared in schema manifest; per-item result array with `ok` per entry; top-level `ok: false` on any item failure |

**Check:** Invoke `tool delete path1 path2 path3` — verify all three are processed in a single call and the response contains a `results` array with one entry per path.

---

### Agent Workaround

**Signature:** usage line plus `unrecognized arguments:` listing the second and later positionals when multiple items are passed; the same command with one item exits `0`

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** `for item in <items>; do tool <subcommand> "$item" || break; done` (one positional per call, stop at first failure); if that fails, escalate with the command, exit code, stdout, and stderr

**Detect arity from schema before constructing the invocation; loop as a fallback when `nargs` is `"1"` or absent:**

```python
import subprocess, json

def get_command_nargs(tool: str, subcommand: str, arg_name: str) -> str:
    """Return nargs for a positional arg; default '1' if undeclared."""
    result = subprocess.run(
        [tool, subcommand, "--schema"],
        capture_output=True, text=True,
    )
    try:
        schema = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return "1"  # conservative default

    for arg in schema.get("args", []):
        if arg.get("name") == arg_name:
            return arg.get("nargs", "1")
    return "1"

def delete_items(tool: str, paths: list[str]) -> list[dict]:
    """Use variadic call when supported; loop when not."""
    nargs = get_command_nargs(tool, "delete", "paths")

    if nargs in ("+", "*"):
        result = subprocess.run(
            [tool, "delete", *paths],
            capture_output=True, text=True,
        )
        parsed = json.loads(result.stdout)
        return parsed.get("results", [parsed])

    # Fallback: one call per item
    results = []
    for path in paths:
        r = subprocess.run([tool, "delete", path], capture_output=True, text=True)
        try:
            results.append(json.loads(r.stdout))
        except json.JSONDecodeError:
            results.append({"path": path, "ok": r.returncode == 0})
    return results
```

**Limitation:** When looping over single-arg calls, partial failure mid-batch leaves already-processed items changed with no rollback — the agent must record which items succeeded before the failure and report the incomplete state rather than retrying the full batch
