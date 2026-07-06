> **Part II: Execution & Reliability** | Challenge §12

## 12. Idempotency & Safe Retries

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

Agents retry on failure. If a command is not idempotent, retries cause duplicated side effects: double payments, duplicate records, multiple emails sent.

**Non-idempotent operations agents commonly retry:**
```bash
$ tool send-email --to user@example.com --subject "Welcome"
# Network timeout after sending
# Agent retries → duplicate email sent

$ tool create-order --amount 100
# Returns 503, agent retries → two orders created

$ tool increment-counter --key views
# Flaky network, agent retries 3x → counter incremented 3x
```

**Idempotency that's not communicated:**
```bash
$ tool deploy --version 1.2.3
# First run: deploys
# Second run: no-op (already at 1.2.3)
# But exits 0 both times with identical output
# Agent cannot tell if it deployed or was already up-to-date
```

### Impact

- Duplicate financial transactions, messages, records
- Agent cannot safely resume after failure
- State becomes inconsistent, hard to recover

### Solutions

**Idempotency keys:**
```bash
tool create-order --amount 100 --idempotency-key "order-$(date +%s)-$RANDOM"
# Server deduplicates based on key
# Safe to retry indefinitely
```

**Declare operation effect in output:**
```json
{
  "ok": true,
  "effect": "created",        // "created" | "updated" | "noop" | "deleted"
  "data": {"id": 42}
}
```

```json
{
  "ok": true,
  "effect": "noop",
  "reason": "Already at version 1.2.3",
  "data": {"current_version": "1.2.3"}
}
```

**`--dry-run` flag for all mutating commands:**
```bash
tool deploy --version 1.2.3 --dry-run
# Output:
{
  "ok": true,
  "effect": "would_create",
  "changes": ["would update service to 1.2.3", "would restart 2 instances"]
}
```

**For framework design:**
- Mark commands as `safe` (read-only, always idempotent) or `unsafe` (mutating)
- Require `--idempotency-key` for all `unsafe` commands, or generate one automatically
- Emit `effect` field in all responses
- Implement `--dry-run` as a framework-level feature, not per-command

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Mutating commands have no idempotency mechanism; retrying causes duplicate side effects |
| 1 | Some commands accept `--idempotency-key` but coverage is partial; no `effect` field in output |
| 2 | `--idempotency-key` on all mutating commands; `effect` field (`created`/`updated`/`noop`) in all responses |
| 3 | Idempotency enforced at framework level; `effect` in all responses; `--dry-run` available on all mutating commands |

**Check:** Call a mutating command twice with the same `--idempotency-key` — the second response must show `effect: "noop"` and exit 0 without duplicating the side effect.

---

### Agent Workaround

**Signature:** retrying a mutating command duplicates the side effect; repeat run exits `0` with output identical to the first, no `effect` field to tell deploy from no-op

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** do not retry the mutating command; escalate with the command, exit code, stdout, and stderr

**Generate a deterministic idempotency key per logical operation and check `effect` on retry:**

```python
import uuid, hashlib

def idempotency_key(operation: str, inputs: dict) -> str:
    # Stable key: same operation + same inputs → same key across retries
    payload = f"{operation}:{sorted(inputs.items())}"
    return hashlib.sha256(payload.encode()).hexdigest()[:32]

key = idempotency_key("create-order", {"amount": 100, "user": "alice"})

result = run(["tool", "create-order", "--amount", "100", "--idempotency-key", key])
parsed = json.loads(result.stdout)

if parsed.get("effect") == "noop":
    # Already completed — safe to treat as success
    pass
```

**Before retrying a failed mutating call, check whether the operation succeeded:**
```bash
# Query state before retrying — if already in target state, skip the mutation
tool get-order --id $ORDER_ID --json | jq '.data.status'
```

**Limitation:** If the tool provides no `effect` field and no idempotency key support, the agent cannot distinguish "already done" from "failed to do" — manually querying state before retry is the only safe approach, and it requires knowing which query to run
