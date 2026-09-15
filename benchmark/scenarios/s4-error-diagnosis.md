# S4 — Diagnose a Failure

**Challenge cluster:** Error quality, structured errors, credential expiry
**Key requirements:** C-013, C-014, F-037, F-063, F-001

## Task given to agent

> "Run the health check and tell me what's wrong if it fails."

## Expected answer

`{"issue": "credentials_expired", "service": "registry", "action": "re-authenticate with: auth login --service registry"}`

The health check fails because the registry credential has expired.

## Why this stresses the spec

**cli-bad:** Returns `exit 1` and prints a multi-line error to stderr mixed with warning prose. The agent must parse unstructured text to determine the root cause. It may misidentify the error type and suggest the wrong remediation.

**cli-good:** Returns `exit 8` (`AUTH_REQUIRED`) with `error.code: "TOKEN_EXPIRED"` and `error.context: {"service": "registry", "expired_at": "..."}`. The agent reads the structured fields directly and produces the correct answer in one step.

## CLI commands exercised

```bash
# bad
health check
# returns: exit 1, stderr: "WARN: cache stale\nERROR: registry auth failed: token expired 2h ago\nINFO: 3 services checked"

# good
health check --output json
# returns: exit 8, {"ok":false,"error":{"code":"TOKEN_EXPIRED","retryable":false,"context":{"service":"registry","expired_at":"..."}},"meta":{"exit_code":8,...}}
```

## Measured delta hypothesis

| Metric | Expected direction |
|--------|--------------------|
| `total_tokens` | bad > good (prose parsing + reasoning vs structured read) |
| `api_calls` | bad >= good |
| `success` | bad < good (prose misparse leads to wrong diagnosis) |
