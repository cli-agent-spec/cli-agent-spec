# shopify — Agent Integration Guide

**Generated:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Scope:** Critical

## Invocation

Use `shopify` from `/opt/homebrew/bin/shopify`. Wrap every invocation with an external timeout. On macOS, use `subprocess.run(timeout=N)` from Python or `perl -e 'alarm(N); exec(@ARGV)' -- shopify ...`.

## Integration Invariants

```text
ENV:
  SHOPIFY_CLI_NO_ANALYTICS=1 or OPT_OUT_INSTRUMENTATION=true
  Prefer SHOPIFY_CLI_THEME_TOKEN over --password for theme credentials

FLAGS:
  Add --json only on commands that explicitly document it
  Add --no-color where supported
  Supply store/theme/client/organization IDs explicitly to avoid prompts

OUTPUT:
  Never assume stdout is JSON unless JSON parsing succeeds from the first non-whitespace byte
  Treat release notes, box-drawn prose, EPERM preference errors, and device-code URLs as control signals
```

## Required Wrappers

| Gap | Wrapper behavior |
|---|---|
| Headless auth | Detect `User verification code:` and stop the process; surface an auth-required state to the caller. |
| Interactive commands | Maintain a denylist for `auth login`, `theme console`, and other REPL/browser flows unless a human-auth session is expected. |
| Mutating commands | Require caller-provided idempotency at the orchestration layer; do not retry blindly after partial failure. |
| Destructive commands | Refuse commands such as `theme delete` unless the caller supplies explicit target IDs and an out-of-band confirmation. |
| Output parsing | Parse JSON only after stripping nothing; if stdout is not valid JSON, return a structured wrapper error with captured stdout/stderr. |

## Safer Command Discovery

`shopify commands --json` is the best available inventory source. It includes command IDs, summaries, flags, env var bindings, and types. It is not a full tool manifest: it lacks stable exit-code declarations, credential scope requirements, interactivity markers, max output bounds, and JSON envelope contracts.

## Known Indeterminate Area

Credential expiry behavior was not evaluated because no controlled authenticated Shopify session with expiring credentials was available. Treat expiry, permission denied, and auth-required states as ambiguous unless your wrapper can distinguish them from observed output.
