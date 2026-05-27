# Firecrawl CLI - CLI Agent Audit Index

**Generated:** 2026-05-27
**CLI version:** 1.18.1
**Scope:** Critical failure modes

## Score Summary

| Metric | Result |
|---|---|
| Failure modes evaluated | 23 of 73 active modes (Critical scope) |
| Failure mode average | 0.48/3 |
| Passing | 0 |
| Partial | 9 |
| Failing | 12 |
| Indeterminate | 2 |
| Readiness | 7/15 [C] |

## Start Here

- [README](README.md) - executive summary and file directory.
- [Issues](report-issues.md) - concrete agent-facing bugs.
- [Runtime Brief](report-runtime.md) - how an agent should invoke Firecrawl safely today.
- [Agent Builder Guide](report-agent-dev.md) - wrapper/integration guidance.
- [Developer Fix List](report-dev.md) - prioritized fixes for CLI authors.

## Worst Gaps

§1 Exit Codes & Status Signaling, §10 Interactivity & TTY Requirements, §12 Idempotency & Safe Retries, §13 Partial Failure & Atomicity, §23 Side Effects & Destructive Operations
