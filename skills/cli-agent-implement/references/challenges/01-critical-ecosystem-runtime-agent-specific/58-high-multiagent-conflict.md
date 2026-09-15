> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §58

## 58. Multi-Agent Concurrent Invocation Conflict

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Medium | **Time:** High | **Context:** Low

### The Problem

Distinct from §15 (race conditions within a single invocation), this is about multiple independent agent instances invoking the same CLI tool simultaneously against shared state: config files, credential caches, state databases. Neither agent knows about the other. Both read-modify-write the same config file, resulting in last-writer-wins corruption with no error reported.

```bash
# Agent A and Agent B run simultaneously:
# Agent A: tool config set region=us-east-1
# Agent B: tool config set environment=staging
# Both read config.json, write their change; last write overwrites the other.
# Both exit 0. Both think they succeeded. Config is corrupted.

# Auth token cache:
# Agent A refreshes token → old token invalidated
# Agent B still holds old token → all B's calls start failing with 401
```

### Impact

- Silent config corruption — both agents exit 0 but state is wrong
- Auth invalidation cascade — token refresh by one agent breaks all others
- No signal of the conflict; failure surfaces much later

### Solutions

**File locking for all config writes:**
```python
with framework.config_lock(timeout_ms=5000) as lock:
    config = lock.read()
    config['region'] = 'us-east-1'
    lock.write(config)
# If lock times out: exit 6 (conflict) with error.code: "CONCURRENT_MODIFICATION"
```

**Per-agent-instance state namespacing:**
```bash
$ tool --instance-id agent-1 config set region=us-east-1
# Writes to ~/.tool/instances/agent-1/config.json
```

**For framework design:**
- All config and state writes MUST use advisory file locking with configurable timeout (default 5s)
- Config writes MUST use atomic rename to prevent partial-write corruption
- Framework MUST provide `--instance-id <id>` to namespace all per-instance state so parallel agents operate without interference

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Config writes use no locking; parallel agents silently corrupt shared state; both exit 0 |
| 1 | Some file locking on config writes; no `--instance-id` for state namespacing; lock timeout not configurable |
| 2 | Advisory locking on all config writes; lock timeout emits `CONCURRENT_MODIFICATION` (exit 6) |
| 3 | `--instance-id` namespaces all per-instance state; atomic rename for config writes; `CONCURRENT_MODIFICATION` includes a `retry_after_ms` hint |

**Check:** Run two simultaneous `tool config set` calls and verify exactly one succeeds; the other should exit with `CONCURRENT_MODIFICATION` rather than silently overwriting.

---

### Agent Workaround

**Signature:** `exit 0` on a config write but a later read returns a different or missing value; auth calls suddenly fail with `401` after another session ran

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Pass a unique `--instance-id <id>` on every invocation to namespace state and do not retry conflicted config writes; if that fails, escalate with the command, exit code, stdout, and stderr

**Use `--instance-id` for state isolation; serialize config writes via an external lock; detect `CONCURRENT_MODIFICATION` errors:**

```python
import subprocess, json, uuid, os, time

# Use a stable instance ID for this agent session
INSTANCE_ID = os.environ.get("AGENT_INSTANCE_ID") or f"agent-{uuid.uuid4().hex[:8]}"

def config_set(key: str, value: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        result = subprocess.run(
            ["tool", "--instance-id", INSTANCE_ID, "config", "set",
             f"{key}={value}", "--output", "json"],
            capture_output=True, text=True,
        )
        parsed = json.loads(result.stdout)
        if parsed.get("ok"):
            return parsed

        error = parsed.get("error", {})
        if error.get("code") == "CONCURRENT_MODIFICATION":
            delay = error.get("retry_after_ms", 500) / 1000
            time.sleep(delay)
            continue

        raise RuntimeError(f"Config set failed: {parsed}")

    raise RuntimeError(f"Config set failed after {max_retries} retries due to conflicts")
```

**Namespace tool invocations to avoid shared state contamination:**
```python
# Always pass instance ID to isolate config/credential state per agent
result = subprocess.run(
    ["tool", "--instance-id", INSTANCE_ID, "auth", "switch", "--account", account],
    capture_output=True, text=True,
)
# This writes to ~/.tool/instances/{INSTANCE_ID}/auth.json
# Not to the shared ~/.tool/auth.json
```

**Limitation:** If the tool has no `--instance-id` flag and stores all state in a single shared file, parallel agent sessions will race — run only one agent session at a time on a given host, or use separate containers/home directories to provide filesystem isolation
