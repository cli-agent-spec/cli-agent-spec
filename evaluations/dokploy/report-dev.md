# dokploy — CLI Author Fix List

**Generated:** 2026-05-26  
**CLI version:** 0.3.0  
**Scope:** Critical failure modes

## Priority Fixes

1. Add a consistent structured response envelope for every command path.

   Use `{"ok": true, "data": ..., "warnings": [], "meta": ...}` for success and `{"ok": false, "error": {"code": "...", "message": "...", "retryable": false}, "meta": ...}` for errors. Make auth/config failures respect `--json`.

2. Define semantic exit codes and document them in `--help` or `--schema`.

   Current failures collapse to exit 1. Agents need distinct codes for validation, auth required, permission denied, timeout, network failure, partial failure, and credential expiry.

3. Ship `dokploy --schema`.

   Include commands, flags, required fields, output format, exit codes, auth requirements, required scopes, danger level, idempotency support, and max output bytes. The source repo already has OpenAPI data; expose it as a stable CLI contract.

4. Add safe mutation controls.

   Generated mutating/destructive commands should support `--dry-run`, `--idempotency-key`, and an `effect` field (`created`, `updated`, `deleted`, `noop`, `would_delete`). Destructive commands should declare `danger_level` and preview affected scope.

5. Move secrets out of argv.

   Keep `DOKPLOY_API_KEY` and `DOKPLOY_AUTH_TOKEN`, but deprecate token/password/key flags or add `--secret-from-env` and `--secret-from-file`. Redact sensitive values globally.

6. Add caller-visible timeout behavior.

   Configure Axios timeouts, expose `--timeout`, emit structured `TIMEOUT` errors, and include duration metadata. For long-running operations, add job IDs or heartbeats.

7. Fix version identity.

   Make `dokploy --version` return the npm package version (`0.29.4` at audit time), not the hard-coded `0.3.0`, so agents can correlate behavior with releases.

## Current Critical Scorecard

| Bucket | Count | Modes |
|---|---:|---|
| Passing | 6 | §10, §37, §50, §61, §62, §64 |
| Partial | 6 | §2, §24, §34, §42, §45, §71 |
| Failing | 10 | §1, §11, §12, §13, §23, §25, §43, §53, §60, §74 |
| Indeterminate | 0 | none |
