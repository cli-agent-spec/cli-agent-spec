> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §65

## 65. Global Configuration State Contamination

**Source:** Antigravity `04_state_and_concurrency.md` (RA)

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** High | **Context:** Low

### The Problem

Distinct from §28 (config file shadowing on READ), this challenge is about tools that WRITE to global configuration files (`~/.config/tool/`, `~/.tool/config.json`) as a side effect of normal operations, permanently altering the host environment for all future sessions. An agent running `tool configure --region us-east-1` intending a per-task setting may inadvertently persist it to the user's global config, affecting every subsequent human and agent session on that machine.

```bash
# Agent sets a config value, intending it to be temporary for this task
$ tool config set output-format=json
# Tool writes to ~/.config/tool/config.json
# Every future invocation of this tool by any user now outputs JSON
# Human opens a new terminal: tool behaves differently — agent contaminated the env

# More dangerous: agent changes authentication context
$ tool auth switch --account staging-account
# Tool writes active account to ~/.tool/auth.json
# Human's next tool use is unexpectedly in staging account — data risk

# Auto-migration contaminates even without explicit config commands:
$ tool update
# New version runs, silently migrates ~/.config/tool/config.json schema
# Git status now shows unexpected modifications — confusing to human
```

### Impact

- Permanent environmental changes visible to all users and future sessions
- Humans return to a modified environment after agent session — confusing and potentially dangerous
- CI systems share a filesystem; one agent job contaminates config for subsequent jobs
- Auto-migration writes make git working trees unexpectedly dirty

### Solutions

**Default all writes to local/session scope:**
```bash
# Bad: writes to global ~/.config/tool/config.json
$ tool config set region=us-east-1

# Good: writes to ./.tool-config (local, git-ignorable)
$ tool config set region=us-east-1
# Requires explicit --global flag for home-dir writes:
$ tool config set --global region=us-east-1
```

**Strict scope declaration in schema:**
```json
{
  "name": "config set",
  "write_scope": "local",   // "local" | "global" | "session"
  "global_flag": "--global",
  "danger_level": "mutating"
}
```

**Config write audit trail:**
```json
{
  "ok": true,
  "warnings": [
    {
      "code": "GLOBAL_CONFIG_MODIFIED",
      "path": "~/.config/tool/config.json",
      "key": "region",
      "previous_value": "eu-west-1",
      "new_value": "us-east-1"
    }
  ]
}
```

**For framework design:**
- Framework MUST default all config writes to the nearest `.tool-config` file in the working directory hierarchy, not to `~/.config/`
- Global config writes MUST require an explicit `--global` flag and MUST emit a `GLOBAL_CONFIG_MODIFIED` warning in the JSON response
- Auto-migrations MUST be opt-in: `tool migrate-config --confirm` rather than running silently on startup

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Config writes default to `~/.config/`; no `--global` flag required; no warning when global config is modified |
| 1 | Some config writes use local scope; `GLOBAL_CONFIG_MODIFIED` warning absent; auto-migration runs silently |
| 2 | `GLOBAL_CONFIG_MODIFIED` warning emitted in `warnings[]` when global config is written; `--global` flag required |
| 3 | Default scope is local (`.tool-config`); global writes require `--global`; auto-migration requires `--confirm`; `write_scope` declared in schema |

**Check:** Run a `tool config set` command without `--global` and verify it writes to a local config file (not `~/.config/`) and that the response includes `write_scope: "local"` in meta.

---

### Agent Workaround

**Signature:** `exit 0` on a config command but files under `~/.config/` or `~/.tool/` change; subsequent sessions show different defaults, formats, or accounts

**Tier:** B (one observable check, then one command)

**Check `warnings[]` for `GLOBAL_CONFIG_MODIFIED`; prefer session-scoped or local config commands:**

```python
import subprocess, json, os

def safe_config_set(tool: str, key: str, value: str, scope: str = "local") -> dict:
    """Set a config value in local scope — never contaminate global config."""
    cmd = [tool, "config", "set", f"{key}={value}", "--output", "json"]

    # Do NOT add --global unless explicitly requested
    # Some tools write to global by default — check the result

    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = json.loads(result.stdout)

    if not parsed.get("ok"):
        return parsed

    # Detect accidental global config modification
    warnings = parsed.get("warnings", [])
    global_modified = [
        w for w in warnings if w.get("code") == "GLOBAL_CONFIG_MODIFIED"
    ]
    if global_modified:
        for w in global_modified:
            path = w.get("path", "unknown")
            old_val = w.get("previous_value")
            new_val = w.get("new_value")
            print(
                f"WARNING: Global config modified at {path}: "
                f"{key}: {old_val!r} → {new_val!r}. "
                "This affects all future sessions on this machine."
            )
            # Consider reverting if this was unintentional
            # subprocess.run([tool, "config", "set", "--global", f"{key}={old_val}"])

    return parsed
```

**Limitation:** If the tool writes to global config by default with no `--local` scope option and no `GLOBAL_CONFIG_MODIFIED` warning, the only safe option is to avoid `config set` commands during agent sessions — use per-call flags (`--region`, `--output-format`) rather than persisted config, or run the agent in an isolated home directory to prevent contamination of the real user's config
