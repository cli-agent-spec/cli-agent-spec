> **Part I: Output & Parsing** | Challenge §1

## 1. Exit Codes & Status Signaling

**Severity:** Critical | **Frequency:** Very Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Low

### The Problem

The most fundamental contract between a CLI tool and its caller is the exit code. Agents treat exit code `0` as success and anything else as failure — but many tools break this contract in ways that silently mislead the agent.

**Violations agents encounter constantly:**

```bash
# Tool exits 0 but operation failed
$ my-deploy --env prod
Warning: config file not found, using defaults
Deploying... timeout after 30s
$ echo $?
0   # ← agent thinks this succeeded
```

```bash
# Tool exits non-zero on non-error conditions
$ grep "pattern" file.txt
$ echo $?
1   # grep exits 1 when no match found — not an error, just "not found"
    # agent may treat this as a failure and retry or abort
```

```bash
# Inconsistent exit codes across versions
$ tool --version
v1.x: exit 0 on warning, exit 1 on error
v2.x: exit 2 on warning, exit 1 on error
# agent cannot reliably interpret without knowing version
```

**Multi-step commands that mask failures:**
```bash
cmd1 && cmd2 && cmd3
# if cmd2 fails, the shell exits with cmd2's code
# but the agent only sees the final code and doesn't know which step failed
```

### Impact

- Agent retries a succeeded operation (token waste, possible duplication)
- Agent proceeds after a failed operation (data corruption, cascading errors)
- Agent enters a retry loop on a "failure" that is actually expected behavior

### Solutions

**For CLI tool authors:**
```
Exit code conventions to follow (the spec's standard table, REQ-F-001):
  0  = success, operation completed as intended
  1  = general error (use sparingly — be specific)
  2  = misuse / bad arguments (before operation starts)
  3  = operation started but failed mid-way
  4  = precondition not met (dependency missing, not initialized)
  5  = not found (the thing you asked about doesn't exist)
  6  = conflict / already exists
  7  = permission denied
  8  = auth required (credentials missing, invalid, or expired)
  9  = payment required
  10 = timeout
  11 = rate limited / quota exceeded
```

**Separate "not found" from "error":**
```bash
# Bad: exits 1 for both "error" and "not found"
tool get-user --id 123
# exit 1

# Good: exits 5 for "not found", 1 for actual errors
tool get-user --id 123
# exit 5  ← agent knows to stop, not retry
```

**For CLI framework design:**
- Define a standard exit code table in your framework
- Provide typed exit code constants (not magic numbers)
- Make every command document its possible exit codes in `--help`
- Support `--exit-on-warning` flag to make strict mode opt-in

---

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Binary `0`/`1` only — all failures exit `1`, no semantic distinction |
| 1 | Some semantic codes used but undocumented or inconsistent across commands |
| 2 | Named codes covering success / validation / not-found / timeout / permission; documented in `--help`; consistent across all commands |
| 3 | Full declared exit code table; exit code embedded in JSON error body (`"exit_code": N`); each command declares its possible codes in the tool manifest |

**Check:** Run the tool with missing required args, a nonexistent resource ID, and a simulated network failure. Confirm exit codes are distinct, documented, and match the JSON error body.

---

### Agent Workaround

**Signature:** `exit 0` while output contains `Error`, `Warning`, `failed`, or `timeout`; or the same `exit 1` for unrelated failures and empty results

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Do not retry; when stdout parses as a JSON envelope trust its `ok` field over the exit code; otherwise escalate with the command, exit code, stdout, and stderr

**When exit codes are not semantic, branch on the JSON envelope instead:**

```python
import subprocess, json

result = subprocess.run(cmd, capture_output=True)

# 1. Never assume exit 0 means the operation succeeded
if result.returncode == 0:
    data = json.loads(result.stdout)
    if not data.get("ok"):
        handle_logical_failure(data["error"])  # tool exited 0 but reported failure

# 2. Map known semantic codes when available
elif result.returncode == 2:
    raise ValidationError()       # fix input, do not retry as-is

elif result.returncode == 5:
    raise NotFoundError()         # stop, do not retry

elif result.returncode == 11:
    retry_after_ms = extract_retry_after_ms(result.stdout)  # error.retry_after_ms
    time.sleep((retry_after_ms or 60_000) / 1000)  # rate-limited — back off

# 3. Fallback: parse stdout/stderr for error details
else:
    try:
        err = json.loads(result.stdout or result.stderr)
    except Exception:
        err = {"message": result.stderr.decode(errors="replace")}
    raise NonRetryableError(err)  # unknown code — default to no-retry
```

**Limitation:** Without semantic exit codes the agent must parse error text to decide retry safety — unreliable across versions and locales
