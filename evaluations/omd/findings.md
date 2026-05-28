# omd — Findings

| Failure mode | Title | Severity | Score | Notes |
|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 2/3 | Encoded separators and traversal file paths are rejected with structured `ARG_ERROR`; response lacks a correction `suggestion` and schema lacks `agent_hardening`. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | No REPL/shell subcommand is exposed; no reachable interactive shell mode was found in help/schema. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 | Verbose auth status with `--token audit-secret-123` did not echo the secret; schema does not mark sensitive fields and CLI args can still expose secrets in process listings. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | `--skills --skills-content` emits full content with no `meta.truncated`, `meta.total_bytes`, `--max-output`, or schema-declared `max_output_bytes`. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | Non-TTY auth paths exit immediately, including SSO, but errors do not include `auth_methods`; schema lacks `requires_auth`/`auth_methods`. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | `csv import --input -` with stdin closed exits immediately, but reports a CSV validation error rather than structured `STDIN_REQUIRED` with a hint. |
| §53 | Credential Expiry Mid-Session | Critical | 1/3 | Expired token path mentions expiry in text, then emits `AUTH_REQUIRED`; no `CREDENTIALS_EXPIRED`, `expired_at`, or `reauth_command`. |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 | Streaming/page features exist, but no heartbeat contract or heartbeat interval was found for long-running commands. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | Large stdin to `csv import --input -` exits without deadlock, but no stdin size limit or `STDIN_TOO_LARGE`; file alternatives exist only on some commands. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | No editor-requiring command is exposed; no `$EDITOR`/`$VISUAL` launch path found in help/schema. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 1/3 | Non-TTY SSO is blocked cleanly instead of launching a browser, but schema does not declare GUI operations or headless behavior. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | README documents non-interactive Cargo install/build and local `cargo build` is idempotent; AGENTS.md lacks a complete install plus verify command. |
| §10 | Interactivity & TTY Requirements | Critical | 3/3 | Non-TTY SSO and dry-run mutation paths exit immediately with structured JSON; no prompt, pager, or editor hang observed. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | `--timeout 1` against a hanging loopback server exits in about 1s, but returns `GENERAL_ERROR` with exit 1 rather than `TIMEOUT` with a defined timeout exit code. |
| §12 | Idempotency & Safe Retries | Critical | 1/3 | `--idempotency-key` is accepted on mutating dry-run, but output lacks an `effect` field and true retry/noop semantics were not verifiable without a server. |
| §13 | Partial Failure & Atomicity | Critical | 2/3 | Source includes structured cancellation envelopes with `partial` and `completed_steps`; no resume token, rollback flag, or step manifest was found. |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 | Dry-run is available for mutation preview, but output lacks `effect: would_delete`, affected scope, and machine-readable `danger_level`. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | Env-var alternatives exist and tested errors did not echo token values, but `--token` and `--password` flags are still accepted for secrets. |
| §25 | Prompt Injection via Output | Critical | 3/3 | Output layer marks external data as `_source: external`/`_trusted: false`, includes sanitization, and exposes `--no-injection-protection`. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | `--schema` command entries do not include `required_scopes`; no `check-permissions` command or machine-readable scope report exists. |
| §1 | Exit Codes & Status Signaling | Critical | 1/3 | Semantic exit codes exist in behavior/source, but help/schema do not declare a full table, JSON errors omit `exit_code`, and clap argument errors can bypass the JSON envelope. |
| §2 | Output Format & Parseability | Critical | 2/3 | Normal commands support consistent JSON envelopes and auto-JSON in non-TTY, but meta lacks `request_id` and invocation errors can still emit prose to stderr. |
