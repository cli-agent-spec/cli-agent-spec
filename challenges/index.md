# CLI Agent Spec — Full Index

> All 73 failure modes across 7 parts. Each failure mode linked to its source file.

---

## Table of Contents

- [Part 1: Ecosystem Runtime Agent Specific](#1-ecosystem-runtime-agent-specific)
- [Part 2: Execution And Reliability](#2-execution-and-reliability)
- [Part 3: Security](#3-security)
- [Part 4: Output And Parsing](#4-output-and-parsing)
- [Part 5: Environment And State](#5-environment-and-state)
- [Part 6: Errors And Discoverability](#6-errors-and-discoverability)
- [Part 7: Observability](#7-observability)

---

## 1. Ecosystem Runtime Agent Specific

> Agent-specific patterns discovered from real frameworks, libraries, and multi-agent deployments.

**37 failure modes** &nbsp;|&nbsp; 🔴 12 critical · 🟠 21 high · 🟡 4 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§34](01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md) | Shell Injection via Agent-Constructed Commands | 🔴 Critical | Common | Hard | High | High | Medium |
| [§37](01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md) | REPL / Interactive Mode Accidental Triggering | 🔴 Critical | Situational | Hard | High | Critical | Low |
| [§42](01-critical-ecosystem-runtime-agent-specific/42-critical-debug-secret-leakage.md) | Debug / Trace Mode Secret Leakage | 🔴 Critical | Situational | Hard | Low | Low | High |
| [§43](01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md) | Tool Output Result Size Unboundedness | 🔴 Critical | Common | Hard | Critical | High | Critical |
| [§45](01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) | Headless Authentication / OAuth Browser Flow Blocking | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§50](01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) | Stdin Consumption Deadlock | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§53](01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md) | Credential Expiry Mid-Session | 🔴 Critical | Common | Hard | High | High | Low |
| [§60](01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) | OS Output Buffer Deadlock | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§61](01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) | Bidirectional Pipe Payload Deadlock | 🔴 Critical | Situational | Hard | High | Critical | Low |
| [§62](01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md) | $EDITOR and $VISUAL Trap | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§64](01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md) | Headless Display and GUI Launch Blocking | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§71](01-critical-ecosystem-runtime-agent-specific/71-critical-noninteractive-installation.md) | Non-Interactive Installation Absence | 🔴 Critical | Common | Easy | Low | Critical | Low |
| [§35](01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md) | Agent Hallucination Input Patterns | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§38](01-critical-ecosystem-runtime-agent-specific/38-high-dependency-version-mismatch.md) | Runtime Dependency Version Mismatch | 🟠 High | Common | Medium | High | High | Low |
| [§40](01-critical-ecosystem-runtime-agent-specific/40-high-async-race-condition.md) | `parse()` vs `parseAsync()` Silent Race Condition | 🟠 High | Common (Node.js ecosystem) | Hard | High | High | Low |
| [§41](01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md) | Update Notifier Side-Channel Output Pollution | 🟠 High | Common (Node.js/npm ecosystem) | Medium | Medium | Medium | Medium |
| [§46](01-critical-ecosystem-runtime-agent-specific/46-high-api-translation-loss.md) | API Schema to CLI Flag Translation Loss | 🟠 High | Common | Medium | High | Medium | Medium |
| [§47](01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md) | MCP Wrapper Schema Staleness | 🟠 High | Common | Hard | High | High | Low |
| [§49](01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md) | Async Job / Polling Protocol Absence | 🟠 High | Common | Hard | High | High | Medium |
| [§51](01-critical-ecosystem-runtime-agent-specific/51-high-glob-expansion.md) | Shell Word Splitting and Glob Expansion Interference | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§54](01-critical-ecosystem-runtime-agent-specific/54-high-conditional-args.md) | Conditional / Dependent Argument Requirements | 🟠 High | Common | Hard | High | Medium | Low |
| [§55](01-critical-ecosystem-runtime-agent-specific/55-high-silent-truncation.md) | Silent Data Truncation | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§56](01-critical-ecosystem-runtime-agent-specific/56-high-pipeline-exit-masking.md) | Exit Code Masking in Shell Pipelines | 🟠 High | Common | Hard | Medium | Low | Low |
| [§58](01-critical-ecosystem-runtime-agent-specific/58-high-multiagent-conflict.md) | Multi-Agent Concurrent Invocation Conflict | 🟠 High | Situational | Hard | Medium | High | Low |
| [§59](01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md) | High-Entropy String Token Poisoning | 🟠 High | Common | Medium | High | Low | High |
| [§65](01-critical-ecosystem-runtime-agent-specific/65-high-global-config-contamination.md) | Global Configuration State Contamination | 🟠 High | Common | Hard | Medium | High | Low |
| [§66](01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md) | Symlink Loop and Recursive Traversal Exhaustion | 🟠 High | Situational | Hard | Medium | Critical | Low |
| [§67](01-critical-ecosystem-runtime-agent-specific/67-high-json5-input.md) | Agent-Generated Input Syntax Rejection | 🟠 High | Common | Easy | High | Medium | Low |
| [§68](01-critical-ecosystem-runtime-agent-specific/68-high-stdout-pollution.md) | Third-Party Library Stdout Pollution | 🟠 High | Common | Medium | Medium | Low | High |
| [§69](01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) | Argument Order Ambiguity | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§70](01-critical-ecosystem-runtime-agent-specific/70-high-single-argument-arity.md) | Single-Argument Arity Forcing Agent Loop Overhead | 🟠 High | Common | Easy | Medium | Medium | Low |
| [§72](01-critical-ecosystem-runtime-agent-specific/72-high-integration-artifact-drift.md) | Integration Artifact Version Drift | 🟠 High | Common | Medium | High | Medium | Low |
| [§73](01-critical-ecosystem-runtime-agent-specific/73-high-documentation-accuracy-drift.md) | Documentation Accuracy Drift | 🟠 High | Common | Hard | High | Medium | Low |
| [§44](01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) | Agent Knowledge Packaging Absence | 🟡 Medium | Very Common | Easy | High | High | Medium |
| [§52](01-critical-ecosystem-runtime-agent-specific/52-medium-command-tree-discovery.md) | Recursive Command Tree Discovery Cost | 🟡 Medium | Very Common | Easy | High | Medium | High |
| [§57](01-critical-ecosystem-runtime-agent-specific/57-medium-locale-errors.md) | Locale-Dependent Error Messages | 🟡 Medium | Situational | Easy | High | Low | Medium |
| [§63](01-critical-ecosystem-runtime-agent-specific/63-medium-column-width-corruption.md) | Terminal Column Width Output Corruption | 🟡 Medium | Common | Easy | Medium | Low | Medium |

