# Runtime Brief — gh
Generated: 2026-05-07 | CLI version: 2.88.1 | Findings: 13 failure modes | Scope: Critical

## Invoke As

`gh`

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `GH_PROMPT_DISABLED=1` | Disables all interactive prompts | §10 |
| `GH_PAGER=cat` | Suppresses pager for long output | §10 |
| `GH_NO_UPDATE_NOTIFIER=1` | Suppresses update notices on stderr | §41 |
| `NO_COLOR=1` | Suppresses ANSI color codes | §8 |
| `--json <fields>` | Forces JSON output (not auto-activated) | §2 |
| `GH_TOKEN=$GH_TOKEN` | Pre-set auth token; avoids interactive login | §45 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Branch on exit code alone | Exit 0 on HTTP 4xx errors — exit code is unreliable | §1, §53 |
| Run `gh issue create` / `gh pr create` without all content flags | Opens `$EDITOR` and blocks | §62 |
| Run list commands without `--limit N` | Default is 30; no truncation signal in output | §43 |
| Retry mutating commands on failure | No idempotency guarantee — duplicates possible | §12 |
| Assume `gh auth login` is available for re-auth | Interactive-only browser flow | §45 |

## Watch in Output

| Pattern (stderr) | Meaning | Action |
|---|---|---|
| `HTTP 401` | Auth token expired or invalid | Replace `GH_TOKEN`; do not retry |
| `HTTP 404` | Resource not found (exits 0) | Check `$?` is unreliable; parse stderr | §1 |
| `Try authenticating with:  gh auth login` | Auth failure — interactive recovery suggested | Abort; report auth failure to operator |
| `GraphQL: Could not resolve` | Resource not found via GraphQL | Treat as not-found; do not retry |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 1/3 |
| §45 | Headless Authentication | Critical | 1/3 |
| §2 | Output Format & Parseability | Critical | 2/3 |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 |
| §11 | Timeouts & Hanging Processes | Critical | 2/3 |
| §43 | Output Size Unboundedness | Critical | 2/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 2/3 |
| §8 | ANSI & Color Code Leakage | High | 3/3 |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 |
| §60 | OS Output Buffer Deadlock | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 |

**Worst gaps (score 0):** §1, §53
**Partial (score 1–2):** §12, §45, §2, §10, §11, §43, §62
**Passing:** §8, §50, §60, §64
