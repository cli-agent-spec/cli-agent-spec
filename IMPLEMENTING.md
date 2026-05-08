# Implementation Guide for AI Agents

This file is for AI agents helping someone **implement the CLI Agent Spec specification** in their own project. It covers how to read the spec, generate language-specific types, and validate your output.

If you are helping to **maintain or extend the specification itself**, read [`AGENTS.md`](AGENTS.md) instead.

---

## What this spec is

The **CLI Agent Spec** specification defines the contracts a CLI tool must satisfy to be reliably orchestrated by an AI agent. It covers exit codes, structured output, error envelopes, command discovery, and more. Implementing it means building a CLI framework (or extending an existing one) that enforces these contracts automatically.

---

## Where to start

| You want to… | Start here |
|--------------|------------|
| Understand what problems the spec solves | [`challenges/index.md`](challenges/index.md) |
| See all requirements at a glance | [`requirements/index.md`](requirements/index.md) |
| Implement a specific requirement | The requirement file `requirements/<id>.md` |
| Get the type definitions for your language | [`schemas/codegen-guide.md`](schemas/codegen-guide.md) |
| Validate your JSON output against a schema | [`schemas/index.md`](schemas/index.md) |

---

## Requirement tiers

Requirements are grouped into three tiers. Implement them in this order:

| Tier | Prefix | Meaning | When to implement |
|------|--------|---------|-------------------|
| Framework-Automatic | `REQ-F` | Enforced by the framework without command author action | First — these are the foundation |
| Command Contract | `REQ-C` | Declared by the command author at registration | Second — per-command declarations |
| Opt-In | `REQ-O` | Explicitly enabled by the application | Last — advanced or optional features |

Don't implement tier by tier. Follow the wave plan in the [Suggested implementation order](#suggested-implementation-order) section below — it respects dependencies across tiers.

---

## Reading a requirement file

Each requirement file (`requirements/<id>.md`) contains:

1. **Description** — what the requirement is and why it exists
2. **Acceptance Criteria** — testable conditions; use these to verify your implementation
3. **Schema** — links to the JSON Schema file(s) the requirement uses
4. **Wire Format** — exact JSON the implementation must emit
5. **Example** — language-agnostic pseudocode showing the pattern
6. **Related** — other requirements that compose or depend on this one

Read the **Schema** link to get the machine-readable type definition. Read **Wire Format** to know exactly what your output must look like. Use **Acceptance Criteria** as your test checklist.

---

## Generating types from schemas

The `schemas/` directory contains JSON Schema draft-07 files. Generate language-specific types once, then use them throughout your implementation.

**Full guide:** [`schemas/codegen-guide.md`](schemas/codegen-guide.md)

**Quick reference:**

| Language | Tool | Install | Generate |
|----------|------|---------|----------|
| Any | `ajv-cli` | `npm install -g ajv-cli` | `ajv validate -s schemas/... -d output.json` |
| Python | `datamodel-code-generator` | `pip install datamodel-code-generator` | `datamodel-codegen --input schemas/ --output src/models/` |
| TypeScript | `json-schema-to-typescript` | `npm install -g json-schema-to-typescript` | `json2ts --input schemas/ --output src/types/` |
| Rust | `cargo-typify` | `cargo install cargo-typify` | `cargo typify schemas/<name>.json > src/types/<name>.rs` |
| Go | `go-jsonschema` | `go install github.com/atombender/go-jsonschema@latest` | `go-jsonschema --package framework schemas/*.json > types.go` |
| Java | `jsonschema2pojo` | `brew install jsonschema2pojo` | `jsonschema2pojo --source schemas/ --target src/main/java/` |

**Always validate before generating:**

```bash
npm install -g ajv-cli
ajv compile -s "schemas/*.json" --spec=draft7
```

**Post-generation invariant:** Code generators do not enforce the `ExitCodeEntry` constraint that `retryable: true` implies `side_effects: "none"`. After generating, add the validation snippet for your language — see the "Validation after generation" section in [`schemas/codegen-guide.md`](schemas/codegen-guide.md).