---

## 2. Execution And Reliability

> Execution flow, blocking behavior, atomicity, and reliability under agent orchestration.

**8 failure modes** &nbsp;|&nbsp; 🔴 4 critical · 🟠 3 high · 🟡 1 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§10](02-critical-execution-and-reliability/10-critical-interactivity.md) | Interactivity & TTY Requirements | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§11](02-critical-execution-and-reliability/11-critical-timeouts.md) | Timeouts & Hanging Processes | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§12](02-critical-execution-and-reliability/12-critical-idempotency.md) | Idempotency & Safe Retries | 🔴 Critical | Common | Hard | High | High | Medium |
| [§13](02-critical-execution-and-reliability/13-critical-partial-failure.md) | Partial Failure & Atomicity | 🔴 Critical | Common | Hard | High | High | Medium |
| [§14](02-critical-execution-and-reliability/14-high-arg-validation.md) | Argument Validation Before Side Effects | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§15](02-critical-execution-and-reliability/15-high-race-conditions.md) | Race Conditions & Concurrency | 🟠 High | Situational | Hard | Medium | Medium | Low |
| [§16](02-critical-execution-and-reliability/16-high-signal-handling.md) | Signal Handling & Graceful Cancellation | 🟠 High | Situational | Hard | Medium | Medium | Low |
| [§17](02-critical-execution-and-reliability/17-medium-child-process-leakage.md) | Child Process Leakage | 🟡 Medium | Situational | Hard | Low | Low | Low |

---

## 3. Security

> Destructive operations, authentication, secret handling, and prompt injection.

**5 failure modes** &nbsp;|&nbsp; 🔴 5 critical

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§23](03-critical-security/23-critical-destructive-ops.md) | Side Effects & Destructive Operations | 🔴 Critical | Common | Medium | Medium | High | Medium |
| [§24](03-critical-security/24-critical-auth-secrets.md) | Authentication & Secret Handling | 🔴 Critical | Common | Hard | Medium | Medium | Low |
| [§25](03-critical-security/25-critical-prompt-injection.md) | Prompt Injection via Output | 🔴 Critical | Situational | Hard | High | High | High |
| [§74](03-critical-security/74-critical-credential-scope-declaration.md) | Credential Scope Declaration Absence | 🔴 Critical | Common | Hard | Low | Medium | Low |
| [§75](03-critical-security/75-critical-safe-default-execution.md) | Safe-Default Execution Mode Absent | 🔴 Critical | Situational | Hard | Low | Critical | Low |

---

## 4. Output And Parsing

> How CLI tools format, stream, and structure their output for agent consumption.

