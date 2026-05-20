# docuseal-cli - Issues Report

**Generated:** 2026-05-20
**CLI version:** 1.0.3
**Scope:** all
**Findings in scope:** 71 failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### §2, §18 - Common failures produce stack traces instead of structured JSON

**Discovered during:** §2 evaluation - 2026-05-20
**Symptom:** Observed templates list without credentials, invalid JSON in -d, a missing upload file, and network failure. These exit 1 with Commander prose or Node stack traces rather than a structured error envelope.
**Impact:** Parse failure and brittle error handling for agents.
**Trigger:** `node bin/run.js templates list --output json`

---

### §10 - configure prompt path exits 0 under non-TTY stdin

**Discovered during:** §10 evaluation - 2026-05-20
**Symptom:** Running node bin/run.js configure with empty stdin printed the server prompt and exited 0 without writing configuration.
**Impact:** False success signal for setup automation.
**Trigger:** `node bin/run.js configure` with empty stdin

---

### §40 - Async handlers are registered under program.parse()

**Discovered during:** §40 evaluation - 2026-05-20
**Symptom:** src/index.js calls program.parse() while command actions are async; observed network/auth failures surfaced as unhandled stack traces.
**Impact:** Unhandled async errors break structured recovery.
**Trigger:** Source inspection of `src/index.js`.

---

### §72 - Integration artifact version drift

**Discovered during:** §72 evaluation - 2026-05-20
**Symptom:** package.json and node bin/run.js --version report 1.0.3, while skills/docuseal-cli/SKILL.md metadata reports 1.0.6.
**Impact:** Agent integration docs can describe a different CLI than the installed binary.
**Trigger:** Compare `node bin/run.js --version` with `skills/docuseal-cli/SKILL.md`.

---

---

## Failure-Mode Gaps  _(score 0-2, sorted: score asc, severity desc)_

These are not confirmed bugs but verified gaps - the CLI does not meet the bar for reliable agent use.

### §1 - Exit Codes & Status Signaling  [Critical · score 0/3]

**What fails:** Failures observed with generic exit 1; no documented semantic exit-code table or JSON error body.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §11 - Timeouts & Hanging Processes  [Critical · score 0/3]

**What fails:** Network failure produced an uncaught Node stack trace; no timeout flag or `TIMEOUT` JSON.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §12 - Idempotency & Safe Retries  [Critical · score 0/3]

**What fails:** Mutating commands have no idempotency key or effect/noop field.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §13 - Partial Failure & Atomicity  [Critical · score 0/3]

**What fails:** No partial-failure/resume protocol.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §23 - Side Effects & Destructive Operations  [Critical · score 0/3]

**What fails:** Destructive archive operations have no `--dry-run` or machine-readable danger declaration.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §24 - Authentication & Secret Handling  [Critical · score 0/3]

**What fails:** Secrets can be supplied via hidden `--api-key` CLI flag; no standard redaction framework.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §25 - Prompt Injection via Output  [Critical · score 0/3]

**What fails:** External API data is returned raw without a trusted/untrusted envelope.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §43 - Tool Output Result Size Unboundedness  [Critical · score 0/3]

**What fails:** No output limit, truncation metadata, or schema max-output declaration.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Critical · Time: High
**Workaround exists:** Partial

---

### §53 - Credential Expiry Mid-Session  [Critical · score 0/3]

**What fails:** No distinct credential-expiry code, reauth command, or expiry metadata.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §60 - OS Output Buffer Deadlock  [Critical · score 0/3]

**What fails:** No streaming protocol or heartbeat for long-running commands.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §74 - Credential Scope Declaration Absence  [Critical · score 0/3]

**What fails:** No machine-readable required scopes or permission check command.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial

---

### §15 - Race Conditions & Concurrency  [High · score 0/3]

**What fails:** No lock protocol for mutating/config operations.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §16 - Signal Handling & Graceful Cancellation  [High · score 0/3]

**What fails:** No SIGTERM partial-result protocol.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §18 - Error Message Quality  [High · score 0/3]

**What fails:** Validation/auth/file/network errors are prose or stack traces without `code`, `suggestion`, or context.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §19 - Retry Hints in Error Responses  [High · score 0/3]

**What fails:** No `retryable` or `retry_after_ms` fields.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §22 - Schema Versioning & Output Stability  [High · score 0/3]

**What fails:** No `meta.schema_version` in responses.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §26 - Stateful Commands & Session Management  [High · score 0/3]

**What fails:** Implicit global config/env state; no `status --output json` context report.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §31 - Network Proxy Unawareness  [High · score 0/3]

**What fails:** Network errors include no proxy context.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §35 - Agent Hallucination Input Patterns  [High · score 0/3]