---

## Key invariants to enforce

These constraints are not checked by code generators. Enforce them at registration time in your framework:

| Invariant | Where defined | Rule |
|-----------|--------------|------|
| `retryable: true` implies `side_effects: "none"` | `ExitCodeEntry` | Hard schema invariant — reject at registration |
| Exit code map must include key `"0"` (SUCCESS) | REQ-C-001 | Every command must declare a SUCCESS entry |
| `ARG_ERROR (3)` may only be emitted before any side effect | REQ-F-001 | Phase boundary between validation and execution |
| `PARTIAL_FAILURE (2)` is never retryable | REQ-F-001 | Some writes occurred — state is unknown |
| Literal integers not permitted at call sites | REQ-F-001 | Use `ExitCode` enum constants only |

---

## Goal-based paths

If you have a specific agent pain point, start with the path that addresses it. Each path is a focused subset of requirements — roughly 10–15 — that delivers measurable improvement on one axis. Requirements marked **†** appear in more than one path; implement them once.

After completing any path, continue with the full [wave plan](#suggested-implementation-order).

---

### Path A — Fewer retries

**Goal:** agent gets enough signal to know whether to retry, when, and with what modification. Eliminates blind retries, infinite hang, and unsafe re-execution of mutating commands.

| Requirement | Title | Agent benefit |
|-------------|-------|---------------|
| [REQ-F-001](requirements/f-001-standard-exit-code-table.md) | Standard Exit Code Table | 14 typed codes with `retryable` flag — no guessing from exit int |
| [REQ-F-002](requirements/f-002-exit-code-2-reserved-for-validation-failures.md) | Exit Code 2 Reserved for Validation Failures | Validation failures are always side-effect-free → always safe to retry |
| [REQ-F-011](requirements/f-011-default-timeout-per-command.md) | Default Timeout Per Command | Prevents infinite hang; agent always gets a response |
| [REQ-F-012](requirements/f-012-timeout-exit-code-and-json-error.md) | Timeout Exit Code and JSON Error | Timeout emits `retryable: true` + elapsed time for backoff |
| [REQ-F-013](requirements/f-013-sigterm-handler-installation.md) | SIGTERM Handler Installation | Cancellation produces a clean JSON error, not a crash |
| [REQ-F-015](requirements/f-015-validate-before-execute-phase-order.md) | Validate-Before-Execute Phase Order | No side effects during validation → safe to fix args and retry |
| [REQ-F-045](requirements/f-045-agent-hallucination-input-pattern-rejection.md) | Agent Hallucination Input Pattern Rejection | Rejects `<placeholder>` inputs at phase 1 before any side effect |
| [REQ-F-063](requirements/f-063-credential-expiry-structured-error.md) | Credential Expiry Structured Error | Distinguishes expired (retryable after re-auth) from missing (not retryable) |
| [REQ-F-065](requirements/f-065-pipeline-exit-code-propagation.md) | Pipeline Exit Code Propagation | Failure codes are not masked by downstream success |
| [REQ-C-001](requirements/c-001-command-declares-exit-codes.md) **†** | Command Declares Exit Codes | Per-command exit code map with `retryable` and `side_effects` |
| [REQ-C-006](requirements/c-006-all-args-validated-in-phase-1.md) | All Args Validated in Phase 1 | All errors collected in one pass; agent sees complete failure set before retry |
| [REQ-C-007](requirements/c-007-mutating-commands-accept-idempotency-key.md) | Mutating Commands Accept `--idempotency-key` | Second call with same key returns `effect: "noop"` — safe to retry |
| [REQ-C-013](requirements/c-013-error-responses-include-code-and-message.md) **†** | Error Responses Include Code and Message | Structured error code lets agent classify failure type |
| [REQ-C-014](requirements/c-014-error-responses-include-retryable-and-retry-after-.md) | Error Responses Include `retryable` and `retry_after_ms` | Explicit retry flag + backoff timing on every error |
| [REQ-O-009](requirements/o-009-validate-only-flag.md) | `--validate-only` Flag | Agent validates args before executing — zero side effects |

---

### Path B — Less context consumed

**Goal:** reduce the volume of text entering the agent's context window per command invocation. Eliminates ANSI noise, unbounded list dumps, and prose mixed into stdout.

| Requirement | Title | Agent benefit |
|-------------|-------|---------------|
| [REQ-F-003](requirements/f-003-json-output-mode-auto-activation.md) | JSON Output Mode Auto-Activation | Auto-activates in non-TTY; no prose contamination without explicit flags |
| [REQ-F-004](requirements/f-004-consistent-json-response-envelope.md) **†** | Consistent JSON Response Envelope | Predictable shape — agent extracts `data` without full parse |
| [REQ-F-006](requirements/f-006-stdout-stderr-stream-enforcement.md) | Stdout/Stderr Stream Enforcement | Prose and errors go to stderr only; stdout is pure JSON |
| [REQ-F-007](requirements/f-007-ansi-color-code-suppression.md) | ANSI/Color Code Suppression | No escape sequences in JSON string values |
| [REQ-F-008](requirements/f-008-no-color-and-ci-environment-detection.md) | `NO_COLOR` and CI Environment Detection | Colors auto-disabled in non-TTY without extra flags |
| [REQ-F-019](requirements/f-019-default-output-limit.md) | Default Output Limit | List commands default to 20 items; agent fetches next page only when needed |
| [REQ-F-021](requirements/f-021-data-meta-separation-in-response-envelope.md) | Data/Meta Separation in Response Envelope | Agent reads only `data`; volatile `meta` fields don't inflate comparison diffs |
| [REQ-F-048](requirements/f-048-help-output-routing-to-stderr-in-non-tty-mode.md) | Help Output Routing to Stderr in Non-TTY Mode | `--help` goes to stderr; stdout stays valid JSON |
| [REQ-F-052](requirements/f-052-response-size-hard-cap-with-truncation-indicator.md) | Response Size Hard Cap with Truncation Indicator | Hard 1 MB cap; `meta.truncated: true` signals the agent to paginate |
| [REQ-F-056](requirements/f-056-terminal-width-wrapping-disabled-in-json-mode.md) | Terminal Width Wrapping Disabled in JSON Mode | No mid-string line breaks inflating token count |
| [REQ-O-001](requirements/o-001-output-format-flag.md) **†** | `--output` Format Flag | Agent selects `json`, `jsonl`, or `tsv` — pick the most compact format for the task |
| [REQ-O-002](requirements/o-002-fields-selector.md) | `--fields` Selector | Agent requests only needed fields; server-side projection |
| [REQ-O-003](requirements/o-003-limit-and-cursor-pagination-flags.md) **†** | `--limit` and `--cursor` Pagination Flags | Agent fetches exactly as many items as needed |
| [REQ-O-008](requirements/o-008-quiet-verbose-debug-verbosity-flags.md) | `--quiet` / `--verbose` / `--debug` Verbosity Flags | `--quiet` suppresses all diagnostic output |

---

### Path C — Less token spend

**Goal:** agent discovers and uses commands efficiently without exploratory calls. Eliminates O(N) `--help` loops, redundant `--version` checks, and trial-and-error argument discovery.

| Requirement | Title | Agent benefit |
|-------------|-------|---------------|
| [REQ-F-004](requirements/f-004-consistent-json-response-envelope.md) **†** | Consistent JSON Response Envelope | Same shape every call → agent needs one parsing template, not per-command logic |
| [REQ-F-022](requirements/f-022-schema-version-in-every-response.md) | Schema Version in Every Response | Agent detects schema changes without a separate `--schema` call |
| [REQ-F-023](requirements/f-023-tool-version-in-every-response.md) | Tool Version in Every Response | Version check is free — no extra `--version` invocation |
| [REQ-F-028](requirements/f-028-config-source-tracking-in-response-meta.md) | Config Source Tracking in Response Meta | Agent sees which config file won — no debug loop needed |
| [REQ-C-001](requirements/c-001-command-declares-exit-codes.md) **†** | Command Declares Exit Codes | Exit codes appear in `--schema`; agent learns failure modes without trial calls |
| [REQ-C-013](requirements/c-013-error-responses-include-code-and-message.md) **†** | Error Responses Include Code and Message | Structured codes enable agent templates reused across commands |
| [REQ-C-015](requirements/c-015-commands-declare-input-and-output-schema.md) | Commands Declare Input and Output Schema | Full parameter + output schema at `--schema`; no exploration required |
| [REQ-O-001](requirements/o-001-output-format-flag.md) **†** | `--output` Format Flag | `--output id` pipes bare IDs — no JSON parse step in composition chains |
| [REQ-O-003](requirements/o-003-limit-and-cursor-pagination-flags.md) **†** | `--limit` and `--cursor` Pagination Flags | Standard cursor model; agent reuses same pagination logic for all list commands |
| [REQ-O-013](requirements/o-013-schema-output-schema-flag.md) | `--schema` / `--output-schema` Flag | One call exposes all parameters, exit codes, and output shape; `--print-schema` is a compatibility alias |
| [REQ-O-026](requirements/o-026-tool-doctor-built-in-command.md) | `tool doctor` Built-In Command | One preflight call replaces O(N) individual dependency checks |
| [REQ-O-041](requirements/o-041-tool-manifest-built-in-command.md) | `tool manifest` Built-In Command | Full command tree in one call — replaces O(N) `--help` per subcommand |

---

### Path overlap

Requirements marked **†** above appear in multiple paths. Implement them once — they count toward all paths simultaneously.

| Requirement | Paths | Why it serves all three |
|-------------|-------|------------------------|
| [REQ-F-004](requirements/f-004-consistent-json-response-envelope.md) | A · B · C | Retry logic needs it (A); compact predictable shape (B); one parse template (C) |
| [REQ-C-001](requirements/c-001-command-declares-exit-codes.md) | A · C | Per-command retry/side-effect map (A); schema-exposed metadata (C) |
| [REQ-C-013](requirements/c-013-error-responses-include-code-and-message.md) | A · C | Failure classification for retry decisions (A); reusable error templates (C) |
| [REQ-O-001](requirements/o-001-output-format-flag.md) | B · C | Format selection reduces output volume (B) and enables efficient composition (C) |
| [REQ-O-003](requirements/o-003-limit-and-cursor-pagination-flags.md) | B · C | Limits output per call (B); standard cursor reused across commands (C) |

---

## Suggested implementation order

Don't implement requirements in ID order. The requirements have dependencies: some are foundations that others build on. The five waves below reflect that topology. Within each wave, requirements are ordered so that foundational ones land first.

There are **two pivot points** that unlock the most work downstream:
- **F-003 / F-004** (JSON envelope) — nearly every structured output requirement depends on this shape being stable
- **F-009** (non-interactive detection) — once it exists, ~10 "suppress X in non-TTY mode" requirements collapse to trivial one-liners

Get these two right before anything else.

---

### Wave 1 — Output contract

The JSON envelope and exit code table must be stable before any other requirement is testable.

| Requirement | Title | Why first |
|-------------|-------|-----------|
| [REQ-F-001](requirements/f-001-standard-exit-code-table.md) | Standard Exit Code Table | Defines the `ExitCode` enum all other reqs reference |
| [REQ-F-002](requirements/f-002-exit-code-2-reserved-for-validation-failures.md) | Exit Code 2 Reserved for Validation Failures | Phase boundary — required by F-015 and C-006 |
| [REQ-F-003](requirements/f-003-json-output-mode-auto-activation.md) | JSON Output Mode Auto-Activation | Activates structured output; everything downstream requires it |
| [REQ-F-004](requirements/f-004-consistent-json-response-envelope.md) | Consistent JSON Response Envelope | `ok / result / error` shape — all wire-format tests validate this |
| [REQ-F-005](requirements/f-005-locale-invariant-serialization.md) | Locale-Invariant Serialization | Must be in the serializer before any data flows through |
| [REQ-F-011](requirements/f-011-default-timeout-per-command.md) | Default Timeout Per Command | Core reliability contract; timeout shape lands in `meta` |
| [REQ-F-012](requirements/f-012-timeout-exit-code-and-json-error.md) | Timeout Exit Code and JSON Error | Timeout must emit a valid envelope — needs F-004 first |
| [REQ-F-018](requirements/f-018-pagination-metadata-on-list-commands.md) | Pagination Metadata on List Commands | Pagination shape is part of the output contract |
| [REQ-F-019](requirements/f-019-default-output-limit.md) | Default Output Limit | Pairs with F-018; both must exist before list commands work |
| [REQ-F-021](requirements/f-021-data-meta-separation-in-response-envelope.md) | Data/Meta Separation in Response Envelope | Envelope structure finalisation |
| [REQ-F-022](requirements/f-022-schema-version-in-every-response.md) | Schema Version in Every Response | Goes into `meta` — needs envelope to exist |
| [REQ-F-023](requirements/f-023-tool-version-in-every-response.md) | Tool Version in Every Response | Goes into `meta` — needs envelope to exist |
| [REQ-O-001](requirements/o-001-output-format-flag.md) | `--output` Format Flag | P0 opt-in; exposes the JSON mode the framework just built |

---

### Wave 2 — Environment detection

`REQ-F-009` is a multiplier. Once the framework can detect non-interactive / non-TTY context, the requirements below reduce to `if non_tty: suppress(X)`.

| Requirement | Title | Enabled by |
|-------------|-------|-----------|
| [REQ-F-009](requirements/f-009-non-interactive-mode-auto-detection.md) | Non-Interactive Mode Auto-Detection | **Pivot point** — implement first in this wave |
| [REQ-F-008](requirements/f-008-no-color-and-ci-environment-detection.md) | `NO_COLOR` and CI Environment Detection | Reads env vars; pairs with F-009 |
| [REQ-F-007](requirements/f-007-ansi-color-code-suppression.md) | ANSI/Color Code Suppression | Triggered by F-008 / F-009 result |
| [REQ-F-006](requirements/f-006-stdout-stderr-stream-enforcement.md) | Stdout/Stderr Stream Enforcement | Routing decision made once mode is known |
| [REQ-F-010](requirements/f-010-pager-suppression.md) | Pager Suppression | `if non_tty: suppress pager` |
| [REQ-F-046](requirements/f-046-pager-environment-variable-suppression.md) | Pager Environment Variable Suppression | Unsets `PAGER`/`LESS` — same condition |
| [REQ-F-047](requirements/f-047-repl-mode-prohibition-in-non-tty-context.md) | REPL Mode Prohibition in Non-TTY Context | `if non_tty: error` |
| [REQ-F-048](requirements/f-048-help-output-routing-to-stderr-in-non-tty-mode.md) | Help Output Routing to Stderr in Non-TTY Mode | Routes `--help` to stderr when non-TTY |
| [REQ-F-053](requirements/f-053-stdout-unbuffering-in-non-tty-mode.md) | Stdout Unbuffering in Non-TTY Mode | `if non_tty: disable line-buffering` |
| [REQ-F-055](requirements/f-055-editor-and-visual-no-op-in-non-tty-mode.md) | `$EDITOR` and `$VISUAL` No-Op in Non-TTY Mode | Prevents editor trap |
| [REQ-F-056](requirements/f-056-terminal-width-wrapping-disabled-in-json-mode.md) | Terminal Width Wrapping Disabled in JSON Mode | `if json_mode: set width=∞` |
| [REQ-F-057](requirements/f-057-headless-environment-detection-and-gui-suppression.md) | Headless Environment Detection and GUI Suppression | Detects missing `DISPLAY`/`WAYLAND_DISPLAY` |
| [REQ-F-038](requirements/f-038-verbosity-auto-quiet-in-non-tty-context.md) | Verbosity Auto-Quiet in Non-TTY Context | P2; trivial once mode is known |

---

### Wave 3 — Safety and signal layer

These are independent of the envelope and detection work but are all P0 or P1 security/reliability requirements that must land before the framework is usable in agent contexts.

| Requirement | Title | Notes |
|-------------|-------|-------|
| [REQ-F-013](requirements/f-013-sigterm-handler-installation.md) | SIGTERM Handler Installation | Install at framework boot |
| [REQ-F-014](requirements/f-014-sigpipe-handler-installation.md) | SIGPIPE Handler Installation | Install at framework boot |
| [REQ-F-015](requirements/f-015-validate-before-execute-phase-order.md) | Validate-Before-Execute Phase Order | Phase boundary for exit code 2 |
| [REQ-F-044](requirements/f-044-shell-argument-escaping-enforcement.md) | Shell Argument Escaping Enforcement | P0 security; no subprocess call without this |
| [REQ-F-045](requirements/f-045-agent-hallucination-input-pattern-rejection.md) | Agent Hallucination Input Pattern Rejection | Reject `<placeholder>`-style inputs |
| [REQ-F-034](requirements/f-034-secret-field-auto-redaction-in-logs.md) | Secret Field Auto-Redaction in Logs | Redact before any log write |
| [REQ-F-051](requirements/f-051-debug-and-trace-mode-secret-redaction.md) | Debug and Trace Mode Secret Redaction | Same pipeline; must cover debug path too |
| [REQ-F-052](requirements/f-052-response-size-hard-cap-with-truncation-indicator.md) | Response Size Hard Cap with Truncation Indicator | Prevents context overflow |
| [REQ-F-054](requirements/f-054-stdin-payload-size-cap-with-input-file-fallback.md) | Stdin Payload Size Cap with `--input-file` Fallback | Prevents pipe deadlock |
| [REQ-F-062](requirements/f-062-glob-expansion-and-word-splitting-prevention.md) | Glob Expansion and Word-Splitting Prevention | Use `execv`-style APIs, never shell strings |
| [REQ-F-065](requirements/f-065-pipeline-exit-code-propagation.md) | Pipeline Exit Code Propagation | `set -o pipefail` equivalent |

---

### Wave 4 — Command Contract P0s and P1s

The F layer must be stable before asking command authors to declare metadata. These requirements define the per-command registration contract.

**P0 first:**

| Requirement | Title |
|-------------|-------|
| [REQ-C-001](requirements/c-001-command-declares-exit-codes.md) | Command Declares Exit Codes |
| [REQ-C-002](requirements/c-002-command-declares-danger-level.md) | Command Declares Danger Level |
| [REQ-C-003](requirements/c-003-mutating-commands-declare-effect-field.md) | Mutating Commands Declare `effect` Field |
| [REQ-C-004](requirements/c-004-destructive-commands-must-support-dry-run.md) | Destructive Commands Must Support `--dry-run` |
| [REQ-C-005](requirements/c-005-interactive-commands-must-support-yes-non-interact.md) | Interactive Commands Must Support `--yes` / `--non-interactive` |
| [REQ-C-006](requirements/c-006-all-args-validated-in-phase-1.md) | All Args Validated in Phase 1 |
| [REQ-C-012](requirements/c-012-commands-with-network-i-o-support-timeout.md) | Commands with Network I/O Support `--timeout` |
| [REQ-C-013](requirements/c-013-error-responses-include-code-and-message.md) | Error Responses Include Code and Message |
| [REQ-C-021](requirements/c-021-auth-commands-declare-headless-mode-support.md) | Auth Commands Declare Headless Mode Support |
| [REQ-C-022](requirements/c-022-async-commands-declare-job-descriptor-schema.md) | Async Commands Declare Job Descriptor Schema |
| [REQ-C-025](requirements/c-025-config-writing-commands-declare-write-scope.md) | Config-Writing Commands Declare Write Scope |

**Then P1 Command Contract requirements:**

| Requirement | Title |
|-------------|-------|
| [REQ-C-007](requirements/c-007-mutating-commands-accept-idempotency-key.md) | Mutating Commands Accept `--idempotency-key` |
| [REQ-C-008](requirements/c-008-multi-step-commands-emit-step-manifest.md) | Multi-Step Commands Emit Step Manifest |
| [REQ-C-009](requirements/c-009-multi-step-commands-report-completed-failed-skippe.md) | Multi-Step Commands Report `completed`/`failed`/`skipped` |
| [REQ-C-014](requirements/c-014-error-responses-include-retryable-and-retry-after-.md) | Error Responses Include `retryable` and `retry_after_ms` |
| [REQ-C-015](requirements/c-015-commands-declare-input-and-output-schema.md) | Commands Declare Input and Output Schema |
| [REQ-C-016](requirements/c-016-secrets-accepted-only-via-env-var-or-file.md) | Secrets Accepted Only via Env Var or File |
| [REQ-C-017](requirements/c-017-commands-register-cleanup-hook.md) | Commands Register `cleanup()` Hook |
| [REQ-C-019](requirements/c-019-subprocess-invoking-commands-declare-argument-sche.md) | Subprocess-Invoking Commands Declare Argument Schema |
| [REQ-C-020](requirements/c-020-resource-id-fields-declare-validation-pattern.md) | Resource ID Fields Declare Validation Pattern |
| [REQ-C-023](requirements/c-023-editor-requiring-commands-declare-non-interactive-.md) | Editor-Requiring Commands Declare Non-Interactive Alternative |
| [REQ-C-024](requirements/c-024-gui-launching-commands-declare-headless-behavior.md) | GUI-Launching Commands Declare Headless Behavior |
| [REQ-C-026](requirements/c-026-commands-declare-conditional-argument-dependencies.md) | Commands Declare Conditional Argument Dependencies |

---

### Wave 5 — Opt-In features

Implement as needed. P0 opt-ins first, then P1, P2, P3.

**P0 opt-ins (3 remaining — O-001 was implemented in Wave 1):**

| Requirement | Title |
|-------------|-------|
| [REQ-O-003](requirements/o-003-limit-and-cursor-pagination-flags.md) | `--limit` and `--cursor` Pagination Flags |
| [REQ-O-021](requirements/o-021-confirm-destructive-flag.md) | `--confirm-destructive` Flag |
| [REQ-O-033](requirements/o-033-headless-and-token-env-var-flags-for-auth-commands.md) | `--headless` and `--token-env-var` Flags for Auth Commands |

(REQ-O-001 was already implemented in Wave 1.)

**P1 opt-ins** (16 total) — implement in the order that matches what your CLI's users need most: verbosity flags (O-008), validation flag (O-009), schema discovery (O-013, O-015, O-016), update suppression (O-020), secret flags (O-022), manifest command (O-041).

**P2/P3 opt-ins** — defer until the core is solid.

---

### Priority summary

| Wave | Requirements | Focus |
|------|-------------|-------|
| 1 | F-001/002/003/004/005/011/012/018/019/021/022/023 + O-001 | Output contract |
| 2 | F-009 + 10 detection-gated reqs | Environment detection |
| 3 | F-013/014/015/034/044/045/051/052/054/062/065 | Safety and signals |
| 4 | C P0s (11 reqs) → C P1s | Command registration |
| 5 | O P0s → O P1s → O P2/P3 | Opt-in features |
