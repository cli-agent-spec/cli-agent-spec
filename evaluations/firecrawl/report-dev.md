# Firecrawl CLI - Developer Fix List

**Generated:** 2026-05-27
**Version:** 1.18.1
**Scope:** Critical

## Priority Fixes

1. Make unauthenticated commands return non-zero structured `AUTH_REQUIRED` JSON with `auth_methods`, never a prompt on stdout under non-TTY.
2. Make `--json` global and invariant: every success and failure should use `ok`, `data`, `error`, `warnings`, and `meta`.
3. Add `firecrawl --schema` with commands, flags, exit codes, required scopes, auth methods, interactivity, safe defaults, and output limits.
4. Change browser auth in headless/non-TTY mode to emit URL JSON and exit, or require an explicit wait flag.
5. Add dry-run/effect/idempotency contracts for setup/config-mutating commands.
6. Add documented output limits with `meta.truncated` and `meta.total_bytes`.

## Scorecard

| Bucket | Count |
|---|---:|
| Pass | 0 |
| Partial | 9 |
| Fail | 12 |
| Indeterminate | 2 |

## Failing Critical Rows

- §1 - Exit Codes & Status Signaling: Failures collapse to exit 1, auth-required scrape exits 0 after printing a prompt, and no JSON error body carries exit_code.
- §10 - Interactivity & TTY Requirements: config/scrape print an interactive auth prompt under stdin=/dev/null; login --browser waits for browser auth until external timeout.
- §12 - Idempotency & Safe Retries: No --idempotency-key support or effect field found on mutating/setup commands.
- §13 - Partial Failure & Atomicity: Multi-step init has no structured completed_steps, failed_step, resume token, or rollback support; --skip-skills run still reported skills installed.
- §23 - Side Effects & Destructive Operations: logout rejects --dry-run; setup/init/logout expose side effects without dry-run, machine-readable danger_level, or effect fields.
- §25 - Prompt Injection via Output: External scrape/search content is not wrapped in a trusted/untrusted envelope; single-format outputs are raw content and no trusted:false metadata is advertised.
- §43 - Tool Output Result Size Unboundedness: No --max-output/--max-length limit or meta.truncated/meta.total_bytes contract is documented or exposed in help.
- §45 - Headless Authentication / OAuth Browser Flow Blocking: Unauthenticated commands print a login prompt to stdout and exit 0; browser login waits for auth instead of returning structured AUTH_REQUIRED/auth_methods.
- §53 - Credential Expiry Mid-Session: Invalid credentials return prose Unauthorized text only; no CREDENTIALS_EXPIRED/PERMISSION_DENIED distinction or reauth_command field was found.
- §64 - Headless Display and GUI Launch Blocking: login --browser emits a URL but then waits for browser authentication and timed out in headless/non-TTY execution.
- §74 - Credential Scope Declaration Absence: No --schema/manifest/check-permissions command and no per-command required_scopes declaration were found.
- §75 - Safe-Default Execution Mode Absent: No safe_default manifest, --live contract, dry-run default, or meta.dry_run/effect output exists for side-effecting commands.

## Partial Rows

- §2 - Output Format & Parseability: Several commands expose --json, but auth and error paths emit prose/prompts or stderr text without ok/data/error envelope.
- §11 - Timeouts & Hanging Processes: search/crawl expose timeout flags, but connection failure returns prose stderr and exit 1, not structured TIMEOUT metadata.
- §24 - Authentication & Secret Handling: FIRECRAWL_API_KEY is supported and invalid-key errors did not echo the tested value, but --api-key accepts secrets on the command line and auth prompts are prose.
- §34 - Shell Injection via Agent-Constructed Commands: Unknown --name was rejected, but rejection is prose only; --output accepts arbitrary paths and no structured VALIDATION_ERROR/suggestion exists.
- §42 - Debug / Trace Mode Secret Leakage: --token/--debug are rejected without echoing the tested token, but --api-key secrets are accepted as CLI args and no trace-safe/schema sensitivity metadata exists.
- §50 - Stdin Consumption Deadlock: Non-TTY auth prompts return promptly, but no STDIN_REQUIRED structured error or hint is emitted.
- §60 - OS Output Buffer Deadlock: Long-running browser auth emits progress text but no JSON heartbeat, elapsed_ms, or step metadata.
- §61 - Bidirectional Pipe Payload Deadlock: A 70KB stdin payload to view-config exited, but no stdin size limit, STDIN_TOO_LARGE error, --input-file alternative, or schema declaration exists.
- §71 - Non-Interactive Installation Absence: README/docs document non-interactive npm/npx install and local npm install was idempotent; no AGENTS.md verify command makes this a 3/3.
