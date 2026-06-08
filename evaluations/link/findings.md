# link-cli — Findings

| Failure mode | Title | Severity | Score | Notes |
|---|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-06-08: Validation, auth, unknown-flag, and network failures all exited 1; JSON errors omit `exit_code`; exit codes are not documented. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-06-08: `--format json` works, but default JSON output is a bare array/object and lacks consistent `ok`/`data`/`error` envelope unless `--full-output` is explicitly added. |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 | 2026-06-08: Interactive `demo` and `onboard` detect non-TTY and exit immediately with structured `REQUIRES_TTY`; auth login emits a URL and `_next` without opening a browser. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | 2026-06-08: API calls have no command-level timeout flag; unreachable API returned `UNKNOWN` after transport delay, not `TIMEOUT`, and no defined timeout exit code. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-06-08: Mutating command schemas expose no `--idempotency-key`, `effect`, or universal `--dry-run` mechanism. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-06-08: Multi-step polling returned a success envelope containing pending states after timeout; no `partial`, `completed_steps`, `failed_step`, rollback, or resume token fields. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-06-08: Destructive/mutating commands do not expose `--dry-run`, `danger_level`, `effect`, or explicit destructive confirmation metadata. |
| §24 | Authentication & Secret Handling | Critical | 2/3 | 2026-06-08: Access tokens are accepted via env vars and auth file paths, and invalid-token errors did not echo the token; errors still use generic `UNKNOWN` and exit 1. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-06-08: API/user-supplied data is returned as ordinary output fields; no default trusted/untrusted separation or external-content annotations were found. |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-06-08: Commands use structured flags, but schema validation is type-oriented; path-like values such as `outputFile` have no traversal or metacharacter hardening in schema. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 2/3 | 2026-06-08: Interactive-only commands exit immediately in non-TTY with structured `REQUIRES_TTY`; schemas do not declare `requires_interactive`. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 | 2026-06-08: No debug/trace mode or token CLI flag is accepted; unknown-flag errors did not echo a supplied secret, but schemas do not mark sensitive fields or provide `--trace-safe`. |
| §43 | Tool Output Result Size Unboundedness | Critical | 1/3 | 2026-06-08: Global `--token-limit` and truncation markers exist, but truncation is not represented as `meta.truncated` with `meta.total_bytes`, and schemas do not declare max output bytes. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | 2026-06-08: Auth-gated commands exit quickly with structured `NOT_AUTHENTICATED` and CTA, but not `AUTH_REQUIRED` with an `auth_methods` array. |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 | 2026-06-08: No ordinary CLI command path was found that reads required payloads from stdin; non-TTY stdin did not trigger blocking behavior in probed commands. |
| §53 | Credential Expiry Mid-Session | Critical | 1/3 | 2026-06-08: Expired env token produced a human-readable expired-token message, but the code was `UNKNOWN` and no `expired_at` or `reauth_command` field was provided. |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 | 2026-06-08: Long-running auth polling emitted all JSON output only at process exit, with no incremental JSON heartbeat while polling. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 | 2026-06-08: No ordinary CLI commands accept large stdin payloads; data input is flag-based, so the evaluated CLI surface avoids bidirectional stdin/stdout payload deadlock. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | 2026-06-08: No editor-requiring commands were present in the command tree; non-interactive alternatives are used instead of editor workflows. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 2/3 | 2026-06-08: Auth login emits a verification URL in JSON without launching a browser; schemas do not declare `gui_operations` or `headless_behavior`. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-06-08: `npm install -g @stripe/link-cli` is documented in README and reran successfully, but the repo lacks `AGENTS.md` install/verify guidance. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-06-08: Command schemas and manifests do not expose `required_scopes`, and no `check-permissions` preflight command was found. |
