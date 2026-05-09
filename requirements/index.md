# Requirements Index

> All requirements for an agent-compatible CLI framework, derived from the CLI Agent Spec's 73 documented failure modes.

**155 total** &nbsp;|&nbsp; 78 Framework-Automatic · 29 Command Contract · 48 Opt-In — amended 2026-05-09

**By priority:** P0: 51 · P1: 62 · P2: 33 · P3: 9 — REQ-O-048 added: destructive commands default to dry-run mode (§75)

---

## Framework-Automatic (F)

**78 requirements** &nbsp;|&nbsp; P0: 33 · P1: 29 · P2: 15 · P3: 1

| ID | Priority | Title | Failure mode(s) |
|----|----------|-------|-------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | P0 | Standard Exit Code Table | [§1](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | P0 | Exit Code 2 Reserved for Validation Failures | [§1](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) [§14](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md) |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | P0 | JSON Output Mode Auto-Activation | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | P0 | Consistent JSON Response Envelope | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-F-005](f-005-locale-invariant-serialization.md) | P0 | Locale-Invariant Serialization | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | P0 | Stdout/Stderr Stream Enforcement | [§3](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md) |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | P0 | ANSI/Color Code Suppression | [§8](../challenges/04-critical-output-and-parsing/08-high-ansi-leakage.md) |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | P0 | NO_COLOR and CI Environment Detection | [§8](../challenges/04-critical-output-and-parsing/08-high-ansi-leakage.md) |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | P0 | Non-Interactive Mode Auto-Detection | [§10](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) |
| [REQ-F-010](f-010-pager-suppression.md) | P0 | Pager Suppression | [§10](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) |
| [REQ-F-011](f-011-default-timeout-per-command.md) | P0 | Default Timeout Per Command | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | P0 | Timeout Exit Code and JSON Error | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | P0 | SIGTERM Handler Installation | [§16](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md) |
| [REQ-F-014](f-014-sigpipe-handler-installation.md) | P0 | SIGPIPE Handler Installation | [§16](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md) |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | P0 | Validate-Before-Execute Phase Order | [§14](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md) |
| [REQ-F-016](f-016-utf-8-sanitization-before-serialization.md) | P1 | UTF-8 Sanitization Before Serialization | [§9](../challenges/04-critical-output-and-parsing/09-high-binary-encoding.md) |
| [REQ-F-017](f-017-binary-field-base64-encoding.md) | P1 | Binary Field Base64 Encoding | [§9](../challenges/04-critical-output-and-parsing/09-high-binary-encoding.md) |
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | P0 | Pagination Metadata on List Commands | [§5](../challenges/04-critical-output-and-parsing/05-high-pagination.md) |
| [REQ-F-019](f-019-default-output-limit.md) | P0 | Default Output Limit | [§5](../challenges/04-critical-output-and-parsing/05-high-pagination.md) |
| [REQ-F-020](f-020-stable-array-sorting-in-json-output.md) | P2 | Stable Array Sorting in JSON Output | [§7](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md) |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | P1 | Data/Meta Separation in Response Envelope | [§7](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md) |
| [REQ-F-022](f-022-schema-version-in-every-response.md) | P1 | Schema Version in Every Response | [§22](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) |
| [REQ-F-023](f-023-tool-version-in-every-response.md) | P1 | Tool Version in Every Response | [§22](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) [§32](../challenges/05-high-environment-and-state/32-high-self-update.md) |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | P2 | Request ID and Trace ID in Every Response | [§33](../challenges/07-medium-observability/33-medium-observability.md) |
| [REQ-F-025](f-025-tool-trace-id-environment-variable-propagation.md) | P2 | TOOL_TRACE_ID Environment Variable Propagation | [§33](../challenges/07-medium-observability/33-medium-observability.md) |
| [REQ-F-026](f-026-append-only-audit-log.md) | P2 | Append-Only Audit Log | [§33](../challenges/07-medium-observability/33-medium-observability.md) |
| [REQ-F-027](f-027-cwd-in-response-meta.md) | P2 | CWD in Response Meta | [§29](../challenges/05-high-environment-and-state/29-medium-working-directory.md) |
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | P1 | Config Source Tracking in Response Meta | [§28](../challenges/05-high-environment-and-state/28-high-config-shadowing.md) |
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | P1 | Auto-Update Suppression in Non-Interactive Mode | [§32](../challenges/05-high-environment-and-state/32-high-self-update.md) |
| [REQ-F-030](f-030-child-process-session-tracking.md) | P2 | Child Process Session Tracking | [§17](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md) |
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | P2 | SIGTERM Forwarding to Tracked Children | [§17](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md) |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | P2 | Session-Scoped Temp Directory | [§15](../challenges/02-critical-execution-and-reliability/15-high-race-conditions.md) |
| [REQ-F-033](f-033-lock-acquisition-with-timeout-and-retry-after-ms.md) | P2 | Lock Acquisition with Timeout and retry_after_ms | [§15](../challenges/02-critical-execution-and-reliability/15-high-race-conditions.md) |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | P1 | Secret Field Auto-Redaction in Logs | [§24](../challenges/03-critical-security/24-critical-auth-secrets.md) |
| [REQ-F-035](f-035-external-data-trust-tagging.md) | P1 | External Data Trust Tagging | [§25](../challenges/03-critical-security/25-critical-prompt-injection.md) |
| [REQ-F-036](f-036-http-client-proxy-environment-variable-compliance.md) | P1 | HTTP Client Proxy Environment Variable Compliance | [§31](../challenges/05-high-environment-and-state/31-high-network-proxy.md) |
| [REQ-F-037](f-037-network-error-context-block.md) | P1 | Network Error Context Block | [§31](../challenges/05-high-environment-and-state/31-high-network-proxy.md) |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | P2 | Verbosity Auto-Quiet in Non-TTY Context | [§4](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | P1 | Duration Tracking in Response Meta | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) [§33](../challenges/07-medium-observability/33-medium-observability.md) |
| [REQ-F-040](f-040-absolute-path-output-enforcement.md) | P2 | Absolute Path Output Enforcement | [§29](../challenges/05-high-environment-and-state/29-medium-working-directory.md) |
| [REQ-F-041](f-041-process-cwd-immutability.md) | P2 | Process CWD Immutability | [§29](../challenges/05-high-environment-and-state/29-medium-working-directory.md) |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | P3 | Log Rotation in Framework Logger | [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | P2 | Temp File Session-Scoped Auto-Cleanup | [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-F-044](f-044-shell-argument-escaping-enforcement.md) | P0 | Shell Argument Escaping Enforcement | [§34](../challenges/01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md) |
| [REQ-F-045](f-045-agent-hallucination-input-pattern-rejection.md) | P0 | Agent Hallucination Input Pattern Rejection | [§35](../challenges/01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md) |
| [REQ-F-046](f-046-pager-environment-variable-suppression.md) | P0 | Pager Environment Variable Suppression | [§10](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) |
| [REQ-F-047](f-047-repl-mode-prohibition-in-non-tty-context.md) | P0 | REPL Mode Prohibition in Non-TTY Context | [§37](../challenges/01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md) |
| [REQ-F-048](f-048-help-output-routing-to-stderr-in-non-tty-mode.md) | P0 | Help Output Routing to Stderr in Non-TTY Mode | [§3](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md) |
| [REQ-F-049](f-049-async-command-handler-enforcement.md) | P1 | Async Command Handler Enforcement | [§40](../challenges/01-critical-ecosystem-runtime-agent-specific/40-high-async-race-condition.md) |
| [REQ-F-050](f-050-update-notifier-side-channel-suppression.md) | P1 | Update Notifier Side-Channel Suppression | [§41](../challenges/01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md) |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | P0 | Debug and Trace Mode Secret Redaction | [§42](../challenges/01-critical-ecosystem-runtime-agent-specific/42-critical-debug-secret-leakage.md) |
| [REQ-F-052](f-052-response-size-hard-cap-with-truncation-indicator.md) | P0 | Response Size Hard Cap with Truncation Indicator | [§43](../challenges/01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md) |
| [REQ-F-053](f-053-stdout-unbuffering-in-non-tty-mode.md) | P0 | Stdout Unbuffering in Non-TTY Mode | [§60](../challenges/01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) |
| [REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md) | P0 | Stdin Payload Size Cap with --input-file Fallback | [§61](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) |
| [REQ-F-055](f-055-editor-and-visual-no-op-in-non-tty-mode.md) | P0 | $EDITOR and $VISUAL No-Op in Non-TTY Mode | [§62](../challenges/01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md) |
| [REQ-F-056](f-056-terminal-width-wrapping-disabled-in-json-mode.md) | P0 | Terminal Width Wrapping Disabled in JSON Mode | [§63](../challenges/01-critical-ecosystem-runtime-agent-specific/63-medium-column-width-corruption.md) |
| [REQ-F-057](f-057-headless-environment-detection-and-gui-suppression.md) | P0 | Headless Environment Detection and GUI Suppression | [§64](../challenges/01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md) |
| [REQ-F-058](f-058-high-entropy-field-masking.md) | P1 | High-Entropy Field Masking | [§59](../challenges/01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md) |
| [REQ-F-059](f-059-json5-input-normalization.md) | P1 | JSON5 Input Normalization | [§67](../challenges/01-critical-ecosystem-runtime-agent-specific/67-high-json5-input.md) |
| [REQ-F-060](f-060-third-party-stdout-interception.md) | P1 | Third-Party Stdout Interception | [§68](../challenges/01-critical-ecosystem-runtime-agent-specific/68-high-stdout-pollution.md) |
| [REQ-F-061](f-061-symlink-loop-detection-in-traversal-utilities.md) | P1 | Symlink Loop Detection in Traversal Utilities | [§66](../challenges/01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md) |
| [REQ-F-062](f-062-glob-expansion-and-word-splitting-prevention.md) | P0 | Glob Expansion and Word-Splitting Prevention | [§51](../challenges/01-critical-ecosystem-runtime-agent-specific/51-high-glob-expansion.md) |
| [REQ-F-063](f-063-credential-expiry-structured-error.md) | P1 | Credential Expiry Structured Error | [§53](../challenges/01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md) |
| [REQ-F-064](f-064-output-truncation-detection-and-warning.md) | P1 | Output Truncation Detection and Warning | [§55](../challenges/01-critical-ecosystem-runtime-agent-specific/55-high-silent-truncation.md) |
| [REQ-F-065](f-065-pipeline-exit-code-propagation.md) | P0 | Pipeline Exit Code Propagation | [§56](../challenges/01-critical-ecosystem-runtime-agent-specific/56-high-pipeline-exit-masking.md) |
| [REQ-F-066](f-066-subprocess-locale-normalization.md) | P1 | Subprocess Locale Normalization | [§57](../challenges/01-critical-ecosystem-runtime-agent-specific/57-medium-locale-errors.md) |
| [REQ-F-067](f-067-interspersed-option-parsing.md) | P1 | Interspersed Option Parsing | [§69](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) |
| [REQ-F-068](f-068-help-and-version-flag-purity.md) | P0 | Help and Version Flag Purity | — |
| [REQ-F-069](f-069-sigint-handler-installation.md) | P0 | SIGINT Handler Installation | [§16](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md) |
| [REQ-F-070](f-070-atomic-write-via-rename.md) | P1 | Atomic Write via Rename | [§15](../challenges/02-critical-execution-and-reliability/15-high-race-conditions.md) |
| [REQ-F-071](f-071-file-descriptor-leak-prevention.md) | P1 | File Descriptor Leak Prevention | [§17](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md) |
| [REQ-F-072](f-072-lf-line-ending-enforcement.md) | P1 | LF Line Ending Enforcement | — |
| [REQ-F-073](f-073-env-var-namespace-prefix.md) | P1 | Environment Variable Namespace Prefix | [§65](../challenges/01-critical-ecosystem-runtime-agent-specific/65-high-global-config-contamination.md) |
| [REQ-F-074](f-074-json-null-absent-empty-convention.md) | P1 | JSON Null/Absent/Empty Convention | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-F-075](f-075-subcommand-additive-stability.md) | P1 | Subcommand Additive Stability | [§22](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) |
| [REQ-F-076](f-076-first-run-init-isolation.md) | P1 | First-Run Init Isolation | — |
| [REQ-F-077](f-077-telemetry-non-blocking.md) | P2 | Telemetry Non-Blocking | [§41](../challenges/01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md) |
| [REQ-F-078](f-078-retry-count-in-response-meta.md) | P2 | Retry Count in Response Meta | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) |

