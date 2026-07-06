> **Part V: Environment & State** | Challenge §32

## 32. Self-Update & Auto-Upgrade Behavior

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Medium | **Time:** High | **Context:** Low

### The Problem

Some CLI tools automatically check for updates, download new versions, or silently upgrade themselves. For agents, this means behavior can change mid-session, schemas can shift, and version-pinned agent skills can break without warning.

**Silent auto-update on invocation:**
```bash
$ tool deploy
Updating tool to v2.1.0... done
Deployed successfully.

# Agent built against v1.x schema — v2.x changed output format
# Agent's JSON parsing now fails on future calls in the same session
# No indication that an update occurred in the JSON output
```

**Update check that delays execution:**
```bash
$ tool sync
Checking for updates...   [3 second pause]
No updates available.
Syncing...
# Every invocation: 3s wasted on update check
# Across 50 tool calls per agent session: 2.5 minutes wasted
```

**Update check that fails and crashes the tool:**
```bash
$ tool deploy
Error: failed to check for updates: connection refused to updates.example.com
exit 1
# Agent thinks deploy failed
# Actually: update check server is down, deploy never ran
```

**Background update that conflicts with running command:**
```bash
$ tool process large-file.csv
# Background updater overwrites tool binary mid-execution
# Process crashes with: "text file busy" or silent corruption
```

### Impact

- Schema changes mid-session break agent's output parsing
- Update check latency accumulates across all tool calls
- Update check failures masquerade as command failures
- Binary replacement during execution causes crashes

### Solutions

**Disable auto-update in non-interactive / CI contexts:**
```python
import sys, os

AUTO_UPDATE = (
    sys.stdin.isatty()
    and not os.environ.get("CI")
    and not os.environ.get("TOOL_NO_UPDATE")
)
```

**`--no-update-check` flag:**
```bash
tool deploy --no-update-check
# Skips update check entirely for this invocation
```

**Update check only on explicit command:**
```bash
tool update          # explicit: check and apply update
tool update --check  # check only, don't apply
# Never auto-update during other commands
```

**Include version in every response `meta`:**
```json
{
  "meta": {
    "tool_version": "1.4.2",
    "schema_version": "1.2.0",
    "update_available": "2.0.0",   // non-blocking: just informational
    "update_channel": "stable"
  }
}
```

**Never replace running binary:**
```bash
# Update writes to tool.new, renames on next cold start
# Never overwrites tool binary while any instance is running
```

**For framework design:**
- `TOOL_NO_UPDATE=1` env var disables all update behavior
- Auto-update disabled whenever `CI=true` or stdout is not a TTY
- Update available surfaced as `meta.update_available`, never blocks execution
- `tool update` is the only command that modifies the tool binary

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Tool auto-updates on invocation; update check can fail and prevent the command from running; no way to disable |
| 1 | `--no-update-check` flag exists; update check still runs by default; `CI=true` not respected |
| 2 | Auto-update disabled when `CI=true` or stdout not a TTY; `TOOL_NO_UPDATE` env var supported; update available in `meta.update_available` |
| 3 | Update check never runs during non-update commands; `tool update` is the only update path; binary replacement deferred to cold start |

**Check:** Set `CI=true` and run any non-update command — verify no update check occurs and `meta.update_available` carries the notification without blocking execution.

---

### Agent Workaround

**Signature:** output contains `Checking for updates` or an update banner; every call pauses seconds before output; response format changes mid-session

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Run `CI=true TOOL_NO_UPDATE=1 tool <args>`; if that fails, escalate with the command, exit code, stdout, and stderr

**Disable auto-update via env vars; pin tool version and verify `meta.tool_version` in responses:**

```python
import subprocess, json, os

env = {
    **os.environ,
    "CI": "true",
    "TOOL_NO_UPDATE": "1",
}

result = subprocess.run(
    ["tool", "deploy", "--output", "json"],
    capture_output=True, text=True,
    env=env,
)
parsed = json.loads(result.stdout)

# Detect if an update occurred mid-session
meta = parsed.get("meta", {})
tool_version = meta.get("tool_version")
schema_version = meta.get("schema_version")

# Warn if version changed from session start
if hasattr(check_version, "last") and check_version.last != schema_version:
    raise RuntimeError(
        f"Schema version changed mid-session: {check_version.last} → {schema_version}"
    )
check_version.last = schema_version
```

**Detect update check latency and skip it when the tool supports the flag:**
```python
import time

start = time.monotonic()
result = subprocess.run(["tool", "--version"], capture_output=True, text=True)
elapsed = time.monotonic() - start

if elapsed > 1.0:
    # Likely an update check — add --no-update-check flag going forward
    UPDATE_FLAG = ["--no-update-check"]
else:
    UPDATE_FLAG = []
```

**Limitation:** If the tool auto-updates silently with no version in output and ignores `CI=true`, the agent has no way to detect that a schema-breaking upgrade occurred — pin the tool to a specific version via the package manager and use a lock file to prevent uncontrolled upgrades

