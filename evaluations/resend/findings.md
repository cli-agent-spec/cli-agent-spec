# resend — Findings

| Failure mode | Title | Severity | Score | Notes |
|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | `--html-file work/../work/traversal-test.html` was accepted and read during dry-run; no traversal/metacharacter rejection or structured suggestion. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | No REPL/shell subcommand is exposed; `login -q` without `--key` exits immediately with structured JSON instead of entering an interactive flow. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 | No `--debug`/`--trace` mode exists and `whoami` masks `--api-key`; no schema marks sensitive fields or trace-safe mode. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | `emails send --html-file work/large.html --dry-run -q` returned 70,166 bytes with no `meta.truncated`, `meta.total_bytes`, or output cap. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | Authenticated command with no key exits promptly as JSON `auth_error`, but lacks `AUTH_REQUIRED` and `auth_methods`. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | `emails batch --file - -q` exits promptly; empty stdin yields `invalid_json`, but there is no `STDIN_REQUIRED` code or hint. |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 | Could not safely create or mock an expired Resend credential; docs list `auth_error`/`validation_failed` but no `CREDENTIALS_EXPIRED` check was runnable. |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 | Long-running commands document NDJSON output per event, but no heartbeat interval, elapsed metadata, or liveness output is documented/exposed. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | `emails batch --file - -q` accepts a >64KB stdin payload and exits without deadlock, but no stdin size limit or `STDIN_TOO_LARGE` error exists. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | Command tree exposes no editor-like command or option; no path launches `$EDITOR`/`$VISUAL`. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 | `open`/`docs` help says they open the default browser; code invokes the OS opener even with `--quiet`/`--json`, with no JSON URL fallback. |
| §71 | Non-Interactive Installation Absence | Critical | 3/3 | `npm install -g resend-cli --no-fund --no-audit` is documented and idempotent; second run exited 0 and `--version` is parseable. |
| §10 | Interactivity & TTY Requirements | Critical | 3/3 | Non-TTY login and delete paths fail fast with JSON (`missing_key`, `confirmation_required`); prompts are suppressed. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | SDK calls are wrapped with an internal 30s timeout, but no user-configurable `--timeout`, dedicated `TIMEOUT` error code, or partial result metadata is exposed. |
| §12 | Idempotency & Safe Retries | Critical | 1/3 | Only `emails send` and `emails batch` expose `--idempotency-key`; most mutating commands lack it and responses do not expose `effect`. |
| §13 | Partial Failure & Atomicity | Critical | 1/3 | `emails batch` has `--batch-validation permissive`, but no `completed_steps`, `failed_step`, resume token, or rollback flag is exposed. |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 | Delete/revoke commands require `--yes` in non-TTY, but destructive commands lack universal `--dry-run`, machine-readable `danger_level`, and `effect`. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | Env auth is documented and output masks keys, but `--api-key` and `login --key` accept secrets in argv; `whoami` reports a fake flag key as authenticated. |
| §25 | Prompt Injection via Output | Critical | 0/3 | Dry-run returns user-supplied HTML as raw JSON under `request.html`; no `trusted:false`, content-type marker, or external-data wrapper. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | `resend commands` contains no `required_scopes`; no `check-permissions` preflight; docs do not declare minimal scopes per command. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | Error docs state all errors exit `1`; observed validation, auth, unknown-command, and API errors all exit `1` with no `exit_code` in JSON. |
| §2 | Output Format & Parseability | Critical | 1/3 | JSON mode exists, but envelopes vary (`dryRun`/`request`, `error`, `ok`/`checks`) and do not consistently include `ok`, `data`, `warnings`, or `meta`. |
