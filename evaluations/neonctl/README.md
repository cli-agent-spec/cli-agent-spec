# neonctl CLI Agent Audit

**CLI:** neonctl
**Version:** 2.22.2
**Date:** 2026-06-06
**Scope:** Critical failure modes

## Summary

Neon CLI is partly agent-ready: it has documented npm installation, API-key auth, global JSON output, config-dir isolation, and an unusually useful `link --agent` JSON state machine. The problem is that those patterns are not applied across the CLI. Auth and init can still block, common failures are prose stderr even in JSON mode, mutating commands lack dry-run/idempotency contracts, and there is no manifest for agents to inspect.

## Scores

| Area | Score |
|---|---:|
| Critical failure modes | 0.38/3 |
| Readiness | 7/15 [C] |

## Key Findings

- `neonctl auth` opens browser OAuth and did not exit under non-TTY timeout.
- `neonctl init` prompts for editor selection unless `--agent` is provided.
- Invalid explicit `--api-key` auth can delete configured credentials.
- `--output json` does not consistently apply to error paths.
- Destructive commands expose no dry-run/danger-level/confirmation manifest.

## Files

| File | Purpose |
|---|---|
| `report-index.md` | Score summary and links |
| `report-dev.md` | Fix list for CLI authors |
| `report-agent-dev.md` | Integration guide for agent builders |
| `report-runtime.md` | Operational brief for agents |
| `report-issues.md` | Concrete issues and gaps |
| `findings.md` | Raw score table |
| `issues.md` | Observed bugs |
| `trace.md` | Probe trace |
| `readiness.md` | Readiness score |
