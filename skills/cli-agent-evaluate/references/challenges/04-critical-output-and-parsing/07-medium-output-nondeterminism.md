> **Part I: Output & Parsing** | Challenge §7

## 7. Output Non-Determinism

**Severity:** Medium | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Agents compare outputs, cache results, detect changes, and build logic on top of command results. If the same command with the same arguments produces different output on successive runs, all of these break silently.

**Random map/set ordering:**
```bash
$ tool list-permissions --role admin
{"permissions": ["write", "read", "delete", "admin"]}

$ tool list-permissions --role admin
{"permissions": ["admin", "delete", "read", "write"]}

# Agent compares: permissions changed? No — just reordered.
# Diff-based change detection: false positive every time
```

**Timestamps embedded in data fields:**
```bash
$ tool get-status --output json
{"status": "ok", "checked_at": "2024-03-11T14:30:01Z", "uptime": 3600}

$ tool get-status --output json
{"status": "ok", "checked_at": "2024-03-11T14:30:04Z", "uptime": 3603}

# Agent caches result, checks if output changed: always "changed"
# Retry detection: can't tell if operation ran twice or output just differs
```

**Random IDs in dry-run output:**
```bash
$ tool deploy --dry-run
{"effect": "would_create", "preview_id": "prev-a3f2c1"}

$ tool deploy --dry-run
{"effect": "would_create", "preview_id": "prev-9b4d2e"}

# Agent uses preview_id for follow-up call: ID is already stale
```

**Unordered batch results:**
```bash
$ tool list-users
{"users": [{"id": 3}, {"id": 1}, {"id": 2}]}  # run 1

$ tool list-users
{"users": [{"id": 1}, {"id": 3}, {"id": 2}]}  # run 2 — different order
```

### Impact

- Change detection produces constant false positives
- Result caching is impossible
- Agent cannot tell "operation ran twice" from "output varies naturally"
- Dry-run IDs are unusable for follow-up calls

### Solutions

**Sort all collections in output:**
```json
// Always sort arrays of objects by a stable key
{"users": [{"id": 1}, {"id": 2}, {"id": 3}]}

// Always sort string arrays lexicographically
{"permissions": ["admin", "delete", "read", "write"]}
```

**Separate volatile metadata from stable data:**
```json
{
  "ok": true,
  "data": {                          // stable — safe to cache/compare
    "status": "ok",
    "version": "1.2.3"
  },
  "meta": {                          // volatile — do not compare
    "checked_at": "2024-03-11T14:30:01Z",
    "duration_ms": 45,
    "request_id": "req-abc"
  }
}
```

**Deterministic dry-run IDs:**
```bash
# Dry-run preview ID derived from inputs, not random
preview_id = sha256(command + args + timestamp_truncated_to_minute)
# Same args within the same minute → same preview ID
```

**`--stable-output` flag:**
```bash
tool list-users --stable-output
# Sorts all collections, omits volatile fields (timestamps, durations)
# Output is deterministic for identical inputs
```

**For framework design:**
- All array fields sorted by default in `--output json` mode
- `data` and `meta` are top-level siblings; agents compare `data` only
- Dry-run IDs are content-addressed, not random
- Document which fields are volatile in the output schema (`"volatile": true`)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Array ordering varies between identical runs; timestamps embedded in top-level data fields |
| 1 | Some collections sorted but not all; timestamps in `data` alongside stable fields |
| 2 | All collections sorted stably; timestamps isolated in `meta`; output is reproducible for identical inputs |
| 3 | `--stable-output` flag omits all volatile fields; dry-run IDs are content-addressed; volatile fields documented in schema |

**Check:** Run the same read command twice in a row and diff the `data` fields — any ordering difference or timestamp change in `data` (not `meta`) is a failure.

---

### Agent Workaround

**Signature:** two identical read-only invocations produce different stdout: reordered arrays, changed timestamps, or fresh random IDs; diff is never empty

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Compare only the `data` field of the two outputs and ignore `meta`; if that fails, escalate with the command, exit code, stdout, and stderr

**Compare only `data`, never `meta`; extract specific fields rather than diffing full output:**

```python
def get_stable(cmd: list[str]) -> dict:
    result = subprocess.run([*cmd, "--output", "json"], capture_output=True, text=True)
    parsed = json.loads(result.stdout)
    # Only compare data — meta contains timestamps and request IDs
    return parsed.get("data", parsed)

# Detect changes correctly
before = get_stable(["tool", "get-status"])
after  = get_stable(["tool", "get-status"])
changed = before != after  # safe — meta excluded
```

**Sort collections before comparing if the tool doesn't:**
```python
import json

def normalize(obj):
    if isinstance(obj, list):
        return sorted([normalize(i) for i in obj], key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items())}
    return obj

before_norm = normalize(before)
after_norm  = normalize(after)
```

**Limitation:** If the tool embeds random IDs or timestamps directly in `data` fields (not `meta`) with no way to suppress them, deterministic comparison is impossible — extract and compare only the specific fields that represent meaningful state
