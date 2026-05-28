# omd CLI Agent Audit

**Generated:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Repository:** `romamo/openmetadata-cli`

## Summary

`omd` is already meaningfully agent-oriented: it has JSON envelopes, schema introspection, dry-run mutation previews, non-TTY auth guards, MCP mode, packaged agent skills, and prompt-injection tagging. The Critical audit found two failing gaps and several partial contracts around auth, timeout, output size, exit-code declaration, and credential scopes.

## Scores

| Area | Score |
|---|---:|
| Critical failure-mode average | 1.5/3 |
| Critical modes passing | 4/22 |
| Critical modes partial | 16/22 |
| Critical modes failing | 2/22 |
| Readiness | 12/15 [B] |

## Key Findings

- No bounded-output contract: large content can be emitted without truncation metadata.
- No machine-readable credential scope declaration or permission preflight.
- Timeout and credential-expiry errors collapse into generic/auth-required codes.
- Invocation errors can bypass the JSON envelope.
- Non-TTY SSO and editor/REPL traps are handled well or not exposed.

## Files

| File | Purpose |
|---|---|
| `report-index.md` | Report index and score summary |
| `report-dev.md` | Fix list for CLI authors |
| `report-agent-dev.md` | Integration guide for agent builders |
| `report-runtime.md` | Runtime brief for agents |
| `report-issues.md` | Concrete issues and gaps |
| `readiness.md` | Readiness score |
| `findings.md` | Failure-mode score table |
| `trace.md` | Raw check traces |
| `linkedin.md` | LinkedIn post draft |
| `x.md` | X Premium post draft |
