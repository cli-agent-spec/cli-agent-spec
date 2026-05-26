# dokploy — Agent Builder Integration Guide

**Generated:** 2026-05-26  
**CLI version:** 0.3.0

## Invocation

Use:

```bash
DOKPLOY_URL="https://your-dokploy.example" DOKPLOY_API_KEY="$TOKEN" dokploy <group> <action> --json
```

Prefer `DOKPLOY_API_KEY` or `DOKPLOY_AUTH_TOKEN` over `dokploy auth -t ...`, because `-t/--token` exposes the secret in argv and shell history.

## Required Wrapper Behavior

- Always run commands with a caller-side timeout.
- Capture stdout and stderr separately.
- Treat any non-JSON output as an error path, even if `--json` was passed.
- Do not rely on exit code meaning beyond success/non-success; observed failures collapse to exit 1.
- Do not pass secrets through CLI flags unless there is no alternative.
- For destructive commands, require an external human or policy approval before invocation; the CLI has no dry-run or affected-scope preview.
- For mutating commands, add your own idempotency guard outside the CLI, such as checking existing resource state before retrying.
- Cap captured output size in the agent runtime; the CLI has no truncation metadata or max-output flag.

## Parsing Rules

Successful generated API commands with `--json` print raw JSON from the API. Error paths can be prose, for example:

```text
No configuration found. Please run 'dokploy auth' first or set DOKPLOY_URL and DOKPLOY_AUTH_TOKEN environment variables.
```

Use a parser that first attempts JSON, then falls back to classifying known prose patterns:

| Pattern | Treat As |
|---|---|
| `No configuration found` | auth_required |
| `error: unknown option` | invocation_error |
| `connect ` / `ECONN` / `EPERM` | network_or_runtime_error |
| `Authentication failed:` | auth_failed |

## Unsupported Agent Contracts

- No `dokploy --schema`
- No declared exit-code table
- No required credential scopes
- No timeout flag
- No idempotency key
- No dry-run flag on destructive commands
- No trusted/untrusted content separation
