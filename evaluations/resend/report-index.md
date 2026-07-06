# resend — Evaluation Index

**Generated:** 2026-07-06
**CLI version:** resend-cli v2.8.1
**Scope:** Critical
**Failure modes evaluated:** 22 of 71 _(scope: Critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | 4 | 12 | 5 | 22 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |
| **All** | **4** | **12** | **5** | **22** |

**Average score:** 1.2 / 3

## Readiness Score

| Dimension | Score |
|---|---|
| Documentation Quality | 3/3 |
| Self-Description | 2/3 |
| Pre-built Integrations | 3/3 |
| Setup Reproducibility | 3/3 |
| Workflow Coverage | 3/3 |
| **Total** | **14/15 [A]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- `whoami` reports a synthetic `--api-key` as authenticated, which can make agents trust an invalid credential.
- `open` and `docs` launch the OS browser even under quiet/JSON-oriented usage, with no structured URL fallback.
- Large dry-run content is emitted in full without `meta.truncated`, `meta.total_bytes`, or an output-size cap.
- User-provided HTML is returned as ordinary JSON data with no `trusted:false` or external-data boundary.
- All observed error cases collapse to exit code 1, forcing agents to parse error strings for retry policy.

## Observed Bugs

6 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
