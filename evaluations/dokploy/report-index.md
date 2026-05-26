# dokploy CLI Agent Audit — Report Index

**Generated:** 2026-05-26  
**CLI version:** 0.3.0  
**Package version:** @dokploy/cli@0.29.4  
**Scope:** Critical failure modes

## Score Summary

| Area | Score |
|---|---:|
| Failure mode average | 1.1/3 |
| Critical modes passing | 6/22 |
| Critical modes partial | 6/22 |
| Critical modes failing | 10/22 |
| Readiness | 7/15 [C] |

## Reports

| File | Audience | Purpose |
|---|---|---|
| `report-dev.md` | CLI authors | Prioritized fix list. |
| `report-agent-dev.md` | Agent builders | Integration guidance and workarounds. |
| `report-runtime.md` | Runtime agents | Compact invocation brief. |
| `report-issues.md` | Agent users/operators | Concrete bugs and gaps observed during checks. |
| `readiness.md` | CLI authors and agent builders | Proactive readiness score. |
| `findings.md` | Auditors | Raw score table. |
| `trace.md` | Auditors | Commands, observations, and score evidence. |

## Worst Gaps

- §1 Exit Codes & Status Signaling — 0/3
- §11 Timeouts & Hanging Processes — 0/3
- §12 Idempotency & Safe Retries — 0/3
- §23 Side Effects & Destructive Operations — 0/3
- §74 Credential Scope Declaration Absence — 0/3

## Passing Areas

- §10 Interactivity & TTY Requirements
- §37 REPL / Interactive Mode Accidental Triggering
- §50 Stdin Consumption Deadlock
- §61 Bidirectional Pipe Payload Deadlock
- §62 $EDITOR and $VISUAL Trap
- §64 Headless Display and GUI Launch Blocking
