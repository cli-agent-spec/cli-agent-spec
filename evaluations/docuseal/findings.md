# docuseal-cli - Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-05-20 | No shell execution path found, but suspicious name/path values are not validated into structured errors. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | 2026-05-20 | No REPL/shell subcommand found. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 | 2026-05-20 | No debug/trace mode found to leak secrets, but no sensitive schema/redaction declaration exists. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-05-20 | No output limit, truncation metadata, or schema max-output declaration. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | 2026-05-20 | Missing auth exits immediately, but as an uncaught stack trace rather than `AUTH_REQUIRED` with `auth_methods`. |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 | 2026-05-20 | No stdin-consuming command found. |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-05-20 | No distinct credential-expiry code, reauth command, or expiry metadata. |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 | 2026-05-20 | No streaming protocol or heartbeat for long-running commands. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 | 2026-05-20 | No stdin payload command found. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | 2026-05-20 | No editor-requiring command found. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 | 2026-05-20 | No GUI/open-browser command found. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-05-20 | README documents non-interactive npm install/use; no AGENTS.md install protocol and global install idempotency was not exercised. |
| §35 | Agent Hallucination Input Patterns | High | 0/3 | 2026-05-20 | Percent-encoded/path-like values are not rejected with structured validation suggestions. |
| §38 | Runtime Dependency Version Mismatch | High | 0/3 | 2026-05-20 | No `engines` declaration or startup runtime-version JSON check. |
| §40 | parse() vs parseAsync() Silent Race Condition | High | 0/3 | 2026-05-20 | Source uses `program.parse()` with async action handlers. |
| §41 | Update Notifier Side-Channel Output Pollution | High | 2/3 | 2026-05-20 | No update notifier found; CI/NO_UPDATE_NOTIFIER produced no side-channel notice. |
| §46 | API Schema to CLI Flag Translation Loss | High | 1/3 | 2026-05-20 | `-d` accepts JSON/bracket notation, but there is no full `--json` body flag or API-schema validation. |
| §47 | MCP Wrapper Schema Staleness | High | 0/3 | 2026-05-20 | No MCP wrapper health, schema version, or stale-schema mapping. |
| §49 | Async Job / Polling Protocol Absence | High | 0/3 | 2026-05-20 | No async job/status protocol or distinct running/done exit codes. |
| §51 | Shell Word Splitting and Glob Expansion Interference | High | 1/3 | 2026-05-20 | Exec-array invocation preserves spaced file paths, but missing files become unstructured `ENOENT` stack traces. |
| §54 | Conditional / Dependent Argument Requirements | High | 0/3 | 2026-05-20 | No machine-readable arg groups or all-at-once dependent-argument validation. |
| §55 | Silent Data Truncation | High | 0/3 | 2026-05-20 | No schema max lengths or `FIELD_TRUNCATED`/validation warning protocol. |
| §56 | Exit Code Masking in Shell Pipelines | High | 0/3 | 2026-05-20 | No `ok`, `meta.ok`, or `meta.exit_code` fields. |
| §58 | Multi-Agent Concurrent Invocation Conflict | High | 0/3 | 2026-05-20 | Config writes use direct writes to shared config; no locking or conflict code. |
| §59 | High-Entropy String Token Poisoning | High | 1/3 | 2026-05-20 | `configure --list` masks stored `api_key`, but there is no semantic token summary/unmask protocol. |
| §65 | Global Configuration State Contamination | High | 0/3 | 2026-05-20 | Config writes default to global user config without `--global` or write-scope metadata. |
| §66 | Symlink Loop and Recursive Traversal Exhaustion | High | 3/3 | 2026-05-20 | No recursive traversal command found. |
| §67 | Agent-Generated Input Syntax Rejection | High | 0/3 | 2026-05-20 | Strict JSON parse errors produce raw stack traces; no `INVALID_JSON` corrected input. |
| §68 | Third-Party Library Stdout Pollution | High | 0/3 | 2026-05-20 | No stdout interception or warnings envelope. |
| §69 | Argument Order Ambiguity | High | 1/3 | 2026-05-20 | Subcommand-level global flags work after the subcommand; root-level placement is rejected. |
| §70 | Single-Argument Arity Forcing Agent Loop Overhead | High | 0/3 | 2026-05-20 | Single-ID commands do not accept variadic IDs with per-item results. |
| §72 | Integration Artifact Version Drift | High | 0/3 | 2026-05-20 | Skill metadata version `1.0.6` differs from binary/package version `1.0.3`, confirming integration artifact drift. |
| §73 | Documentation Accuracy Drift | High | 1/3 | 2026-05-20 | No AGENTS.md; available CLAUDE/skill docs are useful but version drift exists. |
| §44 | Agent Knowledge Packaging Absence | Medium | 1/3 | 2026-05-20 | Repository ships CLAUDE.md and a skill, but no AGENTS.md/CONTEXT.md and no `--schema` danger/requires fields. |
| §52 | Recursive Command Tree Discovery Cost | Medium | 0/3 | 2026-05-20 | No `--schema` command tree; agents must recurse through help text. |
| §57 | Locale-Dependent Error Messages | Medium | 0/3 | 2026-05-20 | OS/file errors surface as raw stack traces, not normalized structured errors. |
| §63 | Terminal Column Width Output Corruption | Medium | 0/3 | 2026-05-20 | No JSON mode; help prose wraps at terminal width. |
| §10 | Interactivity & TTY Requirements | Critical | 1/3 | 2026-05-20 | `configure` has flags for non-interactive setup, but the prompt path still runs in non-TTY and can exit 0 without configuring. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | 2026-05-20 | Network failure produced an uncaught Node stack trace; no timeout flag or `TIMEOUT` JSON. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-05-20 | Mutating commands have no idempotency key or effect/noop field. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | 2026-05-20 | No partial-failure/resume protocol. |
| §14 | Argument Validation Before Side Effects | High | 1/3 | 2026-05-20 | Commander validates some arguments before execution, but exit code is generic and errors are not structured JSON. |
| §15 | Race Conditions & Concurrency | High | 0/3 | 2026-05-20 | No lock protocol for mutating/config operations. |
| §16 | Signal Handling & Graceful Cancellation | High | 0/3 | 2026-05-20 | No SIGTERM partial-result protocol. |
| §17 | Child Process Leakage | Medium | 3/3 | 2026-05-20 | No command found that spawns background child processes. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-05-20 | Destructive archive operations have no `--dry-run` or machine-readable danger declaration. |
| §24 | Authentication & Secret Handling | Critical | 0/3 | 2026-05-20 | Secrets can be supplied via hidden `--api-key` CLI flag; no standard redaction framework. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-05-20 | External API data is returned raw without a trusted/untrusted envelope. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-05-20 | No machine-readable required scopes or permission check command. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-05-20 | Failures observed with generic exit 1; no documented semantic exit-code table or JSON error body. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-05-20 | API commands emit JSON on success, but there is no `--output json` and no `ok`/`data`/`error` envelope; many errors are prose/stack traces. |
| §3 | Stderr vs Stdout Discipline | High | 1/3 | 2026-05-20 | Data is normally stdout, but help/prose success/error output can also appear on stdout. |
| §5 | Pagination & Large Output | High | 1/3 | 2026-05-20 | List commands expose limit/cursor flags, but no standard pagination metadata envelope. |
| §8 | ANSI & Color Code Leakage | High | 3/3 | 2026-05-20 | No ANSI escape sequences observed in piped/non-TTY output. |
| §9 | Binary & Encoding Safety | High | 2/3 | 2026-05-20 | File uploads use Buffer/base64 for binary content; error handling remains unstructured. |
| §4 | Verbosity & Token Cost | Medium | 1/3 | 2026-05-20 | No progress spam observed, but there is no quiet/fields control and CI does not activate structured mode. |
| §6 | Command Composition & Piping | Medium | 0/3 | 2026-05-20 | No `--output id` mode and no stdin `-` ID protocol. |
| §7 | Output Non-Determinism | Medium | 0/3 | 2026-05-20 | Raw API output has no stable-output mode or volatile-field isolation. |
| §26 | Stateful Commands & Session Management | High | 0/3 | 2026-05-20 | Implicit global config/env state; no `status --output json` context report. |
| §28 | Config File Shadowing & Precedence | High | 1/3 | 2026-05-20 | README documents precedence and `configure --list` shows config, but sources are not machine-readable. |
| §31 | Network Proxy Unawareness | High | 0/3 | 2026-05-20 | Network errors include no proxy context. |
| §32 | Self-Update & Auto-Upgrade Behavior | High | 3/3 | 2026-05-20 | No self-update behavior or update check found. |
| §27 | Platform & Shell Portability | Medium | 1/3 | 2026-05-20 | Node CLI is portable in principle, but there is no doctor command and failures are raw. |
| §29 | Working Directory Sensitivity | Medium | 0/3 | 2026-05-20 | File paths are resolved relative to CWD with no `meta.cwd` or framework `--cwd`. |
| §30 | Undeclared Filesystem Side Effects | Medium | 0/3 | 2026-05-20 | Config filesystem side effects are not declared or inventoried. |
| §18 | Error Message Quality | High | 0/3 | 2026-05-20 | Validation/auth/file/network errors are prose or stack traces without `code`, `suggestion`, or context. |
| §19 | Retry Hints in Error Responses | High | 0/3 | 2026-05-20 | No `retryable` or `retry_after_ms` fields. |
| §22 | Schema Versioning & Output Stability | High | 0/3 | 2026-05-20 | No `meta.schema_version` in responses. |
| §20 | Environment & Dependency Discovery | Medium | 0/3 | 2026-05-20 | No `doctor --output json` or structured dependency preflight. |
| §21 | Schema & Help Discoverability | Medium | 0/3 | 2026-05-20 | No `--schema --output json`; help is prose only. |
| §33 | Observability & Audit Trail | Medium | 0/3 | 2026-05-20 | No `request_id`, `duration_ms`, trace propagation, or audit log. |
