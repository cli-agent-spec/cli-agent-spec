> **Part I: Output & Parsing** | Challenge §6

## 6. Command Composition & Piping

**Severity:** Medium | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** Low | **Context:** Low

### The Problem

Agents often need to chain commands: get an ID from one command, pass it to another. Poor composition support forces the agent to do text extraction and reformatting.

**Output not suitable for piping:**
```bash
$ tool create-user --name Alice | tool send-welcome-email
# Doesn't work: create-user outputs JSON blob, send-welcome-email expects a user ID
```

**Required format transformation between commands:**
```bash
$ ID=$(tool get-user --name Alice --format json | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
$ tool delete-user --id $ID
# Agent has to know the JSON structure and write extraction logic
```

**Commands that don't read from stdin:**
```bash
$ tool get-user-id --name Alice | tool send-email
# send-email ignores stdin, requires --user-id argument
```

### Impact

- Agent must write fragile JSON extraction logic for every inter-command data transfer
- No stdin support forces use of temporary files or shell variable extraction, both error-prone
- Commands that don't accept `-` for stdin cannot participate in streaming pipelines

### Solutions

**`--format id` mode (extract single value):**
```bash
$ tool get-user --name Alice --format id
42
# Just the primary identifier, no JSON, pipeable
```

**Stdin acceptance for IDs:**
```bash
$ tool get-user --name Alice --format id | tool send-welcome-email --user-id -
# --user-id - means "read from stdin"
```

**Batch input from file/stdin:**
```bash
$ tool list-users --format jsonl | tool send-welcome-email --users-jsonl -
```

**`--from` flag for reading prior command output:**
```bash
$ tool get-user --name Alice --format json > /tmp/user.json
$ tool send-welcome-email --from-file /tmp/user.json
```

**For framework design:**
- Every command that takes an ID also accepts `-` to read from stdin
- Provide `--format id` as a standard extraction mode
- Define a pipe protocol: each framework command can declare what it emits and what it accepts

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No `--format id` mode; commands don't accept stdin; inter-command data transfer requires manual JSON extraction |
| 1 | `--format json` exists but single-value extraction requires `jq` or inline Python; no stdin acceptance |
| 2 | `--format id` mode available on read commands; some commands accept `-` to read ID from stdin |
| 3 | All ID-taking commands accept `-` for stdin; `--format id` standard across the tool; `--from-file` accepted for structured input |

**Check:** Chain two commands using shell pipe — `tool get-X --format id | tool use-X --id -` — and verify it works without intermediate variables or subshell parsing.

---

### Agent Workaround

**Signature:** piped chain `tool a | tool b` exits with a missing-argument usage error while data sits on stdin; `-` rejected as an ID argument value

**Tier:** B (one observable check, then one command)

**Extract IDs explicitly with `jq` or inline Python rather than shell pipes:**

```python
# Step 1: get the primary ID
result = subprocess.run(
    ["tool", "get-user", "--name", "Alice", "--format", "json"],
    capture_output=True, text=True,
)
user_id = json.loads(result.stdout)["data"]["id"]

# Step 2: pass it to the next command
result2 = subprocess.run(
    ["tool", "send-welcome-email", "--user-id", str(user_id)],
    capture_output=True, text=True,
)
```

**Use temp files for complex intermediate state:**
```python
import tempfile, json, os

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(parsed_result["data"], f)
    tmppath = f.name

try:
    result = subprocess.run(
        ["tool", "process", "--from-file", tmppath],
        capture_output=True, text=True,
    )
finally:
    os.unlink(tmppath)
```

**Limitation:** If the tool suite has no consistent ID field name (some use `id`, others `uuid`, `key`, `name`), the agent must know each command's output schema to extract the right value — check the tool manifest for `primary_key` metadata if available, otherwise read the output schema
