# neon - Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-07-05 | `projects create --name acme%2Fwidgets --output ../../etc/test` rejected only the output enum in prose; no structured validation error or traversal/metacharacter hardening was observed. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 0/3 | 2026-07-05 | `psql` in non-TTY with no credentials entered browser OAuth and timed out instead of emitting a structured interactive-required error. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-07-05 | Invalid `--api-key` did not echo the canary in output, but secrets are accepted as CLI args and no safe trace/schema sensitive-field support was found. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-07-05 | Help and docs expose no `--max-output` or truncation metadata contract such as `meta.truncated` and `meta.total_bytes`. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 | 2026-07-05 | Authenticated commands without credentials launch browser OAuth and hang until killed; no JSON `AUTH_REQUIRED` response was emitted. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | 2026-07-05 | Documented `api --data -` syntax exits immediately as `Unknown command: -`; no structured `STDIN_REQUIRED` code or hint is emitted. |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 | 2026-07-05 | Could not safely mock an expired Neon credential; invalid API key produced only prose auth failure, not enough to score expiry behavior. |
| §60 | OS Output Buffer Deadlock | Critical | ?/3 | 2026-07-05 | No safe credential-free long-running Neon command was available after login-triggering probes were stopped. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | 2026-07-05 | Large stdin to documented `api --data -` path failed early with `Unknown command: -` and probe-side EPIPE; no stdin size limit or `STDIN_TOO_LARGE` response was observed. |
| §62 | $EDITOR and $VISUAL Trap | Critical | ?/3 | 2026-07-05 | Editor paths appear inside embedded psql, but exercising them requires a live psql session; no safe credential-free check was available. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 | 2026-07-05 | `neon auth` with `DISPLAY=` still launched browser OAuth and timed out instead of returning a headless JSON fallback URL. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-07-05 | `npm i -g neon` is documented and idempotent, and `--version` verifies; install guidance is not in an agent-specific `AGENTS.md`. |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 | 2026-07-05 | Non-TTY `link --no-checks` and `psql` probes entered browser OAuth and timed out rather than suppressing prompts automatically. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | 2026-07-05 | No user-facing `--timeout` was found, and no-credential auth paths exceeded the probe timeout without a CLI-produced timeout error. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-07-05 | Mutating command help exposes no `--idempotency-key`, no `effect` field contract, and no framework-level retry idempotency signal. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-07-05 | Multi-step workflows do not expose a general `partial`, `completed_steps`, `failed_step`, or resume token contract in help or manifest output. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-07-05 | `projects delete` exposes no `--dry-run`, no machine-readable danger level, and no affected-scope preview contract. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-07-05 | `NEON_API_KEY` exists, and the invalid canary was not echoed, but `--api-key` accepts secrets on the command line and auth failures are prose with exit 1. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-07-05 | No response envelope or `trusted: false` convention was observed; `api` is designed to return external API content directly. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-07-05 | No CLI manifest/schema or `check-permissions` command exists, so commands do not declare machine-readable required scopes. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-07-05 | Validation, missing-argument, and auth failures all exited 1 with prose stderr and no JSON exit-code body or documented semantic code table. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-07-05 | `--output json` exists globally, but errors still emit prose stderr with empty stdout and no consistent `ok`/`data`/`error` envelope. |
