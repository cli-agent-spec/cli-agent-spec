# temporal — Evaluation Index

**Generated:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Scope:** critical
**Failure modes evaluated:** 22 of 71 _(scope: critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | 2 | 15 | 4 | 22 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |
| **All** | **2** | **15** | **4** | **22** |

**Average score:** 1.1 / 3

## Readiness Score

| Dimension | Score |
|---|---|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 0/3 |
| Setup Reproducibility | 0/3 |
| Workflow Coverage | 1/3 |
| **Total** | **3/15 [F]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- `--output json` does not produce JSON error envelopes for validation and network failures.
- Exit codes collapse distinct failure classes into exit 1.
- Destructive operations lack dry-run/effect metadata and credential scopes are not machine-readable.

## Observed Bugs

4 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
