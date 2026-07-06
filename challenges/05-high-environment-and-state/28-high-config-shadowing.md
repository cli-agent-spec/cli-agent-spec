> **Part V: Environment & State** | Challenge §28

## 28. Config File Shadowing & Precedence

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

Most CLI tools load config from multiple locations in a priority order. Agents operating in real environments encounter unexpected config from the user's dotfiles, project directories, or environment variables — silently overriding expected defaults.

**Silent config override:**
```bash
$ tool deploy --env staging
# Agent expects: deploy to staging
# But ~/.config/tool/config.toml contains: default_env = "production"
# And that takes precedence over --env flag (bug in tool)
# Result: deployed to production — no warning, exit 0
```

**Project-local config shadows global:**
```bash
$ cd /project && tool build
# /project/.toolrc sets: registry = "internal.registry.example.com"
# Agent doesn't know this file exists
# Build uses internal registry — fails in agent's network context
```

**Precedence that's never documented:**
```
Actual precedence (undocumented):
  1. Environment variables
  2. --flag arguments
  3. ./.tool.yaml
  4. ~/.config/tool/config.yaml
  5. /etc/tool/config.yaml
  6. Compiled-in defaults

Agent assumes: --flag arguments win. They don't.
```

**Environment variable config that's invisible:**
```bash
TOOL_ENDPOINT=http://internal-server tool deploy
# Agent doesn't set this env var
# But CI system has it set from a previous step
# Tool connects to internal-server, agent doesn't know why
```

### Impact

- Behavior differs between agent's environment and expected defaults
- Impossible to reproduce agent's behavior in isolation
- Security: production credentials loaded when staging expected
- Agent cannot detect that its explicit flags were overridden

### Solutions

**`--show-config` flag that reveals effective configuration:**
```bash
$ tool --show-config --output json
{
  "effective_config": {
    "env": "production",
    "registry": "internal.registry.example.com",
    "timeout": 30
  },
  "sources": {
    "env":      {"source": "~/.config/tool/config.toml", "value": "production"},
    "registry": {"source": "./.toolrc",                  "value": "internal..."},
    "timeout":  {"source": "default",                    "value": 30}
  }
}
```

**Include active config in every response `meta`:**
```json
{
  "meta": {
    "effective_config_hash": "sha256:abc123",
    "config_sources": ["~/.config/tool/config.toml", "./.toolrc"]
  }
}
```

**`--no-config` flag for isolated runs:**
```bash
tool deploy --no-config --env staging
# Ignores all config files and env vars
# Uses only explicit flags + compiled defaults
# Reproducible behavior regardless of environment
```

**Explicit config path:**
```bash
tool --config /dev/null deploy --env staging
# Guaranteed: no config file loaded
```

**For framework design:**
- Documented, stable precedence order (flags > env vars > local file > global file > defaults)
- `tool --show-config` is a built-in framework command
- `--no-config` disables all file-based config loading
- `meta.config_sources` included in every response

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Config precedence undocumented; env vars or config files can silently override explicit flags; no way to inspect effective config |
| 1 | `--show-config` exists but output is prose; `meta.config_sources` absent from responses |
| 2 | `tool --show-config --output json` shows effective config and per-field sources; precedence order documented |
| 3 | `--no-config` flag available for isolated runs; `meta.config_sources` in every response; flags always win over files (documented invariant) |

**Check:** Set a conflicting env var and run `tool --show-config --output json` — verify the `sources` field identifies the env var as the active source for that setting.

---

### Agent Workaround

**Signature:** explicit flags appear ignored; identical command behaves differently across machines or directories; exit `0` with an unexpected target

**Tier:** B (one observable check, then one command)

**Always run `tool --show-config --output json` before any configuration-sensitive operation:**

```python
import subprocess, json

def get_effective_config(tool: str) -> dict:
    result = subprocess.run(
        [tool, "--show-config", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
        return data.get("effective_config", {})
    except json.JSONDecodeError:
        return {}

config = get_effective_config("tool")
actual_env = config.get("env")
if actual_env != "staging":
    raise RuntimeError(
        f"Config shadowing detected: expected env=staging, tool has env={actual_env!r}"
    )
```

**Use `--no-config` or `--config /dev/null` for reproducible runs when supported:**
```python
result = subprocess.run(
    ["tool", "--no-config", "deploy", "--env", "staging"],
    capture_output=True, text=True,
    env={**os.environ, "TOOL_ENV": ""},  # clear env var overrides too
)
```

**Limitation:** If the tool has no `--show-config` command and does not include `meta.config_sources` in responses, the agent cannot detect config shadowing — validate critical settings by checking the response's effective values (e.g., `data.endpoint`) against what was expected
