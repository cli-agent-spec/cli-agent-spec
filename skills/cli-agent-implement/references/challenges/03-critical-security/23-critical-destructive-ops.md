> **Part IV: Security** | Challenge §23

## 23. Side Effects & Destructive Operations

**Severity:** Critical | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** High | **Context:** Medium

### The Problem

Agents may execute destructive commands without fully understanding consequences, especially when operating autonomously or when command names are ambiguous.

**Ambiguous destructive commands:**
```bash
$ tool clean          # Does it clean temp files? Or delete all data?
$ tool reset          # Reset config? Or wipe the database?
$ tool update         # Update records? Update the tool itself?
$ tool sync --force   # What does force do exactly?
```

**No indication of destructive nature:**
```bash
$ tool deploy --env prod --strategy rolling
# Starts replacing production instances
# No warning, no confirmation, no dry-run output
```

**Irreversible operations without warning:**
```bash
$ tool delete-account --user 42
Deleted.
# No warning that this is permanent, no audit log, no --dry-run available
```

### Impact

- Agent causes unintended data loss in production
- No recovery path after irreversible operation
- Hard to audit what happened and when

### Solutions

**Explicit destructive flag:**
```bash
tool delete-account --user 42 --confirm-destructive
# Without the flag: exits with clear error explaining the flag is required
```

**Machine-readable danger level in help:**
```json
{
  "command": "delete-account",
  "danger_level": "destructive",   // "safe" | "mutating" | "destructive"
  "reversible": false,
  "requires_confirmation": true
}
```

**Dry-run always available for destructive commands:**
```bash
$ tool delete-account --user 42 --dry-run
{
  "ok": true,
  "effect": "would_delete",
  "would_affect": {
    "user": {"id": 42, "name": "Alice"},
    "related_records": 234,
    "reversible": false
  }
}
```

**Audit output:**
```json
{
  "ok": true,
  "effect": "deleted",
  "audit": {
    "timestamp": "2024-03-11T14:30:00Z",
    "operator": "agent-session-abc123",
    "target": {"type": "user", "id": 42},
    "reversible": false
  }
}
```

**For framework design:**
- Commands declare `danger_level` in their schema
- Framework enforces `--dry-run` availability for all `destructive` commands
- `--yes` / `--confirm-destructive` flags auto-supplied by agent harness
- Generate audit log entries for all `mutating` and `destructive` operations

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Destructive commands execute without confirmation and provide no `--dry-run`; `danger_level` not declared |
| 1 | Confirmation prompt or `--yes` flag exists; no `--dry-run`; `danger_level` not machine-readable |
| 2 | `--dry-run` available on all destructive commands; `danger_level` declared in manifest; `effect` field in output |
| 3 | `--confirm-destructive` enforced at framework level; audit output with `operator`, `timestamp`, and `reversible`; `--dry-run` shows exact affected scope |

**Check:** Run a destructive command with `--dry-run` — verify it returns `effect: "would_delete"` (or equivalent) with the affected scope, exits 0, and causes no side effects.

---

### Agent Workaround

**Signature:** destructive-sounding command (`delete`, `reset`, `purge`) exits `0` with terse output (`Deleted.`); `--dry-run` rejected as unknown flag

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Do not run further destructive commands; escalate with the command, exit code, stdout, and stderr

**Always run `--dry-run` before executing destructive commands:**

```python
# Step 1: inspect what would be affected
dry = run([*cmd, "--dry-run"])
parsed = json.loads(dry.stdout)
scope = parsed.get("would_affect") or parsed.get("changes") or parsed.get("data")

# Step 2: confirm scope is expected before executing
if not scope_is_acceptable(scope):
    raise RuntimeError(f"Scope too broad: {scope}")

# Step 3: execute with explicit confirmation flag
result = run([*cmd, "--confirm-destructive"])
```

**Check `danger_level` in the tool manifest before calling:**
```python
manifest = json.loads(run(["tool", "manifest"]).stdout)
cmd_info = next(c for c in manifest["commands"] if c["name"] == "delete-account")
if cmd_info.get("danger_level") == "destructive":
    # Require explicit human approval or policy check before proceeding
    require_approval(cmd_info)
```

**Limitation:** If the tool provides neither `--dry-run` nor `danger_level` in its manifest, the agent has no reliable way to preview impact before executing — treat any command with "delete", "reset", "clean", "purge", or "wipe" in its name as potentially destructive and apply extra caution
