# firecrawl - Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-05-27 | Failures collapse to exit 1, auth-required scrape exits 0 after printing a prompt, and no JSON error body carries exit_code. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-05-27 | Several commands expose --json, but auth and error paths emit prose/prompts or stderr text without ok/data/error envelope. |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 | 2026-05-27 | config/scrape print an interactive auth prompt under stdin=/dev/null; login --browser waits for browser auth until external timeout. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | 2026-05-27 | search/crawl expose timeout flags, but connection failure returns prose stderr and exit 1, not structured TIMEOUT metadata. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-05-27 | No --idempotency-key support or effect field found on mutating/setup commands. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-05-27 | Multi-step init has no structured completed_steps, failed_step, resume token, or rollback support; --skip-skills run still reported skills installed. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-05-27 | logout rejects --dry-run; setup/init/logout expose side effects without dry-run, machine-readable danger_level, or effect fields. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-05-27 | FIRECRAWL_API_KEY is supported and invalid-key errors did not echo the tested value, but --api-key accepts secrets on the command line and auth prompts are prose. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-05-27 | External scrape/search content is not wrapped in a trusted/untrusted envelope; single-format outputs are raw content and no trusted:false metadata is advertised. |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-05-27 | Unknown --name was rejected, but rejection is prose only; --output accepts arbitrary paths and no structured VALIDATION_ERROR/suggestion exists. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | ?/3 | 2026-05-27 | No REPL or shell subcommand was found to run the specified check; no schema exists to declare requires_interactive. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-05-27 | --token/--debug are rejected without echoing the tested token, but --api-key secrets are accepted as CLI args and no trace-safe/schema sensitivity metadata exists. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-05-27 | No --max-output/--max-length limit or meta.truncated/meta.total_bytes contract is documented or exposed in help. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 | 2026-05-27 | Unauthenticated commands print a login prompt to stdout and exit 0; browser login waits for auth instead of returning structured AUTH_REQUIRED/auth_methods. |
| §50 | Stdin Consumption Deadlock | Critical | 1/3 | 2026-05-27 | Non-TTY auth prompts return promptly, but no STDIN_REQUIRED structured error or hint is emitted. |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-05-27 | Invalid credentials return prose Unauthorized text only; no CREDENTIALS_EXPIRED/PERMISSION_DENIED distinction or reauth_command field was found. |
| §60 | OS Output Buffer Deadlock | Critical | 1/3 | 2026-05-27 | Long-running browser auth emits progress text but no JSON heartbeat, elapsed_ms, or step metadata. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | 2026-05-27 | A 70KB stdin payload to view-config exited, but no stdin size limit, STDIN_TOO_LARGE error, --input-file alternative, or schema declaration exists. |
| §62 | $EDITOR and $VISUAL Trap | Critical | ?/3 | 2026-05-27 | No editor-requiring Firecrawl subcommand was found to run the specified check; no schema exists to declare requires_editor or alternatives. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 0/3 | 2026-05-27 | login --browser emits a URL but then waits for browser authentication and timed out in headless/non-TTY execution. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-05-27 | README/docs document non-interactive npm/npx install and local npm install was idempotent; no AGENTS.md verify command makes this a 3/3. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-05-27 | No --schema/manifest/check-permissions command and no per-command required_scopes declaration were found. |
| §75 | Safe-Default Execution Mode Absent | Critical | 0/3 | 2026-05-27 | No safe_default manifest, --live contract, dry-run default, or meta.dry_run/effect output exists for side-effecting commands. |
