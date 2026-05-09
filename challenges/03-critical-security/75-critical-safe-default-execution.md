> **Part III: Security** | Challenge §75

## 75. Safe-Default Execution Mode Absent

**Severity:** Critical | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Low | **Time:** Critical | **Context:** Low

### The Problem

High-stakes commands (trading, infrastructure provisioning, mass data deletion) execute immediately with real side effects. Agents have no way to distinguish a preview invocation from a live one without an explicit `--dry-run` flag — which must be remembered at every callsite.

This is distinct from §23: `--dry-run` may be *available* (REQ-C-004), but its absence is a silent live run, not a safe default. An agent that omits `--dry-run` causes real impact with no warning.

**The unsafe default:**
```bash
$ trade execute --symbol BTC --amount 10000
# Immediately places a real order. No preview. No opt-in required.
```

**The confirmation-gate pattern (REQ-O-021) is also insufficient for this case:**
```bash
$ trade execute --symbol BTC --amount 10000
# Exits 2: CONFIRMATION_REQUIRED — agent must catch error and retry
```

The agent enters error-recovery flow instead of a natural preview → commit workflow.

**The gap: no canonical way to say "preview unless told otherwise":**
```bash
$ trade execute --symbol BTC --amount 10000         # preview by default, exit 0
$ trade execute --symbol BTC --amount 10000 --live  # opt into real execution
```

### Impact

- Agent places a real trade while intending to preview scope and cost
- Unrecoverable financial or infrastructure damage occurs in seconds
- Agent retry logic on transient errors may re-execute a live command that partially succeeded
- Each callsite must independently remember to pass `--dry-run` — a single omission causes harm

### Solutions

**Declare `safe_default: true` at command registration:**
```
register command "execute":
  danger_level: destructive
  safe_default: true   # dry-run is the default; --live opts into real execution
```

**Framework injects `--live` and enforces dry-run default:**
```bash
$ trade execute --symbol BTC --amount 10000
{
  "ok": true,
  "data": {
    "effect": "would_execute",
    "would_affect": {
      "order": { "symbol": "BTC", "side": "buy", "amount": 10000 },
      "estimated_cost_usd": 847230.00,
      "reversible": false
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "dry_run": true, "duration_ms": 42 }
}
```

```bash
$ trade execute --symbol BTC --amount 10000 --live
{
  "ok": true,
  "data": { "effect": "executed", "order_id": "ord_abc123" },
  "error": null,
  "warnings": [],
  "meta": { "dry_run": false, "confirmed": true, "duration_ms": 381 }
}
```

**`--schema` and manifest expose `safe_default`:**
```json
{
  "command": "execute",
  "danger_level": "destructive",
  "safe_default": true,
  "flags": {
    "live": {
      "type": "boolean",
      "default": false,
      "description": "Execute for real; omit to preview scope without side effects"
    }
  }
}
```

**For framework design:**
- Commands declare `safe_default: true` to activate this mode
- Framework registers `--live` (not `--dry-run`) as the opt-in flag — the name signals positive intent
- Without `--live`, the framework routes all execution through the dry-run path
- `meta.dry_run` is always present in the response envelope
- `safe_default` is exposed in the manifest so agents can detect it programmatically

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | High-stakes commands execute immediately with no dry-run default; `safe_default` not declared |
| 1 | `--dry-run` is available but opt-in; no `safe_default` mode; default is live execution |
| 2 | Commands support `safe_default: true`; framework injects `--live`; dry-run exits 0 with `would_*` effect |
| 3 | `safe_default` declared in manifest; `meta.dry_run` always present; agent can detect and enforce safe-default mode programmatically |

**Check:** Invoke a `safe_default: true` command without any flags — verify it returns a `would_*` effect, exits 0, and causes no side effects. Then invoke with `--live` — verify the effect field lacks the `would_` prefix and `meta.dry_run` is `false`.

---

### Agent Workaround

**Check `safe_default` in the manifest before calling:**
```python
manifest = json.loads(run(["tool", "manifest"]).stdout)
cmd = next(c for c in manifest["commands"] if c["name"] == "execute")

if cmd.get("safe_default"):
    # Natural preview → commit workflow
    preview = run(cmd_args)                      # dry-run by default
    verify_scope(json.loads(preview.stdout))
    result = run([*cmd_args, "--live"])
else:
    # No safe-default mode — pass --dry-run explicitly at every callsite
    preview = run([*cmd_args, "--dry-run"])
    verify_scope(json.loads(preview.stdout))
    result = run([*cmd_args, "--confirm-destructive"])
```

**If the tool supports neither `safe_default` nor `--dry-run`:**
```python
# No preview path exists — require human authorization before proceeding
require_human_approval(cmd_info)
```

**Limitation:** If the tool neither declares `safe_default` nor supports `--dry-run`, the agent cannot preview impact — do not invoke high-stakes commands speculatively in any automated flow