**What fails:** Percent-encoded/path-like values are not rejected with structured validation suggestions.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §38 - Runtime Dependency Version Mismatch  [High · score 0/3]

**What fails:** No `engines` declaration or startup runtime-version JSON check.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §40 - parse() vs parseAsync() Silent Race Condition  [High · score 0/3]

**What fails:** Source uses `program.parse()` with async action handlers.
**Frequency:** Common (Node.js ecosystem)
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §47 - MCP Wrapper Schema Staleness  [High · score 0/3]

**What fails:** No MCP wrapper health, schema version, or stale-schema mapping.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §49 - Async Job / Polling Protocol Absence  [High · score 0/3]

**What fails:** No async job/status protocol or distinct running/done exit codes.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §54 - Conditional / Dependent Argument Requirements  [High · score 0/3]

**What fails:** No machine-readable arg groups or all-at-once dependent-argument validation.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §55 - Silent Data Truncation  [High · score 0/3]

**What fails:** No schema max lengths or `FIELD_TRUNCATED`/validation warning protocol.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §56 - Exit Code Masking in Shell Pipelines  [High · score 0/3]

**What fails:** No `ok`, `meta.ok`, or `meta.exit_code` fields.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §58 - Multi-Agent Concurrent Invocation Conflict  [High · score 0/3]

**What fails:** Config writes use direct writes to shared config; no locking or conflict code.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §65 - Global Configuration State Contamination  [High · score 0/3]

**What fails:** Config writes default to global user config without `--global` or write-scope metadata.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §67 - Agent-Generated Input Syntax Rejection  [High · score 0/3]

**What fails:** Strict JSON parse errors produce raw stack traces; no `INVALID_JSON` corrected input.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §68 - Third-Party Library Stdout Pollution  [High · score 0/3]

**What fails:** No stdout interception or warnings envelope.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §70 - Single-Argument Arity Forcing Agent Loop Overhead  [High · score 0/3]

**What fails:** Single-ID commands do not accept variadic IDs with per-item results.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §72 - Integration Artifact Version Drift  [High · score 0/3]

**What fails:** Skill metadata version `1.0.6` differs from binary/package version `1.0.3`, confirming integration artifact drift.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §6 - Command Composition & Piping  [Medium · score 0/3]

**What fails:** No `--output id` mode and no stdin `-` ID protocol.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §7 - Output Non-Determinism  [Medium · score 0/3]

**What fails:** Raw API output has no stable-output mode or volatile-field isolation.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §20 - Environment & Dependency Discovery  [Medium · score 0/3]

**What fails:** No `doctor --output json` or structured dependency preflight.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §21 - Schema & Help Discoverability  [Medium · score 0/3]

**What fails:** No `--schema --output json`; help is prose only.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §29 - Working Directory Sensitivity  [Medium · score 0/3]

**What fails:** File paths are resolved relative to CWD with no `meta.cwd` or framework `--cwd`.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §30 - Undeclared Filesystem Side Effects  [Medium · score 0/3]

**What fails:** Config filesystem side effects are not declared or inventoried.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Low
**Workaround exists:** Partial

---

### §33 - Observability & Audit Trail  [Medium · score 0/3]

**What fails:** No `request_id`, `duration_ms`, trace propagation, or audit log.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §52 - Recursive Command Tree Discovery Cost  [Medium · score 0/3]

**What fails:** No `--schema` command tree; agents must recurse through help text.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §57 - Locale-Dependent Error Messages  [Medium · score 0/3]

**What fails:** OS/file errors surface as raw stack traces, not normalized structured errors.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: Low
**Workaround exists:** Partial

---

### §63 - Terminal Column Width Output Corruption  [Medium · score 0/3]

**What fails:** No JSON mode; help prose wraps at terminal width.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §2 - Output Format & Parseability  [Critical · score 1/3]

**What fails:** API commands emit JSON on success, but there is no `--output json` and no `ok`/`data`/`error` envelope; many errors are prose/stack traces.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §10 - Interactivity & TTY Requirements  [Critical · score 1/3]

**What fails:** `configure` has flags for non-interactive setup, but the prompt path still runs in non-TTY and can exit 0 without configuring.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §34 - Shell Injection via Agent-Constructed Commands  [Critical · score 1/3]

**What fails:** No shell execution path found, but suspicious name/path values are not validated into structured errors.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §45 - Headless Authentication / OAuth Browser Flow Blocking  [Critical · score 1/3]

**What fails:** Missing auth exits immediately, but as an uncaught stack trace rather than `AUTH_REQUIRED` with `auth_methods`.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §3 - Stderr vs Stdout Discipline  [High · score 1/3]

