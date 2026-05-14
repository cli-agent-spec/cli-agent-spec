# gws — Evaluation Index

**Generated:** 2026-05-14
**CLI version:** 0.17.0
**Scope:** Critical (22 of 71 failure modes)

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | 3 | 15 | 4 | 22 |
| **All** | **3** | **15** | **4** | **22** |

**Average score:** 1.23 / 3

_Readiness not evaluated. Run `/cli-agent-readiness` to populate this section._

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

- **Credential expiry is silent** — expired tokens return the same `reason:"authError"` as permanent denial; agents cannot distinguish and cannot auto-recover (§53)
- **No timeout flag** — network hangs block indefinitely with no structured error; the pipeline stalls until OS TCP timeout fires (§11)
- **Exit 0 on auth error** — list commands return exit 0 on auth failure; agents that branch on exit code proceed with empty results as if the call succeeded (§1)
- **No injection protection** — email bodies, document content, and file names arrive as raw strings; LLMs consuming this output are exposed to prompt injection from external data (§25)
- **No headless auth path** — `gws auth login` opens a browser with no `--print-url` alternative; agents must be pre-seeded with `GOOGLE_WORKSPACE_CLI_TOKEN` externally (§64)

## Observed Bugs

7 bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
