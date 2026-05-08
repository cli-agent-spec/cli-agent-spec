# Agent-Compatible CLI Checklist

> A condensed implementation checklist derived from the CLI Agent Spec's 71 documented failure modes.
> Use this to audit an existing CLI tool or verify a new one before agent deployment.

---

```
EXIT CODES
  □ Exit 0 only on true success
  □ Exit 2 exclusively for validation failures (no side effects occurred)
  □ Distinct codes for: error / not-found / timeout / permission / conflict
  □ Document all exit codes in --help and --schema

OUTPUT
  □ --output json mode with consistent schema
  □ Identical schema for 0, 1, N results
  □ effect field on all mutating commands ("created" | "updated" | "noop")
  □ pagination metadata on all list commands
  □ meta.request_id, meta.schema_version, meta.duration_ms in every response
  □ All array fields sorted in stable order
  □ data and meta separated (data = stable, meta = volatile)
  □ All paths in output are absolute

STREAMS
  □ Strict stdout=data, stderr=diagnostics separation
  □ --quiet suppresses all stderr
  □ Warnings included as warnings[] array in JSON output
  □ No ANSI/color codes in --output json mode (unconditional)
  □ NO_COLOR env var respected everywhere

INTERACTIVITY
  □ --non-interactive / --yes flags on all interactive commands
  □ --no-input: fail immediately if input would be needed
  □ Never open pager; respect PAGER=cat
  □ Auto-disable update checks when CI=true or non-TTY

RELIABILITY
  □ Built-in --timeout flag on all network/long-running commands
  □ --idempotency-key on all mutating commands
  □ --dry-run on all destructive/mutating commands
  □ Structured partial failure with completed_steps and resume_from
  □ All args validated before any side effects begin (--validate-only flag)
  □ retryable + retry_after_ms in every error response

SIGNALS & PROCESSES
  □ SIGTERM handler: emit partial JSON, cleanup, exit 143
  □ SIGPIPE handler: suppress BrokenPipeError, exit cleanly
  □ All child processes tracked and killed on parent exit
  □ Commands declare spawns_background_process and cleanup_command

ENCODING & SAFETY
  □ All strings sanitized to valid UTF-8 before JSON serialization
  □ Binary data encoded as base64 with {type, encoding, value} wrapper
  □ Null bytes replaced or escaped, never passed raw

SECURITY
  □ Accept secrets via env var and --secret-from-file, never --password
  □ Auto-redact secret fields in logs
  □ Tag external data as untrusted in output

CONFIG & ENVIRONMENT
  □ --show-config reveals effective configuration and sources
  □ --no-config disables all file-based config loading
  □ --cwd flag on all commands that touch the filesystem
  □ HTTP_PROXY / HTTPS_PROXY / NO_PROXY respected automatically
  □ Network errors include network_context (proxy used, SSL settings)

FILESYSTEM
  □ All filesystem_side_effects declared in command schema
  □ --no-cache flag on commands that write caches
  □ Temp files use session-scoped directory, auto-cleaned
  □ tool cleanup removes all known side-effect paths

SCHEMA & VERSIONING
  □ meta.schema_version in every response
  □ Deprecation warnings before field removal
  □ --schema outputs full machine-readable command manifest
  □ Stable/experimental/volatile field tiers declared
  □ tool update only updates on explicit command, never auto

DISCOVERABILITY
  □ tool doctor runs all preflight checks including proxy/network
  □ Each command documents exit codes, output schema, danger_level
  □ tool status --show-side-effects lists all written paths

OBSERVABILITY
  □ Request ID in every response
  □ TOOL_TRACE_ID env var propagated
  □ Structured audit log
  □ meta.tool_version and meta.cwd in every response

ECOSYSTEM & AGENT-SPECIFIC
  □ Reject shell metacharacters in agent-constructed arguments; never use shell=True
  □ Validate agent-specific hallucination patterns: path traversal, percent-encoding, embedded query params
  □ Ban pager invocation (echo_via_pager) in non-TTY contexts; set PAGER=cat automatically
  □ Gate REPL/shell subcommands on isatty(); return structured error if non-TTY
  □ Runtime version checked at startup; structured error with requirement/actual fields
  □ Help text always to stderr; never to stdout in non-TTY mode
  □ Async action handlers always awaited (parseAsync pattern); never silent void exit
  □ Update notifiers suppressed when CI=true or non-TTY; version in meta.update_available only
  □ Debug/trace modes redact sensitive fields; --trace-safe mode available
  □ Single large responses bounded with truncated + size_bytes in meta
  □ AGENTS.md or equivalent skill file ships with the tool
  □ AUTH_REQUIRED error includes auth_methods array; never hang on OAuth browser flow
  □ --json flag accepts raw API payload on all mutating commands
  □ MCP wrapper declares cli_version; emits SCHEMA_STALE on version mismatch
  □ Standard {ok, data, error, meta} envelope on all JSON responses
  □ Async job commands return job_id + status_command + poll_interval_ms; status uses exit 0/3/4/7
  □ Stdin reads declared in schema; non-TTY stdin reads fail immediately with exit 4
  □ Subprocess invocations use exec-array; stdin payload capped at 64KB with --input-file fallback
  □ --schema returns full command tree in single call; no N+1 help round trips needed
  □ Auth errors distinguish CREDENTIALS_EXPIRED (exit 10) from PERMISSION_DENIED (exit 8)
  □ Conditional argument dependencies declared in schema; all missing co-args reported in one error
  □ Field max_length/max_items declared; truncated fields appear in warnings[], never silently dropped
  □ .ok field in JSON envelope is authoritative; document that pipelines require pipefail or .ok check
  □ error.code always English machine-readable constant; error.message normalized to English (LC_MESSAGES=C)
  □ Config writes use file locking + atomic rename; --instance-id namespaces per-agent state
  □ High-entropy strings (JWTs, base64 blobs) masked by default; semantic summary shown; --unmask to reveal
  □ stdout unbuffered in non-TTY mode (PYTHONUNBUFFERED=1 / line_buffering=True); heartbeats every 10s
  □ $EDITOR/$VISUAL set to no-op in non-TTY mode; commands declare requires_editor with --from-file alt
  □ JSON output mode disables all terminal-width wrapping; never inject newlines into string values
  □ Detect headless (no DISPLAY/WAYLAND_DISPLAY); replace GUI/browser launches with URL in JSON output
  □ Config writes default to local scope; --global required for ~/.config writes; GLOBAL_CONFIG_MODIFIED warning emitted
  □ Recursive traversal tracks visited inodes; exits with SYMLINK_LOOP error on circular detection
  □ Accept JSON5 (trailing commas, comments) on all structured inputs; corrected_input in parse errors
  □ Framework intercepts third-party stdout at fd level; reclassifies prose writes to warnings[]
```

---

## File Structure

Each challenge lives in its own file under `challenges/`:

```
challenges/
  output-and-parsing/              §1–9
  execution-and-reliability/       §10–17
  errors-and-discoverability/      §18–22
  security/                        §23–25
  environment-and-state/           §26–32
  observability/                   §33
  ecosystem-runtime-agent-specific/ §34–68
```

**Consolidated challenges** (redirect stubs point to merged location):
- §36 Pager Invocation → merged into [`§10 Interactivity`](02-critical-execution-and-reliability/10-critical-interactivity.md)
- §39 Help Text to Stdout → merged into [`§3 Stderr/Stdout`](04-critical-output-and-parsing/03-high-stderr-stdout.md)
- §48 Output Envelope → merged into [`§2 Output Format`](04-critical-output-and-parsing/02-critical-output-format.md)

---

*Generated from agent operational experience and external project research (Gemini AMI, Antigravity-cli). Version 1.6 — 2026-04-01. 70 files, 67 active failure modes (3 merged).*

---

*CLI Agent Spec v1.6 — 2026-04-01. Full failure mode reference: [challenges/index.md](index.md). Requirements: [requirements/index.md](../requirements/index.md)*
