# hevn — Report Index

**CLI version:** hevn-cli 0.1.0
**Generated:** 2026-06-01
**Scope:** critical

## Score Summary

| Metric | Result |
|---|---|
| Failure modes evaluated | 22 Critical checks |
| Average score | 0.9/3 |
| Passing | 2 |
| Partial | 12 |
| Failing | 8 |
| Indeterminate | 0 |
| Readiness | 7/15 [C] |

## Critical Scorecard

| § | Title | Score |
|---|---|---|
| §37 | REPL / Interactive Mode Accidental Triggering | 3/3 |
| §62 | $EDITOR and $VISUAL Trap | 3/3 |
| §42 | Debug / Trace Mode Secret Leakage | 2/3 |
| §71 | Non-Interactive Installation Absence | 2/3 |
| §34 | Shell Injection via Agent-Constructed Commands | 1/3 |
| §50 | Stdin Consumption Deadlock | 1/3 |
| §61 | Bidirectional Pipe Payload Deadlock | 1/3 |
| §10 | Interactivity & TTY Requirements | 1/3 |
| §11 | Timeouts & Hanging Processes | 1/3 |
| §12 | Idempotency & Safe Retries | 1/3 |
| §23 | Side Effects & Destructive Operations | 1/3 |
| §24 | Authentication & Secret Handling | 1/3 |
| §1 | Exit Codes & Status Signaling | 1/3 |
| §2 | Output Format & Parseability | 1/3 |
| §43 | Tool Output Result Size Unboundedness | 0/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | 0/3 |
| §53 | Credential Expiry Mid-Session | 0/3 |
| §60 | OS Output Buffer Deadlock | 0/3 |
| §64 | Headless Display and GUI Launch Blocking | 0/3 |
| §13 | Partial Failure & Atomicity | 0/3 |
| §25 | Prompt Injection via Output | 0/3 |
| §74 | Credential Scope Declaration Absence | 0/3 |

## Reports

- [report-issues.md](report-issues.md) — concrete bugs and gaps observed during evaluation.
- [report-runtime.md](report-runtime.md) — operational guidance for agents invoking `hevn`.
- [report-agent-dev.md](report-agent-dev.md) — integration guidance for agent developers.
- [report-dev.md](report-dev.md) — prioritized fix list for CLI authors.
