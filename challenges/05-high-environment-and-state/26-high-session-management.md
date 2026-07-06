> **Part V: Environment & State** | Challenge §26

## 26. Stateful Commands & Session Management

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Some CLIs maintain state between invocations (login sessions, active contexts, selected environments). Agents running commands in parallel or across sessions can have state conflicts.

**Hidden global state:**
```bash
$ tool use-context production
Switched to production context.

# In another agent session simultaneously:
$ tool use-context staging
Switched to staging context.

# Back in first session:
$ tool deploy   # ← now deploys to staging, not production!
```

**Session state without indication:**
```bash
$ tool login
Logged in as alice@example.com

$ tool list-resources
# Returns resources for alice — but agent doesn't know it's logged in as alice
# If another process ran `tool login` as bob, results changed silently
```

**State stored in shared locations:**
```bash
~/.config/tool/current-context   # shared across all processes, all agents
```

### Impact

- Parallel agent sessions silently overwrite each other's context, causing operations to target the wrong environment
- Agent cannot determine the active context without an explicit `tool status` call before every operation
- Stateful side effects (login, context switch) bleed across unrelated agent sessions sharing the same filesystem
- No indication in command output that results are context-dependent, so errors appear as data anomalies rather than configuration conflicts

### Solutions

**Explicit context per invocation:**
```bash
tool deploy --context production           # never rely on implicit current context
tool list-resources --token $TOKEN         # stateless auth per-call
tool --config /tmp/agent-session-42.json deploy  # isolated config file
```

**State inspection command:**
```bash
$ tool status --output json
{
  "logged_in": true,
  "user": "alice@example.com",
  "current_context": "production",
  "token_expires": "2024-03-11T16:00:00Z"
}
```

**For framework design:**
- Provide `--config` / `--context` override for every command
- Default to stateless operation; state is opt-in
- Document all global state locations in `tool status --show-state-files`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Commands rely on implicit global state; no `--context` override; parallel agents silently conflict |
| 1 | `--context` flag exists on some commands; `tool status` returns current session info but not sources |
| 2 | All mutating commands accept `--context`; `tool status --output json` shows `current_context`, `user`, and `token_expires` |
| 3 | `--config` flag accepts isolated config file path; `tool status --show-state-files` lists all global state locations; framework defaults to stateless per-call auth |

**Check:** Run `tool status --output json` and verify it emits `current_context` and `user` as machine-readable fields — not prose.

---

### Agent Workaround

**Signature:** same command silently targets a different context or user across sessions; results change after another process runs `login` or `use-context`

**Tier:** B (one observable check, then one command)

**Always pass explicit `--context` and supply credentials per-call; read `tool status` before any session-sensitive operation:**

```python
import subprocess, json, os

def get_session_state(tool: str) -> dict:
    result = subprocess.run(
        [tool, "status", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

# Verify context before mutating operation
state = get_session_state("tool")
if state.get("current_context") != "production":
    raise RuntimeError(
        f"Wrong context: expected 'production', got '{state.get('current_context')}'"
    )

# Use explicit context flag to avoid race with other agent sessions
result = subprocess.run(
    ["tool", "deploy", "--context", "production"],
    capture_output=True, text=True,
)
```

**Use per-agent isolated config file when `--config` is supported:**
```python
import tempfile, json, os

# Write a session-scoped config with explicit credentials
config = {"context": "production", "token": os.environ["TOOL_TOKEN"]}
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(config, f)
    config_path = f.name

try:
    result = subprocess.run(
        ["tool", "--config", config_path, "deploy"],
        capture_output=True, text=True,
    )
finally:
    os.unlink(config_path)
```

**Limitation:** If the tool stores all state in a single shared file (e.g., `~/.config/tool/config.toml`) and offers no `--config` override, parallel agent sessions will race on that file — serialize tool calls via an external lock or run each agent in an isolated home directory
