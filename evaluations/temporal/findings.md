# temporal — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-07-07 | Missing args, not-found, and network/timeout failures all exited 1; no declared semantic code table or JSON error exit_code field was observed. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-07-07 | `--output json` exists and success paths return JSON, but validation and connection failures print prose/usage text instead of an ok/data/error envelope. |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 | 2026-07-07 | Local mutating config commands complete with stdin closed, and JSON destructive query commands require prompt bypass; no universal schema declares interactive paths. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | 2026-07-07 | `--command-timeout` and `--client-connect-timeout` work, but timeout/network failures exit 1 with `Error: program interrupted` rather than structured TIMEOUT JSON. |
| §12 | Idempotency & Safe Retries | Critical | 1/3 | 2026-07-07 | Workspace-local `env set` was repeatable, and workflow start has ID conflict/reuse policies, but no `--idempotency-key` or response `effect` contract exists. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-07-07 | A deliberate bad batch/query path returned a single prose error with no `partial`, `completed_steps`, `failed_step`, rollback, or resume token. |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 | 2026-07-07 | Query-based destructive commands have `--yes` prompt bypass and JSON mode refuses prompts, but destructive commands expose no `--dry-run`, `danger_level`, or effect field. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-07-07 | Temporal accepts API keys through `--api-key`, which exposes secrets in process arguments; a debug probe did not echo the test key in captured output. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-07-07 | User-controlled/local config data is returned as raw JSON values with no trust boundary, envelope, or `trusted: false` metadata. |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-07-07 | Some enum-style flags reject invalid values, but a `%2F`-encoded environment name was accepted and errors are unstructured; no agent-hardening declaration exists. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | 2026-07-07 | No REPL/shell subcommand was exposed; `temporal shell` exits immediately as an unknown command with stdin closed. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-07-07 | Debug logging did not echo the test API key, but secrets can still be supplied on argv and no schema marks sensitive fields. |
| §43 | Tool Output Result Size Unboundedness | Critical | 1/3 | 2026-07-07 | List commands expose `--limit`/`--page-size`, but outputs lack `meta.truncated`, total byte counts, or a global `--max-output` guard. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 2/3 | 2026-07-07 | Temporal uses API-key/config flags and no browser OAuth flow was observed; auth failures are not exposed as structured `AUTH_REQUIRED`/`auth_methods` envelopes. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | 2026-07-07 | Commands with missing required input failed quickly with usage/prose and did not block, but no structured `STDIN_REQUIRED` code or hint was emitted. |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 | 2026-07-07 | Could not safely create or mock an expired Temporal credential in this environment; behavior remains unverified. |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 | 2026-07-07 | `server start-dev` emitted startup lines, but no JSON heartbeat or progress protocol for long-running commands was observed. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | 2026-07-07 | Workflow input commands provide `--input-file`, but stdin size limits and `STDIN_TOO_LARGE` overflow errors were not observed. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | 2026-07-07 | No editor-requiring command was found; `temporal config edit` exits immediately as unknown with stdin closed. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 2/3 | 2026-07-07 | `server start-dev` documents `--headless` and prints service/UI URLs instead of opening a browser; no schema declares GUI/headless behavior. |
| §71 | Non-Interactive Installation Absence | Critical | 1/3 | 2026-07-07 | The binary is installed and `--version` works, but this audit workspace has no AGENTS.md/README documenting a non-interactive, idempotent install command. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-07-07 | `--schema`, `manifest`, and `check-permissions --for ...` are absent; command entries expose no `required_scopes` field. |
