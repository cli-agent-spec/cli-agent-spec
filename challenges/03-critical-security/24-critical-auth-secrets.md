> **Part IV: Security** | Challenge §24

## 24. Authentication & Secret Handling

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

CLI tools often need credentials. How they receive, store, and expose those credentials determines whether agents can use them safely without leaking secrets into logs or context windows.

**Secrets in arguments (worst pattern):**
```bash
$ tool connect --password "supersecret"
# Appears in: ps aux, shell history, logs, agent context window
```

**Secrets in output:**
```bash
$ tool create-api-key --name "my-key"
API Key created: sk-prod-abc123xyz789
Store this somewhere safe, it won't be shown again.
# The secret is now in the agent's context window and any logs
```

**Secrets in error messages:**
```bash
$ tool connect --token $TOKEN
Error: Invalid token: "Bearer abc123xyz" — expected format: "Token sk-..."
# Token value echoed in error, ends up in logs
```

**Credential prompts in non-interactive mode:**
```bash
$ tool deploy
Enter API token:
# Hangs, or reads empty string, or fails with no explanation
```

### Impact

- Credentials exposed in agent context window → may be logged or transmitted
- Credentials in shell history → leaked via history files
- Credentials in error messages → leaked in log aggregation systems

### Solutions

**Prefer environment variables:**
```bash
TOOL_API_TOKEN=sk-... tool deploy
# Convention: TOOL_VARNAME
```

**Support secrets files:**
```bash
tool deploy --token-file /run/secrets/api-token
# File path, not the value
```

**Never echo secrets in output or errors:**
```json
// Bad
{"error": "Invalid token: sk-prod-abc123xyz789"}

// Good
{"error": {"code": "AUTH_TOKEN_INVALID", "message": "Token is invalid or expired"}}
```

**Secret output handling:**
```json
{
  "ok": true,
  "data": {
    "key_id": "key-42",          // safe to log
    "key_preview": "sk-prod-abc...xyz",  // truncated
    "secret": "REDACTED"          // never return in --output json
  },
  "secret_written_to": "/run/secrets/key-42"  // written to file instead
}
```

**For framework design:**
- Framework-level redaction: any field named `*token*`, `*secret*`, `*password*`, `*key*` is auto-redacted in logs
- Provide `--secret-from-env VAR_NAME` and `--secret-from-file PATH` as standard flags
- Document which env vars each command reads for credentials

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Secrets accepted via CLI args (`--password`, `--token`); error messages echo token values; credential prompts hang non-TTY |
| 1 | Env var alternative exists but `--password`/`--token` flags still accepted; some secrets echo in errors |
| 2 | Only env vars and file paths accepted for secrets; secrets never echoed in error messages or output |
| 3 | Framework auto-redacts `*token*/*secret*/*password*/*key*` fields in all output and logs; `--secret-from-env` and `--secret-from-file` are standard flags |

**Check:** Invoke a command with an intentionally invalid credential — verify the error message contains the error code but not the credential value, and exits with a defined auth error code (exit 8 or 10).

---

### Agent Workaround

**Signature:** stdout or stderr echoes a credential value (`sk-...`, `Bearer ...`); non-TTY run hangs at a prompt like `Enter API token:`

**Tier:** B (one observable check, then one command)

**Always supply credentials via environment variables, never via flags:**

```python
import os, subprocess

env = {
    **os.environ,
    "TOOL_API_TOKEN": secret_value,   # set in env, not in argv
}

result = subprocess.run(
    ["tool", "deploy"],               # no --token flag
    env=env,
    capture_output=True,
    text=True,
)
```

**Scan output for accidental secret leakage before logging:**
```python
import re

SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',          # OpenAI-style keys
    r'Bearer [a-zA-Z0-9\-._~+/]+=*', # Bearer tokens
    r'[A-Za-z0-9+/]{40,}={0,2}',     # Long base64 (API keys)
]

def contains_secret(text: str) -> bool:
    return any(re.search(p, text) for p in SECRET_PATTERNS)

if contains_secret(result.stdout):
    raise RuntimeError("Tool output contains what appears to be a secret — not logging")
```

**Limitation:** If the tool echoes credential values in error messages (e.g., "Invalid token: sk-abc123"), there is no agent-side fix — the secret is already in the captured output; avoid logging or including raw tool output in any persistent store when working with auth-related commands