**10 failure modes** &nbsp;|&nbsp; 🔴 2 critical · 🟠 5 high · 🟡 3 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§1](04-critical-output-and-parsing/01-critical-exit-codes.md) | Exit Codes & Status Signaling | 🔴 Critical | Very Common | Hard | High | High | Low |
| [§2](04-critical-output-and-parsing/02-critical-output-format.md) | Output Format & Parseability | 🔴 Critical | Very Common | Easy | High | Medium | High |
| [§3](04-critical-output-and-parsing/03-high-stderr-stdout.md) | Stderr vs Stdout Discipline | 🟠 High | Very Common | Hard | Medium | Low | High |
| [§5](04-critical-output-and-parsing/05-high-pagination.md) | Pagination & Large Output | 🟠 High | Common | Hard | High | High | Critical |
| [§8](04-critical-output-and-parsing/08-high-ansi-leakage.md) | ANSI & Color Code Leakage | 🟠 High | Common | Hard | Medium | Low | Medium |
| [§9](04-critical-output-and-parsing/09-high-binary-encoding.md) | Binary & Encoding Safety | 🟠 High | Situational | Hard | Low | Medium | Low |
| [§76](04-critical-output-and-parsing/76-high-streaming-default-incompatibility.md) | Streaming-Default JSONL Incompatibility | 🟠 High | Situational | Medium | Medium | Low | Medium |
| [§4](04-critical-output-and-parsing/04-medium-verbosity.md) | Verbosity & Token Cost | 🟡 Medium | Very Common | Easy | High | Low | High |
| [§6](04-critical-output-and-parsing/06-medium-command-composition.md) | Command Composition & Piping | 🟡 Medium | Common | Easy | Medium | Low | Low |
| [§7](04-critical-output-and-parsing/07-medium-output-nondeterminism.md) | Output Non-Determinism | 🟡 Medium | Common | Hard | Medium | Medium | Low |

---

## 5. Environment And State

> Session state, configuration, working directory, filesystem, network, and runtime environment.

**7 failure modes** &nbsp;|&nbsp; 🟠 4 high · 🟡 3 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§26](05-high-environment-and-state/26-high-session-management.md) | Stateful Commands & Session Management | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§28](05-high-environment-and-state/28-high-config-shadowing.md) | Config File Shadowing & Precedence | 🟠 High | Common | Hard | High | High | Medium |
| [§31](05-high-environment-and-state/31-high-network-proxy.md) | Network Proxy Unawareness | 🟠 High | Situational | Hard | Medium | High | Low |
| [§32](05-high-environment-and-state/32-high-self-update.md) | Self-Update & Auto-Upgrade Behavior | 🟠 High | Situational | Hard | Medium | High | Low |
| [§27](05-high-environment-and-state/27-medium-platform-portability.md) | Platform & Shell Portability | 🟡 Medium | Common | Easy | Medium | Medium | Low |
| [§29](05-high-environment-and-state/29-medium-working-directory.md) | Working Directory Sensitivity | 🟡 Medium | Common | Medium | Medium | Low | Low |
| [§30](05-high-environment-and-state/30-medium-filesystem-side-effects.md) | Undeclared Filesystem Side Effects | 🟡 Medium | Common | Hard | Low | Low | Low |

---

## 6. Errors And Discoverability

> Error quality, retry guidance, schema discovery, and versioning.

**5 failure modes** &nbsp;|&nbsp; 🟠 3 high · 🟡 2 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§18](06-high-errors-and-discoverability/18-high-error-quality.md) | Error Message Quality | 🟠 High | Very Common | Easy | High | Medium | High |
| [§19](06-high-errors-and-discoverability/19-high-retry-hints.md) | Retry Hints in Error Responses | 🟠 High | Very Common | Medium | High | High | Medium |
| [§22](06-high-errors-and-discoverability/22-high-schema-versioning.md) | Schema Versioning & Output Stability | 🟠 High | Common | Hard | High | High | Medium |
| [§20](06-high-errors-and-discoverability/20-medium-dependency-discovery.md) | Environment & Dependency Discovery | 🟡 Medium | Common | Easy | Medium | Medium | Low |
| [§21](06-high-errors-and-discoverability/21-medium-schema-discoverability.md) | Schema & Help Discoverability | 🟡 Medium | Very Common | Easy | High | Medium | Medium |

---

## 7. Observability

> Audit trails, request tracing, and operational visibility.

**1 failure mode** &nbsp;|&nbsp; 🟡 1 medium

| # | Title | Severity | Frequency | Detectability | Token Spend | Time | Context |
|---|-------|----------|-----------|---------------|-------------|------|---------|
| [§33](07-medium-observability/33-medium-observability.md) | Observability & Audit Trail | 🟡 Medium | Very Common | Easy | Medium | High | Medium |

---

*73 active failure modes across 7 parts. CLI Agent Spec v1.6 — 2026-05-07.*
