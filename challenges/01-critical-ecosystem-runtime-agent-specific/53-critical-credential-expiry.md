> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §53

## 53. Credential Expiry Mid-Session

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Low

### The Problem

Agents often operate over sessions longer than credential lifetimes. Short-lived IAM roles (15min), JWTs (1hr), API keys (rotated by policy), and OAuth access tokens (1hr) may expire mid-task. When they do, commands start failing with 401/403, but error messages typically say "unauthorized" or "access denied" — identical to "never had permission" errors. The agent cannot distinguish "credential was never valid" (permanent failure requiring escalation) from "credential expired" (transient failure recoverable by refresh).

```bash
# Session starts — IAM role valid for 15 minutes
$ tool deploy --env prod
{"ok": true, "data": {"job_id": "dep_123"}}

# 16 minutes later
$ tool job status dep_123
{"ok": false, "error": {"code": "FORBIDDEN", "message": "Access denied"}}
# Is this: token expired? wrong permissions? job doesn't exist?
# Agent cannot tell. May retry (burns time), may abort (wrong call).

# Worse: cascade failure — every subsequent call also fails
$ tool list-resources
{"ok": false, "error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}}
```

### Impact

- Agent retries indefinitely on a non-retryable permanent permission denial
- Agent abandons a recoverable expired-token situation that just needs a refresh
- Cascading failures across all subsequent commands in the session
- Agent may attempt rollback with the same expired credential, causing rollback to also fail

### Solutions

**Auth errors MUST distinguish expiry from permission denial:**
```json
{
  "ok": false,
  "error": {
    "code": "CREDENTIALS_EXPIRED",
    "message": "Access token expired at 2024-03-11T14:15:00Z.",
    "expired": true,
    "expired_at": "2024-03-11T14:15:00Z",
    "retryable": false,
    "fix_required": "Refresh credentials, then reissue",
    "reauth_command": "tool auth refresh",
    "reauth_env_var": "TOOL_TOKEN"
  }
}
```

**For framework design:**
- Use the standard exit code table: expiry emits `AUTH_REQUIRED (8)` with `error.code: CREDENTIALS_EXPIRED` (recoverable by refresh); permanent denial emits `PERMISSION_DENIED (7)`
- Framework MUST intercept HTTP 401/403 responses and attempt to classify expiry vs permission denial before surfacing the error
- `error.reauth_command` is a mandatory field for all auth errors — the exact command to run to recover credentials

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Expired credentials produce `FORBIDDEN` or `UNAUTHORIZED` identical to permission denial; no way to distinguish; no reauth hint |
| 1 | Error message mentions "expired" in human-readable text; no structured `expired` field; `reauth_command` absent |
| 2 | `CREDENTIALS_EXPIRED` code distinct from `PERMISSION_DENIED`; `expired_at` field present; `reauth_command` provided |
| 3 | Exit code 8 (expiry, `error.code: CREDENTIALS_EXPIRED`) distinct from exit 7 (permanent denied); `reauth_command` on expiry errors; `reauth_env_var` listed |

**Check:** Let credentials expire (or mock expiry) and run any authenticated command — verify the response contains `"code": "CREDENTIALS_EXPIRED"` (not `FORBIDDEN`) and a `reauth_command` field.

---

### Agent Workaround

**Signature:** commands that succeeded earlier in the session start failing with `UNAUTHORIZED`/`FORBIDDEN` or `401`/`403`; every subsequent call fails the same way

**Tier:** B (one observable check, then one command)

**Distinguish `CREDENTIALS_EXPIRED` from permanent auth failures; auto-refresh when `reauth_command` is provided:**

```python
import subprocess, json, os

CREDENTIAL_EXPIRY_CODES = {"CREDENTIALS_EXPIRED", "AUTH_EXPIRED", "TOKEN_EXPIRED"}
PERMANENT_AUTH_CODES = {"PERMISSION_DENIED", "FORBIDDEN", "UNAUTHORIZED"}

def run_with_auth_retry(cmd: list[str], max_auth_retries: int = 1) -> dict:
    for attempt in range(max_auth_retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"No JSON output: {result.stdout[:200]}")

        if parsed.get("ok"):
            return parsed

        error = parsed.get("error", {})
        code = error.get("code", "")

        if code in CREDENTIAL_EXPIRY_CODES and attempt < max_auth_retries:
            reauth_cmd = error.get("reauth_command")
            reauth_env = error.get("reauth_env_var")
            if reauth_cmd:
                # Run the reauth command
                reauth_result = subprocess.run(
                    reauth_cmd.split(), capture_output=True, text=True
                )
                if reauth_result.returncode == 0:
                    continue   # retry the original command
            elif reauth_env:
                raise RuntimeError(
                    f"Credentials expired. Re-set {reauth_env} to refresh."
                )
            raise RuntimeError(f"Credentials expired and no reauth path available: {error}")

        if code in PERMANENT_AUTH_CODES:
            raise PermissionError(f"Permanent auth failure [{code}]: {error.get('message')}")

        raise RuntimeError(f"Command failed: {parsed}")

    raise RuntimeError("Auth retry limit reached")
```

**Limitation:** If the tool does not distinguish expiry from permission denial (both use `FORBIDDEN` or `UNAUTHORIZED`), the agent cannot safely auto-retry — check the `expired_at` field if available; if absent, treat all 401/403 as non-retryable to avoid infinite retry loops
