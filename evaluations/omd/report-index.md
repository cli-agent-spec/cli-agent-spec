# CLI Agent Audit Report Index — omd

**Generated:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Scope:** Critical failure modes

## Score Summary

| Metric | Result |
|---|---:|
| Failure modes evaluated | 22 |
| Average failure-mode score | 1.5/3 |
| Passing | 4 |
| Partial | 16 |
| Failing | 2 |
| Indeterminate | 0 |
| Readiness score | 12/15 [B] |

## Worst Gaps

| Failure mode | Score | Finding |
|---|---:|---|
| §43 Tool Output Result Size Unboundedness | 0/3 | No bounded-output contract or truncation metadata. |
| §74 Credential Scope Declaration Absence | 0/3 | Command schema lacks required credential scopes and no permission preflight exists. |
| §11 Timeouts & Hanging Processes | 1/3 | Timeout exits promptly but is reported as `GENERAL_ERROR`. |
| §53 Credential Expiry Mid-Session | 1/3 | Expiry is text-only and collapses into `AUTH_REQUIRED`. |

## Reports

| File | Audience |
|---|---|
| `report-dev.md` | CLI maintainers fixing the gaps |
| `report-agent-dev.md` | Developers integrating agents with `omd` |
| `report-runtime.md` | Runtime instructions for an AI agent invoking `omd` |
| `report-issues.md` | Concrete observed bugs and gaps |
| `readiness.md` | Proactive agent-readiness score |
| `findings.md` | Score table |
| `trace.md` | Commands and observed outputs |
