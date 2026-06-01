# hevn — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-06-01 | Unknown flags and hostile-looking path values are rejected by Click/Typer prose errors, not structured `VALIDATION_ERROR` responses with suggestions. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | 2026-06-01 | No REPL or shell subcommand is exposed in top-level help, so there is no reachable REPL trigger. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 | 2026-06-01 | No global `--debug`/`--trace` or `--token` secret flag is accepted; secrets are primarily env/config based, but there is no schema marking sensitive inputs. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-06-01 | No `--max-output`/`--max-length`, truncation metadata, or default output envelope was found. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 | 2026-06-01 | `hevn login --no-open --json` prints an auth URL, waits for callback, then exits with prose timeout output; no immediate structured `AUTH_REQUIRED` with `auth_methods`. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | 2026-06-01 | `hevn mcp-key --json` reads a secret from stdin, emits getpass warnings, and aborts; it does not emit structured `STDIN_REQUIRED` guidance. |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-06-01 | Auth failures and missing credentials use generic messages; no distinct `CREDENTIALS_EXPIRED`, `expired_at`, or `reauth_command` contract is exposed. |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 | 2026-06-01 | Long-running paths such as login have no JSON heartbeat or line-buffering contract for agents. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | 2026-06-01 | Secret stdin prompt exists, but no stdin size limit, `STDIN_TOO_LARGE`, or `--input-file` alternative is documented. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | 2026-06-01 | No editor-requiring command was found in help or installed sources. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 | 2026-06-01 | `hevn login` calls `webbrowser.open()` by default and has no schema-declared headless behavior; `--no-open` is manual and still waits. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-06-01 | Non-interactive install from PyPI works and README documents install, but no AGENTS.md install contract or parseable `--version` verify command exists. |
| §10 | Interactivity & TTY Requirements | Critical | 1/3 | 2026-06-01 | Some prompts abort under non-TTY and some commands have `--yes`, but prompt paths still emit prose/warnings and there is no global non-interactive mode. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | 2026-06-01 | HTTP timeout is hardcoded and login has `--timeout`, but timeout errors are prose/exit 2 rather than structured JSON with defined timeout code. |
| §12 | Idempotency & Safe Retries | Critical | 1/3 | 2026-06-01 | `--idempotency-key` exists for transfer flows, but coverage is partial and responses do not declare `effect` semantics. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-06-01 | No structured `partial`, `completed_steps`, `failed_step`, resume token, or rollback contract found. |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 | 2026-06-01 | Destructive commands use confirmation/`--yes`, but no `--dry-run`, machine-readable `danger_level`, or `effect` field is exposed. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-06-01 | Env vars exist, but `hevn mcp-key` accepts secrets interactively/positionally and getpass emits terminal warnings in non-TTY. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-06-01 | External API/user fields are emitted as ordinary JSON/YAML or rich tables without trust annotations or untrusted-content envelopes. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-06-01 | No `--schema`, `required_scopes`, `check-permissions`, or over-privilege report is available. |
| §1 | Exit Codes & Status Signaling | Critical | 1/3 | 2026-06-01 | Exit codes 0/1/2 occur, but semantic codes are undocumented and JSON errors do not include `exit_code`. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-06-01 | Many commands support `--json`, but there is no global `--output json`, no consistent `ok/data/error/meta` envelope, and Typer validation errors remain prose. |
