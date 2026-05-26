# dokploy — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-05-26 | Source uses Commander and Axios rather than shell execution, but generated command arguments are only type/presence checked; encoded slashes and path traversal strings are not rejected before API calls. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | 2026-05-26 | No REPL, shell, or interactive console subcommands were found in help or source. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-05-26 | No debug/trace mode was found and auth failure did not echo the token, but secrets are accepted through `--token` and other generated flags such as `--password`, leaving values visible in argv/process listings. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-05-26 | Generated API commands print raw responses and expose no `--max-output`, truncation metadata, total byte count, or schema-declared output limits. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | 2026-05-26 | Auth is headless-friendly via env vars/API key and does not launch a browser, but unauthenticated commands emit prose only and no structured `AUTH_REQUIRED` error or `auth_methods` field. |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 | 2026-05-26 | No stdin-reading command paths were found in source or help; commands use flags and environment variables. |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-05-26 | No structured distinction exists for expired credentials versus permission/network failures; Axios errors are printed as prose and exit 1. |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 | 2026-05-26 | Commands await the full Axios response and print once; no line-buffered progress, heartbeat, or long-running command metadata exists. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 | 2026-05-26 | No stdin payload command paths were found, so the bidirectional pipe deadlock class is not present. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | 2026-05-26 | No editor-requiring command paths were found in help or source. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 | 2026-05-26 | No browser/GUI launch command paths or `--open-browser` style options were found. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-05-26 | README documents `npm install -g @dokploy/cli`; install is non-interactive and idempotent, but no AGENTS.md install contract or documented verify command exists. |
| §10 | Interactivity & TTY Requirements | Critical | 3/3 | 2026-05-26 | Safe checks with stdin closed returned promptly; no prompts, pagers, editors, or browser flows were found. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | 2026-05-26 | No `--timeout` flag or Axios timeout is configured; network-dependent commands rely on caller-managed timeouts and prose errors. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-05-26 | Mutating commands expose no `--idempotency-key`, `effect`, or `--dry-run` contract. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-05-26 | No structured `partial`, `completed_steps`, `failed_step`, resume token, or rollback flag exists for multi-step operations. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-05-26 | Destructive commands such as `application delete` and `user remove` have no confirmation flag, `--dry-run`, `danger_level`, or affected-scope preview. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-05-26 | Env var auth exists and invalid-token test did not echo the token, but `auth -t/--token` and generated `--password`/`--apiKey`/`--token` flags accept secrets in argv. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-05-26 | `--json` prints raw external API data with no trusted/untrusted separation, response envelope, or injection-protection metadata. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-05-26 | No schema/manifest, `required_scopes`, `check-permissions`, or minimal-scope documentation exists. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-05-26 | Observed failures exit 1 and errors are prose; no exit code table or JSON error body exists. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-05-26 | Generated API commands support `--json`, but `--output json` is unknown, errors remain prose, and there is no consistent `ok`/`data`/`error` envelope. |
