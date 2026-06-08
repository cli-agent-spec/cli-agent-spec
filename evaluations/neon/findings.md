# neonctl — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-06-06 | Uses typed/choice validation for some flags, but no structured `VALIDATION_ERROR`; metacharacter hardening is not declared in schema. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 1/3 | 2026-06-06 | `psql`/interactive-adjacent commands exist but no manifest declares interactive requirements; no structured `INTERACTIVE_REQUIRED` contract. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-06-06 | Invalid secret was not echoed in tested errors, but credentials are accepted as `--api-key` argv and no schema marks sensitive fields. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-06-06 | No `--max-output`, `meta.truncated`, `meta.total_bytes`, or schema-declared output limits found. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 | 2026-06-06 | `neonctl auth` in non-TTY emitted a browser auth URL and did not exit within the timeout; no JSON `AUTH_REQUIRED` response. |
| §50 | Stdin Consumption Deadlock | Critical | 0/3 | 2026-06-06 | `neonctl init` without `--agent` prompted for editor selection and timed out under `stdin=DEVNULL`. |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-06-06 | Auth failures are generic/prose and no `CREDENTIALS_EXPIRED`, `expired_at`, `reauth_command`, or distinct expiry exit code is declared. |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 | 2026-06-06 | Long-running `init --agent` produced terminal spinner/progress output with ANSI control sequences, not structured JSON heartbeats. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | ?/3 | 2026-06-06 | No stdin payload command was identified for a safe large-payload test; no manifest declares stdin limits or `--input-file`. |
| §62 | $EDITOR and $VISUAL Trap | Critical | ?/3 | 2026-06-06 | No editor-requiring command was identified for a direct test; no manifest declares editor requirements or alternatives. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 | 2026-06-06 | Auth launches a browser flow in non-TTY/headless conditions and does not return a structured JSON URL/fallback. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-06-06 | `npm i -g neonctl` is documented and worked; install is not documented in AGENTS.md and no dedicated health-check docs were found. |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 | 2026-06-06 | `auth` and `init` have interactive paths that block or timeout in non-TTY contexts. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | 2026-06-06 | No user-facing `--timeout` or heartbeat control; auth/init paths exceeded subprocess timeouts. API client has a hardcoded 60s timeout. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-06-06 | No idempotency key, effect field, or all-mutating-command dry-run contract found. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-06-06 | No structured `partial`, `completed_steps`, `failed_step`, `resume_from`, or rollback contract found. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-06-06 | Destructive commands such as project/branch/database/role delete expose no `--dry-run`, danger level, or required confirm flag in help. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-06-06 | `NEON_API_KEY` exists and invalid secrets were not echoed, but `--api-key` accepts secrets in argv and failed auth can delete configured credentials. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-06-06 | JSON writer emits raw command data without trusted/untrusted annotations or structural wrapping of external fields. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-06-06 | OAuth scopes appear in auth URL, but commands do not declare per-command `required_scopes`; no `check-permissions` preflight. |
| §75 | Safe-Default Execution Mode Absent | Critical | 0/3 | 2026-06-06 | No `safe_default`, default dry-run mode, `--live`, or `meta.dry_run` contract found. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-06-06 | Failures observed as exit 1 with prose stderr; no semantic exit code table or JSON error body with exit code. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-06-06 | `--output json` exists, and `link --agent` emits JSON, but errors often go to prose stderr and normal JSON lacks a consistent `ok`/`data`/`error` envelope. |
