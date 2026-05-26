# dokploy CLI Agent Audit

**Generated:** 2026-05-26  
**CLI version:** 0.3.0  
**Package version:** @dokploy/cli@0.29.4  
**Scope:** Critical failure modes

## Summary

`dokploy` is a broad API CLI with useful command coverage and a documented `--json` flag on generated API commands, but its agent contract is thin. The main blockers are unstructured errors, generic exit code 1 failures, no schema/manifest, no timeout/idempotency/dry-run controls, and secrets accepted through argv.

## Scores

| Metric | Score |
|---|---:|
| Failure mode average | 1.1/3 |
| Critical modes passing | 6/22 |
| Critical modes partial | 6/22 |
| Critical modes failing | 10/22 |
| Readiness | 7/15 [C] |

## Key Findings

- `--json` does not apply to auth/config errors; missing credentials produce prose and exit 1.
- Destructive commands such as `application delete` expose no `--dry-run`, affected-scope preview, or explicit confirmation contract.
- Auth and generated commands accept sensitive values through flags such as `--token`, `--password`, `--apiKey`, and `--sshPrivateKey`.
- No `--schema`, manifest, exit-code table, required credential scopes, timeout flag, or idempotency key exists.
- Installed package identity is inconsistent: npm reports `@dokploy/cli@0.29.4`, while `dokploy --version` reports `0.3.0`.

## Files

| File | Description |
|---|---|
| `report-index.md` | Index and score summary. |
| `report-issues.md` | Concrete bugs and gaps. |
| `report-runtime.md` | Operational brief for agents invoking the CLI. |
| `report-agent-dev.md` | Integration guide for agent builders. |
| `report-dev.md` | Fix list for CLI authors. |
| `readiness.md` | Proactive readiness score. |
| `findings.md` | Raw failure-mode score table. |
| `trace.md` | Evidence for each critical check. |
| `environment.md` | Runtime and binary profile. |
