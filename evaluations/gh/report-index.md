# CLI Agent Evaluation — gh

**Generated:** 2026-05-07
**CLI version:** 2.88.1
**Scope:** Critical failure modes
**Failure modes evaluated:** 13 of 71 _(scope: Critical)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | 3 | 7 | 2 | 12 |
| High | 1 | 0 | 0 | 1 |
| **All** | **4** | **7** | **2** | **13** |

**Average score:** 1.8 / 3

## Readiness Score

| Dimension | Score |
|---|---|
| Documentation Quality | 1/3 |
| Self-Description | 1/3 |
| Pre-built Integrations | 1/3 |
| Setup Reproducibility | 3/3 |
| Workflow Coverage | 1/3 |
| **Total** | **7/15 [D]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- **Exit 0 on all HTTP errors** (§1, §53) — auth failures, 404s, and GraphQL errors all return exit 0; agents cannot detect failure without parsing stderr prose
- **No machine-readable auth error** (§53) — expired token produces plain-text stderr and suggests an interactive-only fix (`gh auth login`)
- **Mutating commands create real resources immediately** (§62) — `gh issue create` with all flags supplied creates a live issue with no dry-run, no confirmation, no idempotency key
- **`--json` not auto-activated** (§2) — must be passed explicitly with a field list on every command; no response envelope
- **No `--non-interactive` flag** (§10) — headless operation requires undocumented env var combination

## Observed Bugs

3 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
