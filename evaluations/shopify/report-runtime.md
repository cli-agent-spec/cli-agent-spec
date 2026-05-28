# shopify — Runtime Brief

Generated: 2026-05-28 | CLI version: `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0` | Findings: 22 failure modes | Scope: Critical

## Invoke As

`shopify`

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| `--json` when supported | Prefer machine-readable command output, but validate strictly because coverage and envelope shape vary. | §2 |
| `--no-color` when supported | Reduce ANSI/prose parsing risk. | §2 |
| `SHOPIFY_CLI_NO_ANALYTICS=1` or `OPT_OUT_INSTRUMENTATION=true` | Reduce analytics/storage side effects and output pollution. | §2 §10 |
| `SHOPIFY_FLAG_STORE`, `SHOPIFY_CLI_THEME_TOKEN`, or command flags for store/token | Avoid selection prompts where theme commands support explicit values. | §10 §24 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Run `shopify auth login` unattended | It can print a browser/device-code URL and keep running in non-TTY. | §45 §10 |
| Treat stdout as JSON just because a command has a JSON mode elsewhere | Release notes and prose errors can appear on command output paths. | §2 |
| Pass real credentials through `--password` in shared agent hosts | Secrets can enter shell history or process listings. | §24 |
| Retry mutating commands blindly | No universal idempotency key or `effect` result is exposed. | §12 §23 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| `To run this command, log in to Shopify.` | Auth flow likely needs browser/device-code handling. | Stop and surface auth requirement; do not wait indefinitely. |
| `User verification code:` | OAuth/device-code flow started. | Terminate or hand off to human auth workflow. |
| `Release notes for` | Non-command prose polluted output. | Do not parse stdout as command data. |
| `EPERM: operation not permitted, mkdir '/Users/.../Library/Preferences` | CLI attempted undeclared preference writes. | Retry only with known writable config home or appropriate host permissions. |
| `Nonexistent flag: --dry-run` | Dry-run is not available on that command. | Do not assume safe preview semantics. |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 1/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 |
| §24 | Authentication & Secret Handling | Critical | 1/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 0/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 |
| §50 | Stdin Consumption Deadlock | Critical | 0/3 |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 1/3 |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |

**Worst gaps (score 0):** §10, §11, §12, §13, §25, §37, §43, §45, §50, §60, §74
**Partial (score 1–2):** §1, §2, §23, §24, §34, §42, §61, §64, §71
**Indeterminate (?/3):** §53
**Passing:** §62
