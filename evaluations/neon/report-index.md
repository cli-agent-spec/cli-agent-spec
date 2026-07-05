# neon - Evaluation Index

**Generated:** 2026-07-05
**CLI version:** 2.30.1
**Scope:** Critical
**Failure modes evaluated:** 22 of 71 _(scope: Critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Indeterminate | Total |
|---|---:|---:|---:|---:|---:|
| Critical | 0 | 7 | 12 | 3 | 22 |
| High | 0 | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 | 0 |
| **All** | **0** | **7** | **12** | **3** | **22** |

**Average score:** 0.4 / 3

## Readiness Score

| Dimension | Score |
|---|---:|
| Documentation Quality | 2/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 1/3 |
| Setup Reproducibility | 2/3 |
| Workflow Coverage | 2/3 |
| **Total** | **8/15 [C]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- Browser OAuth starts in headless/no-credential flows and blocks agent execution.
- `link --no-checks`, documented as offline, still entered the login path in the probe.
- JSON output mode does not cover error paths, leaving agents with prose stderr and empty stdout.
- Destructive commands expose no dry-run or affected-scope preview contract.
- No manifest/schema declares commands, exit codes, credential scopes, interactivity, or safe defaults.

## Observed Bugs

6 bugs recorded during evaluation - see [report-issues.md](report-issues.md) for details.
