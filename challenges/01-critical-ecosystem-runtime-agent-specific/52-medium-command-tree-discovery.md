> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §52

## 52. Recursive Command Tree Discovery Cost

**Severity:** Medium | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** High

### The Problem

Most CLIs require N+1 help calls to discover the full command surface: one call to list top-level subcommands, then one more call per subcommand to see its flags. A tool with 20 subcommands requires 21 sequential round trips just to build a mental model before any real work begins. With 3+ levels of nesting (`tool resource type action --flags`), the discovery cost grows exponentially. There is no standard for returning the full command tree in a single structured call.

```bash
$ tool --help
# Shows: create, list, update, delete, config, auth, export  ← 7 subcommands

$ tool create --help     # call 2
$ tool list --help       # call 3
$ tool update --help     # call 4
$ tool delete --help     # call 5
$ tool config --help     # call 6
$ tool config get --help # call 7 — subcommand of subcommand
$ tool config set --help # call 8
# ... 8+ calls just to see all flags, before any work starts

# Deep nesting:
$ aws ec2 describe-instances --help    # 3 levels deep
# Discovering the full aws CLI surface: hundreds of calls
```

The problem compounds when the agent must select the right command for a task — it needs to see all available commands before choosing, which means paying the full discovery cost upfront.

### Impact

- 10–50+ tool calls burned on discovery before first productive call
- Full command tree may consume a large fraction of the context window when retrieved incrementally
- Agent may miss relevant subcommands it didn't know to ask about
- Cached command trees go stale after tool updates; no standard way to detect staleness

### Solutions

**Single-call full tree export:**
```bash
$ tool --schema --full
```
```json
{
  "tool": "my-tool",
  "version": "1.2.3",
  "schema_version": "1.0",
  "commands": [
    {
      "name": "create",
      "description": "Create a new resource",
      "args": [],
      "flags": [],
      "subcommands": []
    },
    {
      "name": "config",
      "subcommands": [
        { "name": "get", "args": [] },
        { "name": "set", "args": [] }
      ]
    }
  ]
}
```

**For framework design:**
- `tool --schema` (REQ-O-013) MUST return the full command tree by default, not just the top-level command
- Each command node in the tree includes: name, description, args with types and constraints, flags, required/optional status, subcommands
- The full schema export must be a single synchronous call completing in under 500ms regardless of command count

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No single-call schema export; discovering all subcommands requires N+1 sequential help calls |
| 1 | `tool --schema` returns top-level commands only; subcommand details require additional help calls |
| 2 | `tool --schema --output json` returns full tree in one call; each command includes name, description, flags |
| 3 | Full tree export including args with types, required/optional status, and nested subcommands; completes in <500ms |

**Check:** Run `tool --schema --output json` and verify the output is a complete tree with all subcommands and their flags — no additional `--help` calls needed.

---

### Agent Workaround

**Signature:** `--help` lists subcommand names only; each subcommand's flags require another `--help` call; no single `--schema` call returns the full command tree

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** `tool --schema --output json`; if that fails, escalate with the command, exit code, stdout, and stderr

**Load the full schema tree in one call at session start; cache it for the session:**

```python
import subprocess, json

_schema_cache: dict = {}

def get_schema(tool: str) -> dict:
    if tool in _schema_cache:
        return _schema_cache[tool]

    # Try single-call full tree first
    result = subprocess.run(
        [tool, "--schema", "--output", "json"],
        capture_output=True, text=True,
        timeout=10,
    )
    try:
        schema = json.loads(result.stdout)
        _schema_cache[tool] = schema
        return schema
    except json.JSONDecodeError:
        pass

    # Fall back: collect top-level commands from --help
    result = subprocess.run([tool, "--help"], capture_output=True, text=True)
    import re
    commands = re.findall(r'^\s{2,4}(\w[\w-]*)\s', result.stdout, re.MULTILINE)
    schema = {"commands": [{"name": cmd} for cmd in commands]}
    _schema_cache[tool] = schema
    return schema

def find_command(schema: dict, cmd_name: str) -> dict | None:
    for cmd in schema.get("commands", []):
        if cmd.get("name") == cmd_name:
            return cmd
        sub = find_command({"commands": cmd.get("subcommands", [])}, cmd_name)
        if sub:
            return sub
    return None
```

**Limitation:** If the tool has no `--schema` flag and produces only human-formatted help, the agent must make N+1 sequential help calls to discover all subcommands — cache results aggressively and accept that the discovery budget is spent once per session
