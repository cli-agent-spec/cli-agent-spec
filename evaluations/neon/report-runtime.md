# neon - Runtime Brief

Generated: 2026-07-05 | CLI version: 2.30.1 | Findings: 22 failure modes | Scope: Critical

## Invoke As

`/Users/roman/.hermes/node/bin/neon`

## Always Include

| Flag / Env var | Reason | Sections |
|---|---|---|
| `NEON_API_KEY` | Avoid command-line secret exposure and bypass browser OAuth where possible. | §24, §45 |
| `--output json` | Request machine-readable output, while still treating errors as possibly prose. | §2 |
| `--no-color` | Prevent ANSI/color contamination in captured output. | §2 |
| `--no-analytics` | Reduce unrelated side effects and background flush waits. | §11 |
| `--config-dir <temp-or-project-dir>` | Isolate credentials and avoid global config contamination. | §24 |
| `--context-file <explicit-file>` | Avoid accidental parent-directory `.neon` discovery. | §10 |
| External process timeout | Neon does not expose a general `--timeout`; wrap every invocation. | §11, §45 |

## Never Do

| Action | Risk | Sections |
|---|---|---|
| Run Neon CLI without credentials in a headless agent session. | It can launch browser OAuth and wait until killed. | §10, §45, §64 |
| Assume `--output json` makes errors parseable. | Missing args, invalid auth, and validation failures used prose stderr. | §1, §2 |
| Pass real API keys via `--api-key` in command arguments. | Secrets become visible in command history and process listings. | §24, §42 |
| Run destructive commands expecting dry-run support. | `projects delete` exposes no dry-run or affected-scope preview. | §23 |
| Retry mutating commands blindly. | No idempotency-key or `effect` contract was found. | §12 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `Awaiting authentication in web browser` | Command entered OAuth/browser flow. | Kill the process and rerun only with a valid `NEON_API_KEY` or avoid the path. |
| `ERROR: Not enough non-option arguments` | Validation failure in prose stderr. | Treat as non-JSON failure even when `--output json` was supplied. |
| `ERROR: Unknown command: -` | `api --data -` was not accepted as documented in the probe. | Use a file or literal JSON body and verify parsing before relying on stdin. |
| `Authentication failed, deleting credentials` | Invalid credential path. | Do not parse stdout; inspect stderr and isolate `--config-dir`. |

## Score Summary

| Section | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 |
| §24 | Authentication & Secret Handling | Critical | 1/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 0/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 |
| §60 | OS Output Buffer Deadlock | Critical | ?/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | ?/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |

**Worst gaps (score 0):** §1, §10, §11, §12, §13, §23, §25, §37, §43, §45, §64, §74
**Partial (score 1-2):** §2, §24, §34, §42, §50, §61, §71
**Indeterminate (?/3):** §53, §60, §62
