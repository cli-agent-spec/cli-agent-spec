# neonctl — Report Index

**Date:** 2026-06-06
**Version:** 2.22.2
**Scope:** Critical failure modes

## Scores

| Metric | Score |
|---|---:|
| Failure mode average | 0.38/3 |
| Readiness | 7/15 [C] |
| Passing Critical checks | 0/23 |
| Partial Critical checks | 7/23 |
| Failing Critical checks | 14/23 |
| Indeterminate Critical checks | 2/23 |

## Reports

| File | Audience |
|---|---|
| `report-dev.md` | CLI authors |
| `report-agent-dev.md` | Developers integrating agents with Neon CLI |
| `report-runtime.md` | Agents about to invoke Neon CLI |
| `report-issues.md` | Concrete issues and gaps |
| `findings.md` | Raw score table |
| `trace.md` | Probe details |
| `readiness.md` | Proactive readiness scoring |

## Worst Gaps

- §45 Headless Authentication / OAuth Browser Flow Blocking (0/3)
- §50 Stdin Consumption Deadlock (0/3)
- §23 Side Effects & Destructive Operations (0/3)
- §74 Credential Scope Declaration Absence (0/3)
- §75 Safe-Default Execution Mode Absent (0/3)

## Readiness Detail

| Dimension | Score |
|---|---:|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 1/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 2/3 |
