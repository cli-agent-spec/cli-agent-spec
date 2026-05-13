> **Part III: Errors & Discoverability** | Challenge §21

## 21. Schema & Help Discoverability

**Severity:** Medium | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** Medium

### The Problem

Agents need to know what commands exist, what parameters they accept, and what they return — without running commands to discover this. Human-formatted help text is expensive to parse.

**Help text only in human format:**
```bash
$ tool --help
Usage: tool [OPTIONS] COMMAND [ARGS]...

Options:
  --verbose  Enable verbose output
  --help     Show this message and exit.

Commands:
  deploy   Deploy the application
  rollback Rollback to previous version
```

**No machine-readable schema:**
```bash
$ tool deploy --help
# Returns prose. Agent has to parse natural language to understand args.
```

**No output schema:**
```bash
# Agent has no way to know what fields deploy will return without running it
```

### Impact

- Agent must run commands to discover their parameters and output shape — burning tokens and potentially causing side effects
- Human-formatted help must be parsed with fragile natural-language extraction
- No output schema means the agent cannot validate responses or detect breaking changes
- Per-command schema docs require one help invocation per command, multiplying token cost

### Solutions

**Machine-readable command manifest:**
```bash
$ tool --schema --output json
{
  "commands": [
    {
      "name": "deploy",
      "description": "Deploy the application to an environment",
      "danger_level": "mutating",
      "parameters": [
        {"name": "env", "type": "string", "required": true,
         "enum": ["staging", "prod"], "description": "Target environment"},
        {"name": "version", "type": "string", "required": false,
         "description": "Version tag to deploy (default: latest)"},
        {"name": "dry-run", "type": "boolean", "default": false}
      ],
      "output_schema": {
        "type": "object",
        "properties": {
          "ok": {"type": "boolean"},
          "effect": {"type": "string", "enum": ["deployed", "noop"]},
          "data": {
            "deployment_id": {"type": "string"},
            "version": {"type": "string"}
          }
        }
      },
      "exit_codes": {
        "0": "success",
        "1": "deployment failed",
        "4": "environment not found",
        "7": "deployment timed out"
      }
    }
  ]
}
```

**For framework design:**
- Every command auto-generates its schema from its parameter declarations
- `tool --schema` outputs the full manifest
- If `tool` with no arguments renders root help, keep it lightweight and use it to point to `--schema` rather than dumping the full manifest implicitly
- `tool --print-schema` is accepted as a compatibility alias for `tool --schema`
- Output schema is declared alongside input schema, not separate
- Schema versioning: `tool --schema-version` to track evolution

### Evaluation

**Prerequisite check (§1 / REQ-F-068):** Run `tool` with no arguments and verify exit code is 0. If the bare invocation exits non-zero, cap the score at 0 regardless of `--schema` richness — the agent's first-contact probe fails before any discovery can occur.

| Score | Condition |
|-------|-----------|
| 0 | Bare invocation exits non-zero; or help is prose only with no `--schema` flag; agent must parse natural language to understand arguments |
| 1 | Bare invocation exits 0 with root help; `--help --output json` returns some structured info but no output schema; commands not enumerable from root |
| 2 | Bare invocation exits 0; `tool --schema --output json` returns command list with parameter types, required flags, and exit codes |
| 3 | Bare invocation exits 0; full manifest includes `output_schema` per command; `danger_level` declared; schema auto-generated from parameter declarations; `--print-schema` compatibility alias accepted |

**Check:** First run `tool` with no arguments and confirm exit 0. Then run `tool --schema --output json` and verify the response includes `commands[].parameters[].type` and `commands[].output_schema` for at least one command.

---

### Agent Workaround

**Load the full schema manifest once per session; use it to construct and validate calls:**

```python
import subprocess, json

def load_schema(tool: str) -> dict:
    result = subprocess.run(
        [tool, "--schema", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

schema = load_schema("tool")
commands = {cmd["name"]: cmd for cmd in schema.get("commands", [])}

def get_required_params(cmd_name: str) -> list[str]:
    cmd = commands.get(cmd_name, {})
    return [
        p["name"] for p in cmd.get("parameters", [])
        if p.get("required", False)
    ]

# Validate before calling
required = get_required_params("deploy")
missing = [p for p in required if p not in provided_args]
if missing:
    raise ValueError(f"Missing required params for 'deploy': {missing}")
```

**Fall back to `--help` parsing when `--schema` is not available:**
```python
def get_params_from_help(tool: str, command: str) -> list[str]:
    result = subprocess.run(
        [tool, command, "--help"],
        capture_output=True, text=True,
    )
    # Extract --flag names from help text (fragile, last resort)
    import re
    return re.findall(r"--(\w[\w-]*)", result.stdout)
```

When available, start with root help on empty invocation to discover top-level commands, then narrow to per-command help only for the command you intend to call:
```python
def get_root_help(tool: str) -> str:
    result = subprocess.run(
        [tool],
        capture_output=True, text=True,
    )
    return result.stdout
```

**Limitation:** If the tool has no `--schema` flag and help text is prose, the agent must discover parameters through trial and error — call with no arguments first to see root usage, then inspect the selected subcommand's help or error message; accept that this consumes tokens and may trigger partial side effects
