> **Part V: Environment & State** | Challenge §30

## 30. Undeclared Filesystem Side Effects

**Severity:** Medium | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Low | **Time:** Low | **Context:** Low

### The Problem

Tools write to locations the agent doesn't know about: caches, logs, lock files, temp dirs, credential stores. These accumulate silently, cause permission errors, leak data between sessions, and make behavior non-reproducible.

**Cache writes the agent can't control:**
```bash
$ tool fetch-schema --url https://api.example.com/schema
# Writes: ~/.cache/tool/schemas/api.example.com.json
# Agent doesn't know
# Next call: uses stale cache, returns wrong schema
# Agent has no way to invalidate or inspect the cache
```

**Log files accumulating without rotation:**
```bash
$ tool process large-file.csv
# Writes: ~/.local/share/tool/logs/2024-03-11.log (500MB)
# Agent runs 100 times: 50GB of logs
# Disk full → unrelated commands start failing
```

**Credential store side effects:**
```bash
$ tool login --token $TOKEN
# Writes: ~/.config/tool/credentials.json
# Another agent session overwrites same file with different token
# First session's subsequent calls now use wrong token
```

**Temp files that outlive the command:**
```bash
$ tool export --format xlsx
# Writes: /tmp/tool-export-abc123.xlsx
# Returns path in output
# Agent doesn't clean up → /tmp fills over time
```

### Impact

- Stale cache causes wrong results that are hard to trace
- Disk exhaustion from uncleaned logs/temp files
- Credential files stomped by concurrent sessions
- Data leaks: sensitive output persists on disk after session ends

### Solutions

**Declare all side effect locations in schema:**
```json
{
  "command": "fetch-schema",
  "filesystem_side_effects": [
    {
      "path": "~/.cache/tool/schemas/",
      "type": "cache",
      "ttl_seconds": 3600,
      "clearable_with": "tool cache clear --scope schemas"
    }
  ]
}
```

**`--no-cache` and `--cache-ttl` flags:**
```bash
tool fetch-schema --url ... --no-cache
tool fetch-schema --url ... --cache-ttl 0
```

**Temp files registered for cleanup:**
```json
{
  "ok": true,
  "data": {"path": "/tmp/tool-export-abc123.xlsx"},
  "cleanup": {
    "command": "tool cleanup --file /tmp/tool-export-abc123.xlsx",
    "auto_cleanup_after_seconds": 3600
  }
}
```

**`tool status --show-side-effects` inventory:**
```bash
$ tool status --show-side-effects --output json
{
  "cache": {"path": "~/.cache/tool/", "size_bytes": 45000000},
  "logs":  {"path": "~/.local/share/tool/logs/", "size_bytes": 524000000},
  "temp":  {"path": "/tmp/tool-*/", "count": 14, "size_bytes": 2000000}
}
```

**For framework design:**
- Every command declares `filesystem_side_effects` in its schema
- Framework provides `tool cleanup` that removes all known side effect paths
- Temp files use a session-scoped directory, auto-cleaned when session ends
- Log rotation built into framework (max size, max age)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Filesystem side effects undeclared; no cleanup command; cache, logs, and temp files accumulate without agent control |
| 1 | `--no-cache` flag on some commands; no `filesystem_side_effects` in schema; no cleanup command |
| 2 | `tool status --show-side-effects` lists known paths with sizes; `--no-cache` supported; temp file paths returned in response |
| 3 | `filesystem_side_effects` declared per-command in schema; `tool cleanup` removes all known side effects; response includes `cleanup.command` for temp files |

**Check:** Run `tool status --show-side-effects --output json` — verify it returns a structured inventory of cache, log, and temp paths.

---

### Agent Workaround

**Signature:** repeated calls return stale data despite upstream changes; disk usage grows in `~/.cache` or `/tmp` after runs; leftover temp files

**Tier:** B (one observable check, then one command)

**Check for and clean up temp files returned in response; pass `--no-cache` for reproducible reads:**

```python
import subprocess, json, os

result = subprocess.run(
    ["tool", "export", "--format", "xlsx", "--no-cache", "--output", "json"],
    capture_output=True, text=True,
)
parsed = json.loads(result.stdout)

# Clean up temp files proactively
cleanup = parsed.get("cleanup", {})
cleanup_cmd = cleanup.get("command")
if cleanup_cmd:
    subprocess.run(cleanup_cmd.split(), capture_output=True)

# Or remove the path directly if returned
export_path = parsed.get("data", {}).get("path")
if export_path and os.path.exists(export_path):
    os.unlink(export_path)
```

**Force cache bypass for commands that may use stale state:**
```python
env = {
    **os.environ,
    "TOOL_NO_CACHE": "1",   # common env var pattern
    "CI": "true",           # many tools skip cache in CI mode
}
result = subprocess.run(
    ["tool", "fetch-schema", "--url", url, "--no-cache"],
    capture_output=True, text=True,
    env=env,
)
```

**Limitation:** If the tool declares no `filesystem_side_effects` and returns no `cleanup` field, the agent cannot know what was written — run `tool status --show-side-effects` after long sessions to inventory accumulated files and decide whether to clean them
