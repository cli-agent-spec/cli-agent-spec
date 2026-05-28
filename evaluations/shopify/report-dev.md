# shopify — CLI Author Fix List

**Generated:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Scope:** Critical
**Findings:** 22 Critical checks, average 0.6/3

## Highest-Impact Fixes

1. Add a machine-readable command manifest.
   Include commands, typed flags, exit codes, credential scopes, interactivity requirements, auth methods, destructive-operation declarations, max output limits, and schema version/etag.

2. Standardize JSON envelopes.
   Every command should be able to emit `ok`, `data`, `error`, `warnings`, and `meta`; failures should use the same envelope as successes.

3. Make non-interactive behavior explicit.
   In non-TTY mode, auth, REPL, editor, browser, and prompt paths should exit quickly with structured errors such as `AUTH_REQUIRED`, `INTERACTIVE_REQUIRED`, or `STDIN_REQUIRED`.

4. Add agent-safe mutation semantics.
   Mutating commands need idempotency keys, dry-run support where possible, `effect` fields, partial-failure step reporting, and retry/resume guidance.

5. Separate command output from product notifications and telemetry errors.
   Release notes, analytics failures, and local preference write errors should not appear in stdout for command results.

## Concrete Gaps

| §N | Gap | Suggested implementation |
|---|---|---|
| §45 | Headless auth blocks | Emit JSON auth-required responses in non-TTY; include auth methods and reauth command. |
| §37 §50 | REPL/stdin paths block | Guard interactive commands at startup when stdin is not a TTY. |
| §43 | Unbounded output | Add `--max-output`, default output caps, and `meta.truncated`/`meta.total_bytes`. |
| §1 | Exit codes undocumented | Publish an exit-code table and include the code in JSON errors. |
| §24 | Secret flags accepted | Prefer env/file-based secret injection and mark sensitive args for redaction. |
| §74 | No scope declaration | Add `required_scopes` per command and a `check-permissions` preflight. |

## What Already Helps

`shopify commands --json` is a strong starting point. It is already parseable and carries useful Oclif flag metadata, including env var bindings and types. Extending that into a stable manifest would close several agent-readiness gaps at once.
