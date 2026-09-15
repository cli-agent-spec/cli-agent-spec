# temporal — Runtime Brief

Generated: 2026-07-07 | CLI version: temporal version 1.7.2 (Server 1.31.1, UI 2.49.1) | Findings: 22 failure modes | Scope: critical

## Invoke As

`/opt/homebrew/bin/temporal`

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `stdin=DEVNULL` | Prevent prompt/stdin deadlocks | §10, §50 |
| `--output json` | Use structured success output where available | §2 |
| `--client-connect-timeout` and `--command-timeout` | Bound network waits | §11 |
| `NO_COLOR=1` and `--color never` | Keep output parseable | §2 |
| `PAGER=cat`, `EDITOR=true`, `VISUAL=true` | Avoid pager/editor traps if future commands add them | §10, §62 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Assume `--output json` means errors are JSON | Validation and network failures are prose | §1, §2 |
| Pass API keys on argv when an env/config route is available | Secrets are visible in process listings | §24, §42 |
| Run query-based destructive commands with `--yes` before scoping the query | No dry-run/effect field confirms affected resources | §23 |
| Pipe large payloads when `--input-file` is available | Potential pipe deadlock or unbounded stdin behavior | §61 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `Error: program interrupted` | Timeout-like command interruption | Classify with outer timer; retry only if safe |
| `required flag(s)` | Validation failure | Do not retry unchanged |
| `must bypass prompts when using JSON output` | Destructive query requires explicit prompt bypass | Review scope before adding `--yes` |
| `workflow not found` | Missing resource/not-found | Treat as terminal unless creating it is part of workflow |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 |
| §12 | Idempotency & Safe Retries | Critical | 1/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 |
| §24 | Authentication & Secret Handling | Critical | 1/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 1/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 2/3 |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 2/3 |
| §71 | Non-Interactive Installation Absence | Critical | 1/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |

**Worst gaps (score 0):** §1, §13, §25, §74
**Partial (score 1–2):** §2, §10, §11, §12, §23, §24, §34, §42, §43, §45, §50, §60, §61, §64, §71
**Indeterminate (?/3):** §53
**Passing:** §37, §62
