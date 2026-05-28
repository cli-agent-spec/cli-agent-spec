# shopify — Evaluation Index

**Generated:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Scope:** Critical
**Failure modes evaluated:** 22 of 71 _(scope: Critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---:|---:|---:|---:|
| Critical | 1 | 9 | 11 | 22 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |
| **All** | **1** | **9** | **11** | **22** |

**Average score:** 0.6 / 3

## Readiness Score

| Dimension | Score |
|---|---:|
| Documentation Quality | 1/3 |
| Self-Description | 2/3 |
| Pre-built Integrations | 0/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 1/3 |
| **Total** | **6/15 [D]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- `shopify auth login` blocks in non-TTY after printing a device-code URL.
- `shopify theme console` can hang under non-TTY instead of returning a structured interactive-required error.
- Release notes, analytics/storage errors, and stack traces can pollute command output.
- There is no consistent JSON envelope for success and failure paths.
- Mutating/destructive commands lack universal dry-run, idempotency, and effect contracts.

## Observed Bugs

5 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
