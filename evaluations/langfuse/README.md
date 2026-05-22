# Langfuse CLI Agent Audit

**Generated:** 2026-05-22  
**CLI:** `langfuse` from `langfuse-cli` 0.0.10  
**Install used:** project-local npm install in `/Users/roman/Documents/Languse`

## Summary

The Langfuse CLI is installable and discoverable, with a useful OpenAPI-backed command surface and `--curl` preview mode. The main agent-readiness gaps are structured error consistency, semantic exit codes, safe mutation controls, output-size contracts, and credential/scope metadata.

## Scores

| Metric | Result |
|---|---:|
| Critical failure-mode average | 1.4/3 |
| Critical pass / partial / fail / indeterminate | 6 / 7 / 6 / 3 |
| Readiness score | 9/15 [C] |

## Key Findings

- `--json` is not honored for parser and validation errors.
- Exit code `1` is reused for distinct failure classes.
- Delete/create commands lack dry-run, idempotency, and effect metadata.
- Missing-auth errors do not expose `AUTH_REQUIRED` or `auth_methods`.
- There is no top-level agent manifest with typed commands, flags, exit codes, scopes, and safety metadata.

## Files

| File | Description |
|---|---|
| `environment.md` | Local binary/runtime profile. |
| `readiness.md` | Proactive agent-readiness score. |
| `findings.md` | Critical failure-mode score table. |
| `trace.md` | Commands and observed outputs for each check. |
| `issues.md` | Concrete bugs and gaps. |
| `report-index.md` | Report directory and score summary. |
| `report-dev.md` | Fix list for CLI authors. |
| `report-agent-dev.md` | Integration guidance for agent builders. |
| `report-runtime.md` | Runtime brief for agents. |
| `report-issues.md` | Issues report for users/maintainers. |
