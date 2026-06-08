# link-cli — Evaluation Index

**Generated:** 2026-06-08
**CLI version:** 0.7.1
**Scope:** Critical
**Failure modes evaluated:** 22 of 71 _(scope: Critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Total |
|---|---:|---:|---:|---:|
| Critical | 3 | 11 | 8 | 22 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |
| **All** | **3** | **11** | **8** | **22** |

**Average score:** 1.2 / 3

## Readiness Score

| Dimension | Score |
|---|---:|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 3/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 3/3 |
| **Total** | **10/15 [B]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- Semantic failures all exit 1 and JSON errors omit an `exit_code`, so agents cannot branch reliably on process status.
- Default `--format json` is not consistently enveloped; callers must know to add `--full-output`.
- Auth/API timeout and polling behaviors return generic or success-shaped output instead of machine-actionable timeout/partial states.
- Mutating commands lack idempotency, dry-run, danger, and effect contracts.
- Command metadata does not declare required credential scopes.

## Observed Bugs

6 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
