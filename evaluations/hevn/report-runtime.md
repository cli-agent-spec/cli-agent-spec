# hevn — Runtime Brief for Agents

**Generated:** 2026-06-01
**CLI version:** hevn-cli 0.1.0

## Invoke

Use:

```bash
/Users/roman/Documents/HEVN\ CLI/.audit-venv311/bin/hevn <command> --json
```

Set an isolated config path for unattended runs:

```bash
export HEVN_CLI_CONFIG=/path/to/agent/hevn-config.json
export HEVN_API_KEY=...
export HEVN_MCP_KEY=...
```

## Always Do

- Prefer `--json` or `--yaml` on commands that support them.
- Pass `--yes` only after independently verifying the affected object and scope.
- Set `HEVN_CLI_CONFIG` so the agent does not read or mutate a human user's default `~/.config/hevn-cli/config.json`.
- Use external subprocess timeouts. CLI network calls use an internal 60 second HTTP timeout, and not all waits produce structured timeout JSON.

## Never Do

- Do not call `hevn login` in a fully unattended agent run; it waits for a browser callback.
- Do not depend on `hevn --version`; it is not implemented.
- Do not assume every `--json` response has `ok`, `data`, `error`, and `meta`.
- Do not pipe secrets into `hevn mcp-key` in non-TTY mode; use `HEVN_MCP_KEY`.
- Do not parse Typer validation errors as JSON.

## Watch in Output

- `No such option` means Click/Typer validation failed and output is prose on stderr.
- `This command needs app authorization (JWT)` means app auth is missing.
- `This command needs an MCP key` means MCP auth is missing.
- `Request failed:` can represent network, DNS, or transport failure and is not a typed retry contract.
