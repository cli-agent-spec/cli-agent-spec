# docuseal-cli - Evaluation Index

**Generated:** 2026-05-20  
**CLI version:** 1.0.3  
**Scope:** all  
**Failure modes evaluated:** 71 of 71 _(scope: all)_

## Score Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Total |
|---|---:|---:|---:|---:|
| Critical | 5 | 6 | 11 | 22 |
| High | 3 | 11 | 21 | 35 |
| Medium | 1 | 3 | 10 | 14 |
| **All** | **9** | **20** | **42** | **71** |

**Average score:** 0.72 / 3

## Readiness Score

| Dimension | Score |
|---|---|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 1/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 2/3 |
| **Total** | **7/15 [C]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- Common failures produce stack traces instead of structured JSON, so agents cannot parse errors consistently.
- All observed failures collapse to generic exit code 1 with no semantic exit-code table.
- The configure prompt path can exit 0 under non-TTY stdin without writing configuration.
- Async handlers are registered under program.parse(), and observed auth/network failures surfaced as unhandled stack traces.
- The bundled skill metadata is versioned 1.0.6 while the installed binary reports 1.0.3.

## Observed Bugs

4 bugs recorded during evaluation - see [report-issues.md](report-issues.md) for details.
