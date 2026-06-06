# neonctl — Integration Guide for Agent Builders

**Date:** 2026-06-06
**Version:** 2.22.2

## Invocation

Use the absolute binary discovered during audit:

```bash
/Users/roman/.hermes/node/bin/neonctl
```

For agent runs, always include:

```bash
--config-dir <isolated-temp-dir> --no-analytics --color false
```

Prefer credentials in the environment:

```bash
NEON_API_KEY=<token> neonctl <command> --output json --config-dir <isolated-temp-dir> --no-analytics --color false
```

Avoid passing `--api-key` unless you have no other option; it places the secret in argv.

## Safe Patterns

Use `link --agent` when linking a local directory. It is the one documented JSON state-machine workflow:

```bash
neonctl link --agent --output json --config-dir <isolated-temp-dir> --no-analytics --color false
```

Always run commands through a subprocess timeout. The CLI has auth/init paths that can block.

Set these environment variables around every invocation:

```bash
PAGER=cat
GIT_PAGER=cat
MANPAGER=cat
LESS=-FRX
EDITOR=true
VISUAL=true
NO_COLOR=1
```

## Parse Rules

- Do not assume `--output json` means errors are JSON. Check stdout first, then stderr.
- Treat exit code `1` as generic. There is no semantic exit-code table.
- Treat missing stdout plus prose stderr as an error even if the requested output mode was JSON.
- Redact captured output before storing it; auth-related commands can include URLs and account metadata.

## Commands To Avoid Without Human Approval

Treat these as destructive or mutating unless you have a dry-run-equivalent workflow from the user:

```text
projects create/delete/update
branches create/delete/reset/restore/rename/add-compute/set-default
databases create/delete
roles create/delete
ip-allow add/remove/reset
data-api create/update/delete/refresh-schema
```

## Known Gaps

| Gap | Agent workaround |
|---|---|
| Browser auth blocks non-TTY | Use `NEON_API_KEY`; never call `auth` unattended. |
| `init` prompts without `--agent` | Pass `--agent cursor`, `--agent copilot`, or `--agent claude`, and still use a timeout. |
| No manifest/schema | Parse help conservatively; do not infer required scopes or danger level. |
| No dry-run for deletes | Do not execute destructive commands autonomously. |
| No idempotency key contract | Query current state before retrying mutating operations. |
| JSON errors inconsistent | Build fallback stderr parsing and classify unknown errors as non-retryable. |
