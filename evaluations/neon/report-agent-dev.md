# neon - Agent Developer Integration Guide

**Generated:** 2026-07-05
**CLI version:** 2.30.1
**Scope:** Critical

## Invocation Contract

Use the absolute binary from the environment profile:

```bash
/Users/roman/.hermes/node/bin/neon
```

Recommended wrapper defaults:

```text
ENV:
  NEON_API_KEY=<provided securely by the runtime>
  NO_COLOR=1

FLAGS:
  --output json
  --no-color
  --no-analytics
  --config-dir <agent-owned-temp-dir>
  --context-file <agent-owned-context-file>

PROCESS:
  stdin closed unless a command explicitly needs stdin
  external timeout on every invocation
  stderr captured and parsed as a possible error source
```

## Critical Integration Rules

1. Do not call authenticated Neon commands without a valid API key in headless execution. The CLI can enter browser OAuth and wait.
2. Do not treat `--output json` as a guarantee on failure paths. Validate stdout as JSON and fall back to stderr classification.
3. Keep credentials out of argv. Prefer `NEON_API_KEY` over `--api-key`.
4. Isolate state with `--config-dir` and `--context-file`; do not let commands discover parent `.neon` files.
5. Never blind-retry mutating commands. No idempotency-key or effect contract was found.
6. For destructive commands, require a separate read/confirm step in the agent layer because the CLI lacks a general dry-run contract.

## Workarounds by Gap

| Section | Gap | Agent-side workaround |
|---|---|---|
| §45, §64, §10 | Browser OAuth in headless/no-credential paths | Preflight `NEON_API_KEY` before any authenticated call; kill on `Awaiting authentication in web browser`. |
| §1, §2 | Prose errors and generic exit code 1 | Classify stderr patterns and never assume JSON exists on non-zero exit. |
| §12 | No idempotency key | Read state before mutation and after failure; retry only when target state is absent. |
| §23 | No dry-run for destructive operations | Have the agent list/inspect target resources first and require explicit user confirmation before delete. |
| §24, §42 | Secret flag accepted | Inject secrets through environment variables and scrub command logs. |
| §50, §61 | Stdin sentinel bug | Avoid `--data -`; use literal JSON or `@file` only after a small validation probe. |
| §74 | No scope manifest | Maintain your own command-to-scope map and ask users for minimal keys out of band. |
| §53, §60, §62 | Indeterminate checks | Treat credential expiry, long-running streaming, and psql editor paths as unverified risk. |

## Recommended Adapter Behavior

Return an internal normalized result regardless of Neon CLI output shape:

```json
{
  "ok": false,
  "exit_code": 1,
  "stdout_json": null,
  "stderr_text": "ERROR: ...",
  "classified_error": "VALIDATION_ERROR | AUTH_BROWSER_FLOW | AUTH_FAILED | UNKNOWN",
  "retryable": false
}
```

The adapter should mark `AUTH_BROWSER_FLOW` when stderr contains `Awaiting authentication in web browser` and terminate the child process immediately.
