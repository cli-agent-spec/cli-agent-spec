# Langfuse CLI — Fix List for CLI Authors

**Generated:** 2026-05-22  
**Version:** `langfuse-cli` 0.0.10  
**Scope:** Critical failure modes

## Priority Fixes

1. Make `--json` universal.
   Parser errors, missing required arguments, unknown commands, validation failures, and auth failures should all return a stable envelope such as `{"ok":false,"error":{"code":"VALIDATION_ERROR","message":"...","exit_code":2}}` when `--json` is present. Today these paths print prose usage text.

2. Publish semantic exit codes.
   Define and document stable codes for validation, auth required, auth expired, permission denied, not found, timeout/network, and unexpected failure. Include the code in JSON error bodies.

3. Add machine-readable auth metadata.
   `api __schema --json` should include required auth variables and command-level credential requirements. Missing auth should return `AUTH_REQUIRED` with `auth_methods`, for example `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`.

4. Add safe mutation controls.
   Mutating commands should expose `--idempotency-key` and return `effect` (`created`, `updated`, `noop`). Destructive commands should expose `--dry-run`, affected scope, and explicit danger metadata.

5. Add output-size controls.
   Provide a universal `--max-output` or `--max-bytes` flag, default limits for large payloads, and `meta.truncated` / `meta.total_bytes` in JSON responses.

6. Add an agent manifest.
   A top-level `langfuse --manifest` or `langfuse --schema` should return typed commands, flags, exit codes, auth methods, required scopes, mutability/danger level, and output-size defaults. Current top-level unknown schema flags print help and exit 0.

## Critical Scorecard

Passing: §37, §50, §61, §62, §64, §10  
Partial: §34, §42, §45, §71, §11, §24, §2  
Failing: §43, §12, §23, §25, §74, §1  
Indeterminate: §53, §60, §13

## Notes

The CLI already has a good foundation: local npm install works, API discovery exists, `--curl` is useful, and the bundled OpenAPI spec is co-versioned with the package. Most gaps are in agent-facing contracts around errors, safety, and structured metadata rather than basic command availability.
