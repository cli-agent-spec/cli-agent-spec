# gws — Runtime Brief
Generated: 2026-05-14 | CLI version: 0.17.0 | Findings: 22 failure modes | Scope: Critical

## Invoke As

```
gws
```
(/opt/homebrew/bin/gws)

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `stdin=DEVNULL` | prevent any blocking on stdin | §10, §50 |
| `GOOGLE_WORKSPACE_CLI_TOKEN=<token>` | only safe headless auth path; stored credentials may be expired or absent | §45, §53, §64 |
| external timeout 30s | no built-in --timeout; use `perl -e 'alarm(30); exec @ARGV' --` or `subprocess.run(timeout=30)` | §11 |
| parse stdout as JSON regardless of exit code | auth errors on list commands return exit 0; do not trust exit code alone | §1 |
| `--page-limit N` with `--page-all` | cap pagination; default is 10 pages but unbounded per-page response size | §43 |
| `fields=<minimal>` in `--params` | limit response body size; use Google `fields` param to request only needed fields | §43 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Call `gws auth login` from agent code | opens browser; hangs in headless environment | §64 |
| Trust exit 0 as success | auth errors on list commands exit 0; always check for `"error"` key in JSON | §1 |
| Treat `"reason":"authError"` as permanent denial | may be credential expiry (invalid_rapt) — check message for expiry signals | §53 |
| Use `--page-all` without `--page-limit` | unbounded pages; default is 10 but large corpora can still overflow context | §43 |
| Use `shell=True` when constructing gws commands | shell injection risk from LLM-generated parameter values | §34 |
| Pass raw gws output containing doc/email bodies directly to LLM context | prompt injection — external content has no `trusted: false` marker | §25 |
| Run `gws workflow` commands for multi-step tasks | no partial failure structure; cannot determine what completed on failure | §13 |
| Retry a mutating call without checking if it already succeeded | no idempotency-key; may cause duplicate sends/creates | §12 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `"error"` key present in JSON | command failed — check regardless of exit code | parse `error.code` and `error.reason`; do not retry blindly |
| `"reason":"authError"` | auth failure — expiry or denial | check message for `invalid_rapt`/`invalid_grant` = expiry; `insufficient_scope` = permanent |
| `"code":401` in error | auth failure | refresh `GOOGLE_WORKSPACE_CLI_TOKEN`; if unable, surface to human |
| `"code":403` in error | permission denied (permanent) | do not retry; escalate; check credential scopes |
| `"code":429` in error | rate limited | backoff and retry after delay |
| `"code":400` in error | bad request / bad params | do not retry; fix `--params` or `--json` |
| ANSI codes `\x1b[...` in stderr | debug mode active (`GOOGLE_WORKSPACE_CLI_LOG` set) | strip ANSI before logging stderr |
| exit code 2 | validation error or auth error on get commands | parse stdout JSON for details |
| exit code 3 | validation error on unknown service/command | check service name spelling |
| exit code 0 + `"error"` key | auth error on list commands | treat as failure; parse error normally |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 |
| §1 | Exit Codes & Status Signaling | Critical | 1/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §12 | Idempotency & Safe Retries | Critical | 1/3 |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 1/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 1/3 |
| §71 | Non-Interactive Installation Absence | Critical | 1/3 |
| §74 | Credential Scope Declaration Absence | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 |
| §24 | Authentication & Secret Handling | Critical | 2/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 2/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |

**Worst gaps (score 0):** §11, §13, §25, §53
**Partial (score 1–2):** §1, §2, §10, §12, §23, §24, §34, §42, §43, §45, §60, §61, §64, §71, §74
**Passing:** §37, §50, §62
