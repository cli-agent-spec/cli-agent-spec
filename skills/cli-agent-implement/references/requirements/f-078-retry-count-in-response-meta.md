# REQ-F-078: Retry Count in Response Meta

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** Silent assumption — agents set `--timeout` expecting it to bound total elapsed time; tools that retry internally multiply the timeout budget invisibly and expose the agent's outer retry loop to double-retry

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

When the framework performs internal retries (network calls, lock acquisition, transient error recovery), it MUST report the retry count in the response `meta` block. This allows agents to:

1. Detect that retries occurred and attribute latency correctly
2. Avoid double-retrying: if the tool already retried 3 times internally, the agent's outer retry loop should not retry again
3. Diagnose flakiness: persistent internal retries indicate an infrastructure issue worth surfacing

The framework MUST also expose `--retries` and `--retry-delay` flags so agents can control the internal retry budget explicitly.

## Acceptance Criteria

- Any response from a command that performed ≥1 internal retry includes `"retries": N` in `meta`
- `"retries": 0` is omitted (not included) when no retries occurred, to avoid noise
- `--retries 0` disables all internal retries; the command fails immediately on first error
- `--retries N --retry-delay 500ms` sets the retry budget; the agent can set these to match its own timeout budget
- A command that exhausted all retries exits non-zero with `"retryable": false` in the error block

---

## Schema

`response-envelope` — `meta` block extended with optional `retries` integer field

---

## Wire Format

Response after 2 internal retries:

```json
{
  "ok": true,
  "data": { "id": "deploy-42" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "request_id": "req_01HZ",
    "command": "deploy",
    "duration_ms": 3420,
    "retries": 2,
    "timestamp": "2026-04-01T12:00:00Z"
  }
}
```

Error after exhausting retries:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NETWORK_ERROR",
    "message": "Connection refused after 3 attempts",
    "retryable": false,
    "retries_exhausted": 3
  },
  "warnings": [],
  "meta": {
    "exit_code": 12,
    "duration_ms": 9240,
    "retries": 3
  }
}
```

---

## Example

```
$ tool deploy --env prod --retries 0
→ fails immediately on first network error; agent's outer retry loop takes over

$ tool deploy --env prod --retries 3 --retry-delay 1s
→ tool retries up to 3 times internally; meta.retries reports how many occurred
→ agent knows not to retry again if meta.retries == 3 and ok == false
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Extends: retry count complements duration in meta to explain latency |
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Composes: total timeout budget consumed across all retries |
| [REQ-C-014](c-014-error-responses-include-retryable-and-retry-after-.md) | C | Provides: retryable field that agents use alongside retry count |