---

## Command Contract (C)

**29 requirements** &nbsp;|&nbsp; P0: 12 · P1: 14 · P2: 1 · P3: 2

| ID | Priority | Title | Failure mode(s) |
|----|----------|-------|-------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | P0 | Command Declares Exit Codes | [§1](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) |
| [REQ-C-002](c-002-command-declares-danger-level.md) | P0 | Command Declares Danger Level | [§23](../challenges/03-critical-security/23-critical-destructive-ops.md) |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | P0 | Mutating Commands Declare effect Field | [§12](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md) |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | P0 | Destructive Commands Must Support --dry-run | [§23](../challenges/03-critical-security/23-critical-destructive-ops.md) |
| [REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md) | P0 | Interactive Commands Must Support --yes / --non-interactive | [§10](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) |
| [REQ-C-006](c-006-all-args-validated-in-phase-1.md) | P0 | All Args Validated in Phase 1 | [§14](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md) |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | P1 | Mutating Commands Accept --idempotency-key | [§12](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md) |
| [REQ-C-008](c-008-multi-step-commands-emit-step-manifest.md) | P1 | Multi-Step Commands Emit Step Manifest | [§13](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md) |
| [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) | P1 | Multi-Step Commands Report completed/failed/skipped | [§13](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md) |
| [REQ-C-010](c-010-background-process-commands-declare-metadata.md) | P2 | Background-Process Commands Declare Metadata | [§17](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md) |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | P3 | Commands Declare Filesystem Side Effects | [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-C-012](c-012-commands-with-network-i-o-support-timeout.md) | P0 | Commands with Network I/O Support --timeout | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | P0 | Error Responses Include Code and Message | [§18](../challenges/06-high-errors-and-discoverability/18-high-error-quality.md) |
| [REQ-C-014](c-014-error-responses-include-retryable-and-retry-after-.md) | P1 | Error Responses Include retryable and retry_after_ms | [§19](../challenges/06-high-errors-and-discoverability/19-high-retry-hints.md) |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | P1 | Commands Declare Input and Output Schema | [§21](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md) |
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | P1 | Secrets Accepted Only via Env Var or File | [§24](../challenges/03-critical-security/24-critical-auth-secrets.md) |
| [REQ-C-017](c-017-commands-register-cleanup-hook.md) | P1 | Commands Register cleanup() Hook | [§16](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md) |
| [REQ-C-018](c-018-commands-declare-platform-requirements.md) | P3 | Commands Declare Platform Requirements | [§27](../challenges/05-high-environment-and-state/27-medium-platform-portability.md) |
| [REQ-C-019](c-019-subprocess-invoking-commands-declare-argument-sche.md) | P1 | Subprocess-Invoking Commands Declare Argument Schema | [§34](../challenges/01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md) |
| [REQ-C-020](c-020-resource-id-fields-declare-validation-pattern.md) | P1 | Resource ID Fields Declare Validation Pattern | [§35](../challenges/01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md) |
| [REQ-C-021](c-021-auth-commands-declare-headless-mode-support.md) | P0 | Auth Commands Declare Headless Mode Support | [§45](../challenges/01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) |
| [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md) | P0 | Async Commands Declare Job Descriptor Schema | [§49](../challenges/01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md) |
| [REQ-C-023](c-023-editor-requiring-commands-declare-non-interactive-.md) | P1 | Editor-Requiring Commands Declare Non-Interactive Alternative | [§62](../challenges/01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md) |
| [REQ-C-024](c-024-gui-launching-commands-declare-headless-behavior.md) | P1 | GUI-Launching Commands Declare Headless Behavior | [§64](../challenges/01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md) |
| [REQ-C-025](c-025-config-writing-commands-declare-write-scope.md) | P0 | Config-Writing Commands Declare Write Scope | [§65](../challenges/01-critical-ecosystem-runtime-agent-specific/65-high-global-config-contamination.md) |
| [REQ-C-026](c-026-commands-declare-conditional-argument-dependencies.md) | P1 | Commands Declare Conditional Argument Dependencies | [§54](../challenges/01-critical-ecosystem-runtime-agent-specific/54-high-conditional-args.md) |
| [REQ-C-027](c-027-commands-declare-option-placement.md) | P1 | Commands Declare Option Placement Convention | [§69](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) |
| [REQ-C-028](c-028-already-exists-response-pattern.md) | P1 | ALREADY_EXISTS Response Pattern | [§12](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md) |
| [REQ-C-029](c-029-command-declares-required-scopes.md) | P0 | Command Declares Required Scopes | [§74](../challenges/03-critical-security/74-critical-credential-scope-declaration.md) |