**What fails:** Data is normally stdout, but help/prose success/error output can also appear on stdout.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Low
**Workaround exists:** Partial

---

### §5 - Pagination & Large Output  [High · score 1/3]

**What fails:** List commands expose limit/cursor flags, but no standard pagination metadata envelope.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §14 - Argument Validation Before Side Effects  [High · score 1/3]

**What fails:** Commander validates some arguments before execution, but exit code is generic and errors are not structured JSON.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §28 - Config File Shadowing & Precedence  [High · score 1/3]

**What fails:** README documents precedence and `configure --list` shows config, but sources are not machine-readable.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §46 - API Schema to CLI Flag Translation Loss  [High · score 1/3]

**What fails:** `-d` accepts JSON/bracket notation, but there is no full `--json` body flag or API-schema validation.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §51 - Shell Word Splitting and Glob Expansion Interference  [High · score 1/3]

**What fails:** Exec-array invocation preserves spaced file paths, but missing files become unstructured `ENOENT` stack traces.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §59 - High-Entropy String Token Poisoning  [High · score 1/3]

**What fails:** `configure --list` masks stored `api_key`, but there is no semantic token summary/unmask protocol.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Low
**Workaround exists:** Partial

---

### §69 - Argument Order Ambiguity  [High · score 1/3]

**What fails:** Subcommand-level global flags work after the subcommand; root-level placement is rejected.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §73 - Documentation Accuracy Drift  [High · score 1/3]

**What fails:** No AGENTS.md; available CLAUDE/skill docs are useful but version drift exists.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §4 - Verbosity & Token Cost  [Medium · score 1/3]

**What fails:** No progress spam observed, but there is no quiet/fields control and CI does not activate structured mode.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Low
**Workaround exists:** Partial

---

### §27 - Platform & Shell Portability  [Medium · score 1/3]

**What fails:** Node CLI is portable in principle, but there is no doctor command and failures are raw.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §44 - Agent Knowledge Packaging Absence  [Medium · score 1/3]

**What fails:** Repository ships CLAUDE.md and a skill, but no AGENTS.md/CONTEXT.md and no `--schema` danger/requires fields.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §42 - Debug / Trace Mode Secret Leakage  [Critical · score 2/3]

**What fails:** No debug/trace mode found to leak secrets, but no sensitive schema/redaction declaration exists.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Low · Time: Low
**Workaround exists:** Partial

---

### §71 - Non-Interactive Installation Absence  [Critical · score 2/3]

**What fails:** README documents non-interactive npm install/use; no AGENTS.md install protocol and global install idempotency was not exercised.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Critical
**Workaround exists:** Partial

---

### §9 - Binary & Encoding Safety  [High · score 2/3]

**What fails:** File uploads use Buffer/base64 for binary content; error handling remains unstructured.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial

---

### §41 - Update Notifier Side-Channel Output Pollution  [High · score 2/3]

**What fails:** No update notifier found; CI/NO_UPDATE_NOTIFIER produced no side-channel notice.
**Frequency:** Common (Node.js/npm ecosystem)
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

## Passing  _(score 3/3 - safe to use without special handling)_

§37 REPL / Interactive Mode Accidental Triggering, §50 Stdin Consumption Deadlock, §61 Bidirectional Pipe Payload Deadlock, §62 $EDITOR and $VISUAL Trap, §64 Headless Display and GUI Launch Blocking, §66 Symlink Loop and Recursive Traversal Exhaustion, §17 Child Process Leakage, §8 ANSI & Color Code Leakage, §32 Self-Update & Auto-Upgrade Behavior

---

## Risk Summary

| Category | Count | §N list |
|---|---:|---|
| Observed bugs | 4 | §2, §10, §18, §40, §72 |
| Score 0 - complete failure | 42 | §43, §53, §60, §35, §38, §40, §47, §49, §54, §55, §56, §58, §65, §67, §68, §70, §72, §52, §57, §63, §11, §12, §13, §15, §16, §23, §24, §25, §74, §1, §6, §7, §26, §31, §29, §30, §18, §19, §22, §20, §21, §33 |
| Score 1 - major gap | 16 | §34, §45, §46, §51, §59, §69, §73, §44, §10, §14, §2, §3, §5, §4, §28, §27 |
| Score 2 - minor gap | 4 | §42, §71, §41, §9 |
| Score 3 - passing | 9 | §37, §50, §61, §62, §64, §66, §17, §8, §32 |
| Indeterminate (?/3 - timed out) | 0 | None |

**Highest-risk combination:** §1 and §2 combine generic exit codes with no stable output envelope, so agents cannot reliably distinguish success, validation failure, auth failure, network failure, or crashes.
