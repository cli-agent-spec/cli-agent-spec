# cube — Evaluation Index

**Generated:** 2026-08-06
**CLI version:** 1.7.16
**Scope:** Critical severity
**Failure modes evaluated:** 22 of 74 _(scope: Critical severity)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | 2 | 11 | 9 | 22 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |
| **All** | **2** | **11** | **9** | **22** |

**Average score:** 0.8 / 3

## Readiness Score

| Dimension | Score |
|---|---|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 0/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 3/3 |
| **Total** | **7/15 [C]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- OAuth login launches a browser and remains in a polling loop under headless CI
- API responses are unbounded and fully buffered, with no truncation or heartbeat
- Destructive raw API requests have no dry-run, affected-scope preview, or confirmation contract
- `--json` returns raw JSON on success but prose-only stderr on failure
- Mutations have no idempotency key or structured partial-failure recovery

## Observed Bugs

17 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
