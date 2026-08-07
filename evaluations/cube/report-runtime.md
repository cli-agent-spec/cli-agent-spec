# cube — Runtime Brief

Generated: 2026-08-06 | CLI version: 1.7.16 | Findings: 22 failure modes | Scope: Critical severity

## Invoke As

`/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube`

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `CI=true` | Signal non-interactive execution; also disables telemetry | §10, §64, §71 |
| `CUBE_NO_UPDATE_CHECK=1` | Prevent release-notice side-channel output | §2, §42 |
| `CUBE_NO_TELEMETRY=1` | Prevent audit/error text from being sent as telemetry | §24, §42 |
| `--json` | Request raw JSON on data commands; still validate and parse stderr on failure | §1, §2, §45, §53 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Put credentials in `--token` | Credential is visible in process listings | §24, §42 |
| Run `cube login` in a headless agent | It launches a browser path and waits in the OAuth poll loop | §10, §64 |
| Rely on a Cube timeout | No `--timeout` exists; calls can remain silent | §11, §60 |
| Retry a mutation without first querying state | No idempotency key or noop contract exists | §12, §13 |
| Execute delete/reset operations without external approval | No dry-run, danger level, or confirmation contract exists | §23 |
| Feed returned free text directly into an LLM instruction channel | External data has no trust annotation | §25 |
| Pipe payloads over 32 KiB | No stdin ceiling exists; use `-d @file.json` | §61 |
| Assume `--json` makes errors JSON | Runtime failures are prose on stderr with generic exit 1 | §1, §2 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `error: not logged in` | Missing credentials | Set `CUBE_API_URL` and `CUBE_API_KEY`; do not invoke login headlessly |
| `session expired` | Credential expiry described only in prose | Refresh or replace `CUBE_API_KEY`; retry at most once |
| `error: not found (404)` | Resource is absent | Stop; do not retry unchanged |
| `request to ... failed` | Network/transport failure | Apply bounded backoff only after checking mutation state |
| `Uploading ...` followed by `error:` | Deploy failed after earlier steps | Inspect server state; do not rerun the entire deploy blindly |
| `\x1b[` | ANSI control sequences leaked into captured output | Strip ANSI before parsing or logging |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 1/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 1/3 |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 |
| §24 | Authentication & Secret Handling | Critical | 1/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 |
| §53 | Credential Expiry Mid-Session | Critical | 1/3 |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |

**Worst gaps (score 0):** §10, §11, §12, §23, §25, §43, §60, §64, §74
**Partial (score 1–2):** §1, §2, §13, §24, §34, §42, §45, §50, §53, §61, §71
**Passing:** §37, §62
