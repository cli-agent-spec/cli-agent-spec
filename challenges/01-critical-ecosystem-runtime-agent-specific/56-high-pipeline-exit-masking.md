> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §56

## 56. Exit Code Masking in Shell Pipelines

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Low | **Context:** Low

### The Problem

When a CLI tool is used in a shell pipeline (`tool | jq '.data[]'`), the shell reports the exit code of the *last* command — `jq` — not the tool. If `tool` fails with exit 1 but outputs a valid JSON error envelope (which `jq` happily parses), `jq` exits 0. The agent sees `exit 0` and empty output, interprets this as "the command succeeded but returned no results."

```bash
# Agent runs: tool list-users | jq '.data[].id'
#
# tool exits 1 (rate limited), outputs:
# {"ok": false, "error": {"code": "RATE_LIMITED"}}
#
# jq parses this, finds no .data[].id, exits 0, outputs nothing
#
# Agent sees: exit 0, empty output → "no users exist"
# Correct interpretation: rate limited, retry after backoff

# Fix requires pipefail — but agents can't guarantee it's set:
set -o pipefail
tool list-users | jq '.data[].id'
```

### Impact

- Failed operations silently appear as successes (empty result set)
- Rate limits, auth failures, and partial errors all masked as "zero results"
- Requires `pipefail` shell option which agents cannot guarantee

### Solutions

**Primary defense: check `.ok` in the JSON envelope, not only the exit code:**
```bash
result=$(tool list-users)
echo "$result" | jq -e '.ok' > /dev/null || { echo "$result" | jq '.error'; exit 1; }
echo "$result" | jq '.data[].id'
```

**`meta.ok` mirrors top-level `ok` for pipeline detection:**
```json
{"ok": false, "meta": {"ok": false, "exit_code": 9}, "error": {...}}
```

**For framework design:**
- Document prominently: agents MUST check `.ok` in the JSON envelope, not only the exit code, when piping
- Framework SHOULD write `TOOL_FAILED=1` to stderr on failure so pipeline callers can detect failure without `pipefail`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Failures masked to exit 0 when piped through `jq` or similar; agent cannot detect failure without `pipefail` |
| 1 | `ok` field present in response but no `meta.ok` mirror; pipeline detection requires application-layer check |
| 2 | `meta.ok` mirrors top-level `ok`; `meta.exit_code` present; agent can detect failure by checking JSON before piping |
| 3 | Framework writes `TOOL_FAILED=1` to stderr on failure; `meta.ok` and `meta.exit_code` in every response |

**Check:** Chain `tool list-users | jq '.data[].id'` where the tool is rate-limited — verify that with `set -o pipefail` or by checking the JSON first, the failure is detectable.

---

### Agent Workaround

**Signature:** pipeline exits `0` with empty output; running the tool alone exits non-zero and prints a JSON error envelope with `"ok": false`

**Tier:** B (one observable check, then one command)

**Never pipe structured output directly; always capture and check `.ok` before extracting fields:**

```python
import subprocess, json

# NEVER:  result = subprocess.run(["tool list-users | jq '.data[].id'"], shell=True)
# ALWAYS: capture first, check ok, then extract

result = subprocess.run(
    ["tool", "list-users", "--output", "json"],
    capture_output=True, text=True,
    stdin=subprocess.DEVNULL,
)

try:
    parsed = json.loads(result.stdout)
except json.JSONDecodeError:
    raise RuntimeError(f"Tool produced non-JSON: {result.stdout[:200]}")

# Check ok BEFORE extracting data — exit code alone is unreliable in pipelines
if not parsed.get("ok"):
    error = parsed.get("error", {})
    raise RuntimeError(f"[{error.get('code')}] {error.get('message')}")

# Now safe to extract
user_ids = [u["id"] for u in parsed.get("data", {}).get("users", [])]
```

**When shell pipelines are unavoidable, use `set -o pipefail`:**
```bash
#!/bin/bash
set -eo pipefail
RESULT=$(tool list-users --output json)
echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if not d['ok']: sys.exit(d['error']['code'])
for u in d['data']['users']: print(u['id'])
"
```

**Limitation:** `set -o pipefail` is not supported in all shells (not POSIX); in portable scripts, always capture to a variable first and check `.ok` before piping to downstream processors
