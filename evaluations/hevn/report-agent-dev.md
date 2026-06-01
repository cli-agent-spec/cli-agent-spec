# hevn — Integration Guide for Agent Builders

**Generated:** 2026-06-01
**CLI version:** hevn-cli 0.1.0

## Invocation Invariants

```text
ENV HEVN_CLI_CONFIG=<agent-owned config path>
ENV HEVN_API_KEY=<app credential when app commands are needed>
ENV HEVN_MCP_KEY=<MCP credential when MCP/transfer commands are needed>
FLAG --json on commands that support it
FLAG --yes only after independent scope confirmation
TIMEOUT subprocess.run(..., timeout=N)
```

## Integration Notes

- There is no machine-readable manifest. Build command wrappers from observed help and keep them version-pinned to `hevn-cli 0.1.0`.
- Treat `--json` as command-specific, not global. `hevn --output json` and `hevn --schema` both fail.
- Validation and auth errors are not consistently enveloped. Some are JSON `{"ok": false, ...}`, while Typer errors remain prose.
- The packaged `agent-skill` command is not usable in 0.1.0 because the referenced `CLAUDE.md` resource is absent.
- For auth, skip browser flows in agents. Inject credentials through env vars or an isolated config file.

## Per-Gap Workarounds

| § | Workaround |
|---|---|
| §45 / §64 | Do not run browser login in headless automation. Use `HEVN_API_KEY` and `HEVN_MCP_KEY`. |
| §1 / §2 | Check both exit code and parseability. Fall back to stderr parsing for Click/Typer errors. |
| §23 | Before any mutation, perform a read/list check and require an explicit object id. There is no dry-run contract. |
| §43 | Apply output capture limits outside the CLI. Prefer list commands with `--limit` where available. |
| §74 | Document required scopes in the agent wrapper because the CLI does not expose them. |
