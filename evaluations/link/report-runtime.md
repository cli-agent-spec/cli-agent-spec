# link-cli — Runtime Brief

Generated: 2026-06-08 | CLI version: 0.7.1 | Findings: 22 failure modes | Scope: Critical

## Invoke As

`link-cli`

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `--format json --full-output` | Default JSON is parseable but not consistently enveloped; `--full-output` adds `ok`, `data`, and `meta`. | §2 |
| `--auth <path>` or `LINK_AUTH_FILE=<path>` | Avoid hidden platform config writes and isolate agent sessions. | §24, §45 |
| External process timeout | API calls do not expose a general timeout contract. | §11 |
| `NO_UPDATE_NOTIFIER=1` | Keep update notifier output out of agent parsing paths. | §2, §68-adjacent |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Branch only on process exit code 1. | Multiple unrelated failures collapse to the same exit code. | §1 |
| Treat `ok: true` polling output as final success without inspecting status fields. | Pending auth states can appear inside a success envelope. | §13 |
| Retry mutating commands blindly. | No idempotency key or effect contract prevents duplicate side effects. | §12 |
| Assume auth errors describe credential scope or expiry precisely. | Auth-required and expired-token paths use incomplete machine-readable fields. | §45, §53, §74 |
| Depend on incremental stdout from polling commands. | Long-running polling output can be buffered until process exit. | §60 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `"code": "UNKNOWN"` | Generic failure class; inspect message and command context. | Do not retry blindly; classify manually. |
| `"code": "NOT_AUTHENTICATED"` | Auth is required but no `auth_methods` field is present. | Run `link-cli auth login` and poll with bounded external timeout. |
| `"pending": true` | Flow is not complete even if the command exited 0. | Continue polling or surface to user. |
| `[truncated: showing tokens` | Token limiter clipped output. | Re-run with `--token-offset` or stronger filtering. |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 |
| §24 | Authentication & Secret Handling | Critical | 2/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 2/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 1/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 |
| §53 | Credential Expiry Mid-Session | Critical | 1/3 |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 2/3 |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |

**Worst gaps (score 0):** §1, §11, §12, §13, §23, §25, §60, §74
**Partial (score 1-2):** §2, §10, §24, §34, §37, §42, §43, §45, §53, §64, §71
**Passing:** §50, §61, §62
