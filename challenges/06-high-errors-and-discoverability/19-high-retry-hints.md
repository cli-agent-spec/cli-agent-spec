> **Part III: Errors & Discoverability** | Challenge §19

## 19. Retry Hints in Error Responses

**Severity:** High | **Frequency:** Very Common | **Detectability:** Medium | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

When a command fails, the agent decides: retry immediately, retry after delay, retry with different args, or give up. Without explicit guidance, agents either retry everything (wasting resources, amplifying rate-limit violations) or give up on recoverable failures.

**Agent retrying a non-retryable error:**
```bash
$ tool create-user --email "not-an-email"
{"ok": false, "error": {"code": "VALIDATION_ERROR", "message": "Invalid email"}}
exit 1

# Agent retries 3 times with identical args
# Each retry fails identically — wasted calls, wasted tokens
```

**Agent giving up on a retryable error:**
```bash
$ tool call-api
{"ok": false, "error": {"code": "SERVICE_UNAVAILABLE", "message": "Try again later"}}
exit 1

# Agent marks task as failed and escalates to user
# But the service recovered 2 seconds later
```

**Rate limit with no backoff hint:**
```bash
$ tool sync-data
{"ok": false, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}}
exit 11

# Agent retries immediately → hits rate limit again → retry loop
```

### Impact

- Retry amplifies the original problem (rate limits, load)
- No-retry on recoverable failures wastes the entire task
- Agent cannot distinguish "try again" from "fix your args first"

### Solutions

**`retryable` and `retry_after_ms` in every error:**
```json
{
  "ok": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "API rate limit exceeded",
    "retryable": true,
    "retry_after_ms": 5000,
    "retry_strategy": "exponential_backoff",
    "max_retries": 3
  }
}
```

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email address",
    "retryable": false,
    "fix_required": "Correct the --email argument before retrying"
  }
}
```

**Retry classification taxonomy:**
```
retryable: false → VALIDATION_ERROR, NOT_FOUND, PERMISSION_DENIED, CONFLICT
                   (fix-then-retry cases carry fix_required with the correction)
retryable: true  → TIMEOUT, SERVICE_UNAVAILABLE, RATE_LIMITED, NETWORK_ERROR
INTERNAL_ERROR   → retryable: false by default; a command may declare it true
                   when the failure is known to be transient
```

**Exit code alignment:**
```
Exit 11 (RATE_LIMITED)      → retryable, wait error.retry_after_ms
Exit 12 (UNAVAILABLE)       → retryable, exponential back-off
Exit 10 (TIMEOUT)           → retryable only when the command declares
                              side_effects: "none" for TIMEOUT
Exit 7 (PERMISSION_DENIED)  → never retryable without auth change
Exit 2 (ARG_ERROR)          → never retryable without arg change
```

**For framework design:**
- Every error class has a default `retryable` value in the error registry
- `retry_after_ms` sourced from response header (Retry-After) when available
- Framework-level retry logic: honor `retryable` and `retry_after_ms` automatically
- Emit `attempt` and `max_attempts` in `meta` so agents know retry history

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No `retryable` field; agent cannot distinguish transient from permanent failures; no delay hint for rate limits |
| 1 | Some errors include `retryable`; `retry_after_ms` absent; agent must guess delay |
| 2 | All errors include `retryable: true/false`; rate-limited responses include `retry_after_ms`; exit code encodes retryability |
| 3 | `retry_strategy` field present; `max_retries` hint provided; `meta.attempt` and `meta.max_attempts` track retry history |

**Check:** Trigger a rate-limit error (or a validation error) and verify the response includes `retryable: true` (or `false`) and, for rate limits, a `retry_after_ms` value.

---

### Agent Workaround

**Signature:** error output lacks `retryable` and `retry_after_ms`; immediate retry after `RATE_LIMITED` fails again; identical retries fail identically

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Retry once after a 1 s back-off only if the command is read-only, never if it mutates; if that fails, escalate with the command, exit code, stdout, and stderr

**Implement retry logic driven by `retryable` and `retry_after_ms` fields:**

```python
import subprocess, json, time

def run_with_retry(cmd: list[str], max_attempts: int = 3) -> dict:
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            if attempt == max_attempts:
                raise
            time.sleep(2 ** attempt)
            continue

        if parsed.get("ok"):
            return parsed

        error = parsed.get("error", {})
        retryable = error.get("retryable")

        if retryable is False:
            # Permanent failure — do not retry
            raise RuntimeError(
                f"[{error.get('code')}] {error.get('message')} "
                f"(fix: {error.get('fix_required', 'see error')})"
            )

        if retryable is True and attempt < max_attempts:
            delay_ms = error.get("retry_after_ms", 1000 * (2 ** attempt))
            time.sleep(delay_ms / 1000)
            continue

        raise RuntimeError(f"Command failed after {attempt} attempts: {parsed}")

    raise RuntimeError("Max attempts reached")
```

**Map exit codes to retry decisions when `retryable` field is absent:**
```python
# Exit codes that are retryable per the spec's standard table
# (10 = TIMEOUT is only safe when the command declares side_effects: "none")
RETRYABLE_EXIT_CODES = {10, 11, 12}  # TIMEOUT, RATE_LIMITED, UNAVAILABLE
# Exit codes that are never retryable without changing something first
PERMANENT_EXIT_CODES = {2, 3, 5, 6, 7}  # ARG_ERROR, PARTIAL_FAILURE, NOT_FOUND, CONFLICT, PERMISSION_DENIED

if result.returncode in RETRYABLE_EXIT_CODES:
    time.sleep(5)
    # retry
elif result.returncode in PERMANENT_EXIT_CODES:
    raise RuntimeError("Permanent failure — do not retry")
```

**Limitation:** If the tool provides no `retryable` field and uses exit code 1 for all failures (both permanent and transient), the agent cannot safely distinguish them — apply the default retry policy from `triage.md` (one retry for read-only commands, none for mutations) and treat unknown errors as non-retryable after the final attempt
