> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §46

## 46. API Schema to CLI Flag Translation Loss

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** High | **Time:** Medium | **Context:** Medium

### The Problem

CLI tools that wrap HTTP APIs (the majority of developer-facing CLIs) suffer from "translation loss" — the API's native JSON schema is translated into a set of CLI flags by a human author, and that translation is always lossy. The API may accept nested objects, arrays, arbitrary key-value maps, or complex discriminated unions. The CLI flattens these into `--flag value` pairs, losing type information, making required/optional status ambiguous, and forcing agents to learn two schemas (the API schema and the CLI flag schema) that should be the same thing.

The jpoehnelt rubric's Axis 2 defines this precisely: at level 3 ("zero translation loss"), an agent should be able to use the API schema as documentation directly — passing a JSON payload to the CLI that maps one-to-one to the API request body, with no CLI-specific translation step.

This is distinct from challenge #21 (Schema & Help Discoverability), which concerns whether a schema exists. This challenge concerns the semantic fidelity of the CLI schema to the underlying API schema — even when both schemas exist, they may diverge.

```bash
# API schema (from OpenAPI spec) expects:
{
  "user": {
    "name": "Alice",
    "roles": ["admin", "viewer"],
    "metadata": {"department": "engineering"}
  }
}

# CLI equivalent (lossy translation):
my-tool user create \
  --name Alice \
  --roles admin,viewer \        # Array represented as comma-separated string (lossy!)
  --metadata-department engineering  # Nested key flattened with hyphen separator (lossy!)

# Problems:
# - What if a role name contains a comma?
# - What if metadata has 20 keys?
# - What if the nested structure has 4 levels?
# - Agent must learn the translation rules; they differ per tool
```

The translation loss creates errors when:
1. Values contain the separator character (comma in role names)
2. The flattened flag space has naming conflicts
3. New API fields are added but the CLI doesn't expose them yet
4. Array ordering matters but comma-separated representation loses ordering guarantees

### Impact

- Agents working with both an API and its CLI wrapper must maintain two mental models of the same interface
- Lossy translations silently truncate or corrupt complex values (arrays containing separator characters, deeply nested objects)
- API fields not yet mapped to CLI flags are inaccessible without falling back to raw HTTP clients
- Schema divergence grows over time as the API evolves faster than the CLI wrapper
- Agents that have successfully used the API directly may construct incorrect CLI invocations because they apply API schema knowledge to CLI flag patterns incorrectly

### Solutions

**Level 1 — Raw JSON payload input:**
```bash
# Accept raw JSON payload for complex commands (jpoehnelt Axis 2 level 2)
my-tool user create --json '{"name": "Alice", "roles": ["admin", "viewer"], "metadata": {...}}'
```

**Level 2 — Stdin JSON for structured input:**
```bash
echo '{"name": "Alice", "roles": ["admin", "viewer"]}' | my-tool user create --from-stdin
```

**Level 3 — Zero translation loss (jpoehnelt Axis 2 level 3):**
```bash
# CLI accepts the exact API request body; maps directly to API call with no reinterpretation
my-tool api POST /users --body '{"user": {"name": "Alice", "roles": [...]}}'
# Agent uses the OpenAPI spec as CLI documentation directly
```

**For framework design:**
- For every mutating command, accept `--json <payload>` as an alternative to individual flags, where the payload maps directly to the underlying API request body
- Expose a `--raw-api` mode (jpoehnelt Axis 2 level 3) that accepts the API request body directly and performs no flag-to-body translation
- Validate that the `--json` payload passes the same JSON Schema as the API request body (i.e., the CLI's JSON Schema and the API's JSON Schema are identical for mutating operations)
- `--schema` output should include both the CLI flag schema and, where applicable, the underlying API JSON Schema with a reference to where translation occurs
- Generate CLI wrappers from OpenAPI specs (rather than hand-writing them) to guarantee zero initial translation loss

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No `--json` flag; arrays only as comma-separated strings; nested objects flattened with hyphens; no escape for separator characters |
| 1 | `--json` flag exists on some commands but validation is against the CLI flag schema, not the API body schema |
| 2 | `--json` accepts the full API request body on all mutating commands; validated against API JSON Schema |
| 3 | `--raw-api` mode passes payload directly; CLI schema and API schema identical for mutating operations; generated from OpenAPI spec |

**Check:** Pass a value containing the array separator character (e.g., a comma in a tag name) via `--json` — verify it is accepted correctly and not split.

---

### Agent Workaround

**Signature:** comma-containing value arrives split into multiple items; API-documented field has no corresponding flag; `unknown option` for fields the API accepts

**Tier:** A (one safe command, no branching)

**Use `--json` to bypass flag-based translation for complex structured inputs:**

```python
import subprocess, json

# Prefer --json over individual flags for complex or nested inputs
payload = {
    "user": {
        "name": "Alice",
        "roles": ["admin", "viewer"],   # no comma-separator ambiguity
        "metadata": {"department": "engineering", "team": "platform"}
    }
}

result = subprocess.run(
    ["tool", "user", "create",
     "--json", json.dumps(payload),   # raw JSON, no translation loss
     "--output", "json"],
    capture_output=True, text=True,
)
parsed = json.loads(result.stdout)
```

**Fall back to individual flags with caution around separator characters:**
```python
# When --json is not available, verify separator-containing values are handled
roles = ["admin", "viewer"]
for role in roles:
    if "," in role:
        raise ValueError(
            f"Role {role!r} contains comma — use --json flag to avoid "
            "comma-separated array translation loss"
        )

result = subprocess.run(
    ["tool", "user", "create", "--roles", ",".join(roles)],
    capture_output=True, text=True,
)
```

**Limitation:** If the tool has no `--json` flag and uses comma-separated arrays, values containing the separator cannot be expressed — use the underlying API directly (bypassing the CLI) for inputs that require full JSON fidelity
