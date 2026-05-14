# gws — Issues

### §1 candidate — Auth failures exit 0
`gws drive files list` returns a JSON auth error but exits 0 instead of a non-zero auth code. Discovered during §1 evaluation on 2026-05-14. Auth errors are indistinguishable from success by exit code alone on list commands.

### §53 — Credential expiry indistinguishable from permission denial
`reason: "authError"` is used for both expired tokens (invalid_rapt) and permanent permission denial. No `CREDENTIALS_EXPIRED` code, no `reauth_command`, no `expired_at`. Agents cannot safely auto-retry. Discovered during §53 evaluation on 2026-05-14.

### §45 candidate — Missing AUTH_REQUIRED structured error
Missing credentials produce `reason: "authError"` (same as expiry). No `auth_methods` array to guide the agent toward the correct auth method. Discovered during §45 evaluation on 2026-05-14.

### §43 candidate — No response body size limit
`--page-limit` limits pagination pages but not individual response body size. A single large document or email body is returned in full with no `meta.truncated` signal. Discovered during §43 evaluation on 2026-05-14.

### §11 candidate — No timeout mechanism
No `--timeout` flag. Network hangs would block indefinitely with no structured error or defined exit code. Discovered during §11 evaluation on 2026-05-14.

### §42 candidate — ANSI codes in debug stderr
`GOOGLE_WORKSPACE_CLI_LOG=gws=debug` emits ANSI escape sequences to stderr. Agents capturing stderr for error parsing will receive polluted output. Discovered during §42 evaluation on 2026-05-14.

### §64 — No headless auth alternative for `gws auth login`
`gws auth login` opens a browser with no `--print-url` or `--no-browser` flag. Headless agents must pre-set `GOOGLE_WORKSPACE_CLI_TOKEN` externally — no in-band alternative. Discovered during §64 evaluation on 2026-05-14.
