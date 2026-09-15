# S2 — Deploy with Conflict

**Challenge cluster:** Exit codes, retry safety, idempotency
**Key requirements:** F-001, F-002, C-001, C-013, C-014, C-007

## Task given to agent

> "Deploy version 2.1.0 of the app to staging. If it fails, retry until it succeeds or you're sure it can't."

## Expected answer

`{"status": "deployed", "version": "2.1.0", "env": "staging"}`

The first call returns a conflict error (another deploy is in progress). The second call (after the conflict clears) succeeds.

## Why this stresses the spec

**cli-bad:** First call returns `exit 1` and prints "Error: deployment locked". The agent does not know if this is retryable, if the previous call had side effects, or how long to wait. It either gives up, retries immediately (causing another conflict), or spends tokens asking for clarification.

**cli-good:** First call returns `exit 4` with `error.code: "LOCK_HELD"`, `retryable: true`, and `retry_after_ms: 2000` (REQ-F-033). Retryable implies no side effects. The agent waits 2 seconds and retries with the same `--idempotency-key`. Zero ambiguity, zero extra token spend on diagnosis.

## CLI commands exercised

```bash
# bad
deploy --version 2.1.0 --env staging
# returns: exit 1, "Error: deployment locked"

# good
deploy --version 2.1.0 --env staging --idempotency-key bench-001 --output json
# returns: exit 4, {"ok":false,"error":{"code":"LOCK_HELD","retryable":true,"retry_after_ms":2000},"meta":{"exit_code":4,...}}
# second call: exit 0, {"ok":true,"data":{"status":"deployed",...},"meta":{"exit_code":0,...}}
```

## Measured delta hypothesis

| Metric | Expected direction |
|--------|--------------------|
| `total_tokens` | bad >> good (diagnosis loop vs structured retry hint) |
| `api_calls` | bad > good (extra calls to reason about the error) |
| `steps` | bad > good |
| `time_ms` | bad > good (extra reasoning before retry) |
