> **Part II: Execution & Reliability** | Challenge §14

## 14. Argument Validation Before Side Effects

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Many CLI tools begin executing — creating files, sending requests, modifying state — before validating all their arguments. When validation fails mid-execution, the tool has already caused partial side effects that must be undone.

**Validation scattered through execution:**
```bash
$ tool deploy --env prod --version 1.2.3 --notify-slack "#invalid channel"
# Step 1: connect to prod ✓
# Step 2: deploy version 1.2.3 ✓  ← side effect happened
# Step 3: notify slack → Error: invalid channel name
exit 1
# Deployment happened, notification didn't. Partial success with exit 1.
# Agent sees failure, may retry → redeploys unnecessarily
```

**Required arg not validated until needed:**
```bash
$ tool backup --destination s3://my-bucket --encrypt --key-file /missing.pem
# Starts backup (writes 2GB to temp)
# Reaches encryption step → Error: key file not found
# 2GB of temp data must be cleaned up
# Wasted time, disk I/O, and the agent's turn budget
```

**Type validation only on use:**
```bash
$ tool process --workers "abc"
# Starts processing
# Spawns worker pool → Error: invalid literal for int(): 'abc'
# Work already partially started
```

### Impact

- Partial side effects on validation failure require manual cleanup
- Agent retries cause duplicate side effects (deploy ran twice)
- Wasted execution time before hitting a predictable error
- Error message points to validation issue, not the side effect that already occurred

### Solutions

**Two-phase execution: validate-then-execute:**
```python
def run(args):
    # Phase 1: validate ALL args before touching anything
    errors = validate(args)
    if errors:
        emit_validation_errors(errors)
        sys.exit(2)  # exit 2 = bad args, no side effects occurred

    # Phase 2: execute (side effects start here)
    execute(args)
```

**Validation result in structured output:**
```json
{
  "ok": false,
  "phase": "validation",          // side effects: none
  "errors": [
    {
      "param": "--key-file",
      "code": "FILE_NOT_FOUND",
      "message": "Key file '/missing.pem' does not exist",
      "value": "/missing.pem"
    },
    {
      "param": "--workers",
      "code": "TYPE_ERROR",
      "message": "Expected integer, got 'abc'",
      "value": "abc"
    }
  ]
}
```

**Preflight flag:**
```bash
tool deploy --env prod --version 1.2.3 --validate-only
# Runs all validation, reports errors, exits without deploying
# exit 0 = would succeed
# exit 2 = validation errors (listed in JSON)
```

**For framework design:**
- Framework enforces: all `@validate` hooks run before any `@execute` hooks
- Exit code `2` reserved exclusively for validation failures (no side effects)
- `--validate-only` is a framework-level flag available on all commands
- Validation errors always list all problems at once (not just the first one)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Validation fails mid-execution after side effects have occurred; exit 1 with text error |
| 1 | Most args validated upfront but some checked lazily; exit code not distinguished from execution failure |
| 2 | All args validated before execution; exit 2 for validation failures; structured error list |
| 3 | Exit 2 with structured JSON validation errors listing all problems at once; `--validate-only` flag available |

**Check:** Pass an invalid argument alongside a valid destructive flag — verify exit 2 is returned immediately with a JSON error, and that no side effect has occurred (no file created, no network call made).

---

### Agent Workaround

**Signature:** argument or type error (`invalid literal`, `not found`) appears only after progress output; `exit 1` not `exit 2`; side effects exist despite the bad argument

**Tier:** B (one observable check, then one command)

**Use `--validate-only` before executing mutating commands when available:**

```python
# Dry-run validation first — no side effects
validate_result = run([*cmd, "--validate-only"])
if validate_result.returncode == 2:
    errors = json.loads(validate_result.stdout).get("errors", [])
    # Fix argument errors before executing
    raise ValueError(f"Argument errors: {errors}")

# Only execute after validation passes
result = run(cmd)
```

**Detect validation failure by exit code:**
```python
result = run(cmd)
if result.returncode == 2:
    # Validation failure — no side effects occurred, safe to fix and retry
    parsed = json.loads(result.stdout)
    bad_params = [e["param"] for e in parsed.get("errors", [])]
elif result.returncode != 0:
    # Execution failure — side effects may have occurred, check state before retrying
    pass
```

**Limitation:** If the tool does not distinguish exit 2 (validation) from exit 1 (execution failure), the agent cannot safely determine whether a retry would cause duplicate side effects — treat any non-zero exit from a mutating command as potentially having caused partial side effects
