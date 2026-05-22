# Langfuse CLI — Integration Guide for Agent Builders

**Generated:** 2026-05-22  
**Binary:** `./node_modules/.bin/langfuse`

## Recommended Invocation

Use the project-local binary and prefer environment variables for credentials:

```sh
LANGFUSE_PUBLIC_KEY=pk-lf-... \
LANGFUSE_SECRET_KEY=sk-lf-... \
LANGFUSE_HOST=https://cloud.langfuse.com \
./node_modules/.bin/langfuse api __schema --json
```

## Invariants

- Always set a subprocess timeout externally; the CLI does not expose `--timeout`.
- Always pass `stdin` as `/dev/null` or equivalent for agent calls.
- Prefer `--json` for API execution, but be prepared for prose usage output on parser errors.
- Use `--curl` to preview requests before mutations or destructive operations.
- Do not pass secrets in CLI args when avoidable; use `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST`.
- Treat any exit code `1` as ambiguous. Parse stdout/stderr for the real failure category.
- Add your own output caps around command stdout because the CLI does not declare truncation metadata.

## Workarounds

For mutations, query current state before retrying. If a previous attempt may have succeeded, reconcile by name or ID before issuing another create/delete request.

For destructive operations, run with `--curl` first and inspect the generated URL/method. The CLI does not provide `--dry-run`.

For structured parsing, first try JSON parse. If parsing fails, classify known prose patterns such as `missing required argument`, `unknown command`, `Missing --username for basic auth`, and `fetch failed`.

For credential setup, provide project-scoped Langfuse API keys. The CLI does not expose per-command `required_scopes`.
