> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §54

## 54. Conditional / Dependent Argument Requirements

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Medium | **Context:** Low

### The Problem

Many commands have arguments only required when another argument takes a specific value: `--auth-type oauth` requires `--client-id` and `--client-secret`; `--output file` requires `--output-path`. These conditional dependencies are almost never expressed in machine-readable form. The agent provides a partial set of arguments, the tool fails, and the agent must retry — often multiple times, discovering one missing co-requirement per round trip.

```bash
# Round trip 1
$ tool create --type oauth
Error: missing required argument: --client-id

# Round trip 2
$ tool create --type oauth --client-id abc123
Error: missing required argument: --client-secret

# Round trip 3: finally works — but took 3 calls to discover a 2-flag dependency
$ tool create --type oauth --client-id abc123 --client-secret xyz
```

### Impact

- N round trips to discover N co-required arguments in a dependency group
- Mid-execution failures for implicit conditional requirements not in the schema
- Agent cannot pre-validate a complete invocation without undocumented domain knowledge

### Solutions

**Schema declares conditional requirement groups:**
```json
{
  "arg_groups": [
    {
      "condition": {"arg": "auth-type", "equals": "oauth"},
      "required": ["client-id", "client-secret"]
    }
  ]
}
```

**Phase 1 validation reports ALL missing co-requirements at once:**
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "missing_args": [
      {"name": "client-id", "reason": "required when --auth-type=oauth"},
      {"name": "client-secret", "reason": "required when --auth-type=oauth"}
    ]
  }
}
```

**For framework design:**
- Schema format MUST support `required_when` and `arg_groups` conditional dependency declarations
- Phase 1 validation MUST evaluate all conditional requirements simultaneously and report all missing args in a single error response

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Conditional requirements discovered one per round trip; no `arg_groups` in schema; each retry reveals one more missing arg |
| 1 | Some conditional requirements documented in `--help` prose; not machine-readable; still reported one at a time |
| 2 | `VALIDATION_ERROR` reports all missing co-required args at once via `missing_args` array |
| 3 | `arg_groups` with `condition` declared in schema; `--validate-only` available to pre-check without executing |

**Check:** Pass only the triggering arg (e.g., `--auth-type oauth`) without its co-required args — verify a single error response lists ALL missing co-required args simultaneously.

---

### Agent Workaround

**Signature:** `missing required argument` errors surface one flag per retry after setting a value like `--type oauth`; each round trip reveals one more co-requirement

**Tier:** B (one observable check, then one command)

**Extract all `missing_args` from a single validation error; provide all co-required args in one retry:**

```python
import subprocess, json

def build_complete_call(base_cmd: list[str], known_args: dict) -> dict:
    """Discover all required args by doing a dry-run validation pass."""
    cmd = [*base_cmd, "--validate-only"] if "--validate-only" in get_flags(base_cmd[0]) else base_cmd

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return known_args

    if parsed.get("ok"):
        return known_args  # no missing args

    error = parsed.get("error", {})
    if error.get("code") == "VALIDATION_ERROR":
        missing = error.get("missing_args", [])
        for m in missing:
            arg_name = m.get("name") or m.get("field", "")
            reason = m.get("reason", "required")
            if arg_name not in known_args:
                print(f"Missing required arg: --{arg_name} ({reason})")
                # Agent must now provide this arg — add it to known_args
    return known_args

def call_with_all_args(cmd: list[str], args: dict) -> dict:
    """Build final call with all known args after validation."""
    full_cmd = list(cmd)
    for flag, value in args.items():
        full_cmd.extend([f"--{flag}", str(value)])
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

**Limitation:** If the tool reports missing args one at a time (not all at once), the agent must make N round trips to discover N co-required args — build the complete arg set from the schema's `arg_groups` declaration if available, or use `--validate-only` mode before the real call