---

## Opt-In (O)

**48 requirements** &nbsp;|&nbsp; P0: 6 · P1: 19 · P2: 17 · P3: 6

| ID | Priority | Title | Failure mode(s) |
|----|----------|-------|-------------|
| [REQ-O-001](o-001-output-format-flag.md) | P0 | --output Format Flag | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-O-002](o-002-fields-selector.md) | P2 | --fields Selector | [§4](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) |
| [REQ-O-003](o-003-limit-and-cursor-pagination-flags.md) | P0 | --limit and --cursor Pagination Flags | [§5](../challenges/04-critical-output-and-parsing/05-high-pagination.md) |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | P2 | --output jsonl / --stream Flag | [§5](../challenges/04-critical-output-and-parsing/05-high-pagination.md) |
| [REQ-O-005](o-005-output-id-extraction-mode.md) | P3 | --output id Extraction Mode | [§6](../challenges/04-critical-output-and-parsing/06-medium-command-composition.md) |
| [REQ-O-006](o-006-stdin-as-id-source.md) | P3 | Stdin as ID Source (-) | [§6](../challenges/04-critical-output-and-parsing/06-medium-command-composition.md) |
| [REQ-O-007](o-007-stable-output-flag.md) | P3 | --stable-output Flag | [§7](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md) |
| [REQ-O-008](o-008-quiet-verbose-debug-verbosity-flags.md) | P1 | --quiet / --verbose / --debug Verbosity Flags | [§4](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) |
| [REQ-O-009](o-009-validate-only-flag.md) | P1 | --validate-only Flag | [§14](../challenges/02-critical-execution-and-reliability/14-high-arg-validation.md) |
| [REQ-O-010](o-010-resume-from-flag-for-multi-step-commands.md) | P2 | --resume-from Flag for Multi-Step Commands | [§13](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md) |
| [REQ-O-011](o-011-rollback-on-failure-flag.md) | P2 | --rollback-on-failure Flag | [§13](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md) |
| [REQ-O-012](o-012-heartbeat-interval-flag.md) | P2 | --heartbeat-interval Flag | [§11](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) |
| [REQ-O-013](o-013-schema-output-schema-flag.md) | P1 | --schema / --output-schema Flag | [§21](../challenges/06-high-errors-and-discoverability/21-medium-schema-discoverability.md) |
| [REQ-O-014](o-014-schema-version-compatibility-flag.md) | P2 | --schema-version Compatibility Flag | [§22](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) |
| [REQ-O-015](o-015-show-config-flag.md) | P1 | --show-config Flag | [§28](../challenges/05-high-environment-and-state/28-high-config-shadowing.md) |
| [REQ-O-016](o-016-no-config-flag.md) | P1 | --no-config Flag | [§28](../challenges/05-high-environment-and-state/28-high-config-shadowing.md) |
| [REQ-O-017](o-017-cwd-root-flag.md) | P2 | --cwd / --root Flag | [§29](../challenges/05-high-environment-and-state/29-medium-working-directory.md) |
| [REQ-O-018](o-018-no-cache-and-cache-ttl-flags.md) | P3 | --no-cache and --cache-ttl Flags | [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-O-019](o-019-proxy-and-no-proxy-flags.md) | P2 | --proxy and --no-proxy Flags | [§31](../challenges/05-high-environment-and-state/31-high-network-proxy.md) |
| [REQ-O-020](o-020-no-update-check-flag.md) | P1 | --no-update-check Flag | [§32](../challenges/05-high-environment-and-state/32-high-self-update.md) |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | P0 | --confirm-destructive Flag | [§23](../challenges/03-critical-security/23-critical-destructive-ops.md) |
| [REQ-O-022](o-022-secret-from-env-secret-from-file-flags.md) | P1 | --secret-from-env / --secret-from-file Flags | [§24](../challenges/03-critical-security/24-critical-auth-secrets.md) |
| [REQ-O-023](o-023-no-injection-protection-flag.md) | P3 | --no-injection-protection Flag | [§25](../challenges/03-critical-security/25-critical-prompt-injection.md) |
| [REQ-O-024](o-024-context-config-override-flag.md) | P1 | --context / --config Override Flag | [§26](../challenges/05-high-environment-and-state/26-high-session-management.md) |
| [REQ-O-025](o-025-warnings-as-errors-flag.md) | P3 | --warnings-as-errors Flag | [§3](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md) |
| [REQ-O-026](o-026-tool-doctor-built-in-command.md) | P1 | tool doctor Built-In Command | [§20](../challenges/06-high-errors-and-discoverability/20-medium-dependency-discovery.md) |
| [REQ-O-027](o-027-tool-cleanup-built-in-command.md) | P2 | tool cleanup Built-In Command | [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-O-028](o-028-tool-status-built-in-command.md) | P2 | tool status Built-In Command | [§26](../challenges/05-high-environment-and-state/26-high-session-management.md) [§30](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md) |
| [REQ-O-029](o-029-tool-changelog-built-in-command.md) | P2 | tool changelog Built-In Command | [§22](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) |
| [REQ-O-030](o-030-tool-audit-log-built-in-command.md) | P2 | tool audit-log Built-In Command | [§33](../challenges/07-medium-observability/33-medium-observability.md) |
| [REQ-O-031](o-031-dependency-version-matrix-declaration.md) | P1 | Dependency Version Matrix Declaration | [§38](../challenges/01-critical-ecosystem-runtime-agent-specific/38-high-dependency-version-mismatch.md) |
| [REQ-O-032](o-032-raw-payload-flag-for-mutating-commands.md) | P1 | --raw-payload Flag for Mutating Commands | [§46](../challenges/01-critical-ecosystem-runtime-agent-specific/46-high-api-translation-loss.md) |
| [REQ-O-033](o-033-headless-and-token-env-var-flags-for-auth-commands.md) | P0 | --headless and --token-env-var Flags for Auth Commands | [§45](../challenges/01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) |
| [REQ-O-034](o-034-tool-generate-skills-built-in-command.md) | P2 | tool generate-skills Built-In Command | [§44](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) |
| [REQ-O-035](o-035-tool-mcp-validate-built-in-command.md) | P2 | tool mcp-validate Built-In Command | [§47](../challenges/01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md) |
| [REQ-O-036](o-036-instance-id-flag-for-agent-state-namespacing.md) | P1 | --instance-id Flag for Agent State Namespacing | [§58](../challenges/01-critical-ecosystem-runtime-agent-specific/58-high-multiagent-conflict.md) |
| [REQ-O-037](o-037-unmask-flag-for-high-entropy-fields.md) | P2 | --unmask Flag for High-Entropy Fields | [§59](../challenges/01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md) |
| [REQ-O-038](o-038-heartbeat-ms-flag-for-long-running-commands.md) | P1 | --heartbeat-ms Flag for Long-Running Commands | [§60](../challenges/01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) [§49](../challenges/01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md) |
| [REQ-O-039](o-039-input-file-flag-for-stdin-commands.md) | P1 | --input-file Flag for Stdin Commands | [§61](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) [§50](../challenges/01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) |
| [REQ-O-040](o-040-no-follow-symlinks-flag-for-traversal-commands.md) | P1 | --no-follow-symlinks Flag for Traversal Commands | [§66](../challenges/01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md) |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | P1 | tool manifest Built-In Command | [§52](../challenges/01-critical-ecosystem-runtime-agent-specific/52-medium-command-tree-discovery.md) |
| [REQ-O-042](o-042-output-format-env-var-default.md) | P2 | Output Format Environment Variable Default | [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) |
| [REQ-O-043](o-043-agents-md-content-spec.md) | P1 | AGENTS.md Required Content | [§44](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) [§73](../challenges/01-critical-ecosystem-runtime-agent-specific/73-high-documentation-accuracy-drift.md) |
| [REQ-O-044](o-044-noninteractive-install-command.md) | P1 | Non-Interactive Install Command Documentation | [§71](../challenges/01-critical-ecosystem-runtime-agent-specific/71-critical-noninteractive-installation.md) |
| [REQ-O-045](o-045-integration-artifact-version-declaration.md) | P1 | Integration Artifact Version Declaration | [§72](../challenges/01-critical-ecosystem-runtime-agent-specific/72-high-integration-artifact-drift.md) [§47](../challenges/01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md) |
| [REQ-O-046](o-046-agents-md-ci-validation.md) | P2 | AGENTS.md CI Validation | [§73](../challenges/01-critical-ecosystem-runtime-agent-specific/73-high-documentation-accuracy-drift.md) [§44](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) |
| [REQ-O-047](o-047-tool-check-permissions-built-in-command.md) | P0 | tool check-permissions Built-In Command | [§74](../challenges/03-critical-security/74-critical-credential-scope-declaration.md) |
| [REQ-O-048](o-048-destructive-commands-default-dry-run.md) | P0 | Destructive Commands Default to Dry-Run Mode | [§75](../challenges/03-critical-security/75-critical-safe-default-execution.md) |

---

*CLI Agent Spec v1.6 — 154 requirements (78 REQ-F + 29 REQ-C + 47 REQ-O). Updated 2026-05-07.*
