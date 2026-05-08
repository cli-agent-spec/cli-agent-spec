# Challenge Sources & Epistemic Status

This file documents where each challenge came from, how confident the source is, and what kind of evidence supports it. Understanding the source matters for prioritization — a challenge derived from first principles is structurally guaranteed to be real; one absorbed from training data is real but anecdotal.

---

## Source Categories

| Code | Type | Description | Confidence |
|------|------|-------------|------------|
| **FP** | First-principles inference | Logically deduced from the agent interaction model — no experience required | High (structural) |
| **TD** | Training data pattern | Absorbed from GitHub issues, blog posts, Stack Overflow, CLI library docs, forum threads during training | Medium (anecdotal, unverifiable) |
| **RA** | Research artifact | Read from specific real source code, docs, or spec during this project's research phase | High (verifiable) |
| **TD+FP** | Both | Attested in training data AND independently derivable from first principles | Very High |

---

## Challenge Source Map

### Part I: Output & Parsing

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§1](04-critical-output-and-parsing/01-critical-exit-codes.md) | Exit Codes & Status Signaling | TD+FP | Exit code 0/1 overloading is described in dozens of CLI design guides and POSIX docs; structurally guaranteed: agents branch on exit code, so ambiguity causes misrouting |
| [§2](04-critical-output-and-parsing/02-critical-output-format.md) | Output Format & Parseability | TD+FP | Ubiquitous in agent/LLM tool-use literature; structurally guaranteed: agent reads stdout as data |
| [§3](04-critical-output-and-parsing/03-high-stderr-stdout.md) | Stderr vs Stdout Discipline | TD+FP | Very common complaint in agent tooling discussions; structurally guaranteed: mixing streams breaks downstream parsing |
| [§4](04-critical-output-and-parsing/04-medium-verbosity.md) | Verbosity & Token Cost | TD+FP | Token cost framing is specific to LLM agent context; verbose output filling context window is structurally predictable |
| [§5](04-critical-output-and-parsing/05-high-pagination.md) | Pagination & Large Output | TD+FP | Pagination as a list API problem is well-documented; context-window overflow framing is agent-specific pattern from training |
| [§6](04-critical-output-and-parsing/06-medium-command-composition.md) | Command Composition & Piping | TD | Classic Unix piping design discussion; agent-specific ID chaining pattern absorbed from agent tool-use guides |
| [§7](04-critical-output-and-parsing/07-medium-output-nondeterminism.md) | Output Non-Determinism | TD+FP | Non-deterministic output breaking diffing is a known CI/CD problem; agent retry-loop consequence is first-principles inference |
| [§8](04-critical-output-and-parsing/08-high-ansi-leakage.md) | ANSI & Color Code Leakage | TD+FP | Extremely common complaint in both CI and agent contexts; structurally guaranteed if agent reads stdout |
| [§9](04-critical-output-and-parsing/09-high-binary-encoding.md) | Binary & Encoding Safety | TD | Binary-in-JSON encoding issues documented in API design guides and CLI output handling discussions |

### Part II: Execution & Reliability

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§10](02-critical-execution-and-reliability/10-critical-interactivity.md) | Interactivity & TTY Requirements | TD+FP | Most-cited agent CLI problem in training data; structurally guaranteed: non-TTY + prompt = deadlock |
| [§11](02-critical-execution-and-reliability/11-critical-timeouts.md) | Timeouts & Hanging Processes | TD+FP | Hanging processes in automation documented extensively; timeout budget exhaustion is first-principles inference |
| [§12](02-critical-execution-and-reliability/12-critical-idempotency.md) | Idempotency & Safe Retries | TD+FP | Idempotency keys documented in Stripe API design, distributed systems literature; agent retry-safety framing from agent SDK discussions |
| [§13](02-critical-execution-and-reliability/13-critical-partial-failure.md) | Partial Failure & Atomicity | TD+FP | Multi-step failure handling is a classic distributed systems problem; agent-specific resume/rollback framing from training |
| [§14](02-critical-execution-and-reliability/14-high-arg-validation.md) | Argument Validation Before Side Effects | TD+FP | Validate-before-execute principle is well-documented; exit-2-guarantees-no-side-effects framing is agent-specific |
| [§15](02-critical-execution-and-reliability/15-high-race-conditions.md) | Race Conditions & Concurrency | TD | Concurrent access to shared CLI state documented in CLI design guides and lock-file discussions |
| [§16](02-critical-execution-and-reliability/16-high-signal-handling.md) | Signal Handling & Graceful Cancellation | TD+FP | SIGTERM handling is documented POSIX behavior; cleanup-on-cancel for agents is first-principles inference |
| [§17](02-critical-execution-and-reliability/17-medium-child-process-leakage.md) | Child Process Leakage | TD | Zombie process and orphaned child documentation from Unix process management literature |

### Part III: Errors & Discoverability

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§18](06-high-errors-and-discoverability/18-high-error-quality.md) | Error Message Quality | TD+FP | Good error message design is well-documented (e.g., Rust compiler errors blog posts); machine-parseable error framing is agent-specific |
| [§19](06-high-errors-and-discoverability/19-high-retry-hints.md) | Retry Hints in Error Responses | TD | Retry-After header pattern from HTTP RFCs; CLI-level retry hints absorbed from API design guides and agent tooling discussions |
| [§20](06-high-errors-and-discoverability/20-medium-dependency-discovery.md) | Environment & Dependency Discovery | TD | Dependency preflight checking documented in CLI tool design; agent-specific "doctor" pattern from Homebrew, Flutter doctor |
| [§21](06-high-errors-and-discoverability/21-medium-schema-discoverability.md) | Schema & Help Discoverability | TD+FP | Help discoverability for agents is documented in MCP and agent SDK guides; structurally guaranteed: agent needs machine-readable schema to construct valid calls |
| [§22](06-high-errors-and-discoverability/22-high-schema-versioning.md) | Schema Versioning & Output Stability | TD | API versioning literature; schema-version-in-output pattern from REST API design guides and GraphQL introspection discussions |

### Part IV: Security

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§23](03-critical-security/23-critical-destructive-ops.md) | Side Effects & Destructive Operations | TD+FP | Dry-run and confirmation patterns are well-documented; agent-specific "no human to catch mistakes" risk framing from agent safety discussions |
| [§24](03-critical-security/24-critical-auth-secrets.md) | Authentication & Secret Handling | TD+FP | Secret-in-env-var pattern is documented in 12-factor app, CI/CD guides; agent-specific leakage vectors from agent security training data |
| [§25](03-critical-security/25-critical-prompt-injection.md) | Prompt Injection via Output | TD | Prompt injection via tool output is documented in LLM security research (Greshake et al., similar papers absorbed in training) |
| [§74](03-critical-security/74-critical-credential-scope-declaration.md) | Credential Scope Declaration Absence | FP | Observed during gh evaluation: personal PAT grants full account access to agent; OAuth scope minimization is standard security practice but absent from CLI design guides |

### Part V: Environment & State

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§26](05-high-environment-and-state/26-high-session-management.md) | Stateful Commands & Session Management | TD | Session state in CLIs documented in tool design guides; agent session isolation framing from agent SDK discussions |
| [§27](05-high-environment-and-state/27-medium-platform-portability.md) | Platform & Shell Portability | TD | Cross-platform CLI portability is extensively documented; `#!/usr/bin/env` and POSIX shell compatibility are classic topics |
| [§28](05-high-environment-and-state/28-high-config-shadowing.md) | Config File Shadowing & Precedence | TD | Config precedence (env > file > default) is documented in 12-factor app and CLI design guides; agent-specific confusion absorbed from troubleshooting discussions |
| [§29](05-high-environment-and-state/29-medium-working-directory.md) | Working Directory Sensitivity | TD+FP | CWD sensitivity is a well-known scripting hazard; agent-specific absolute-path requirement is first-principles inference |
| [§30](05-high-environment-and-state/30-medium-filesystem-side-effects.md) | Undeclared Filesystem Side Effects | TD | Side effect declaration is documented in functional programming and CLI design; agent-specific cleanup challenges absorbed from automation tooling discussions |
| [§31](05-high-environment-and-state/31-high-network-proxy.md) | Network Proxy Unawareness | TD | Proxy env var support (`HTTP_PROXY`, `HTTPS_PROXY`) is documented in many HTTP library guides; agent-specific inference from enterprise environment discussions |
| [§32](05-high-environment-and-state/32-high-self-update.md) | Self-Update & Auto-Upgrade Behavior | TD | Auto-update in non-interactive mode is a known CI problem; agent-specific output pollution framing absorbed from automation discussions |

### Part VI: Observability

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§33](07-medium-observability/33-medium-observability.md) | Observability & Audit Trail | TD | Structured logging, request IDs, and audit trails are documented in production engineering guides; agent-specific trace propagation from OpenTelemetry and agent SDK discussions |

### Part VII: Ecosystem, Runtime & Agent-Specific (§34–47, §49–70)

Discovered by reading specific real artifacts during the research phase of this project.

#### §34–47: Research phase (jpoehnelt SKILL.md, agentyper, Commander.js, MCP spec)

| # | Challenge | Source | Primary Artifact |
|---|-----------|--------|-----------------|
| [§34](01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md) | Shell Injection via Agent-Constructed Commands | RA+FP | jpoehnelt SKILL.md — Input Hardening axis; structurally guaranteed when agents construct shell strings |
| [§35](01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md) | Agent Hallucination Input Patterns | RA+FP | jpoehnelt SKILL.md — Input Hardening axis; path traversal and percent-encoding patterns from OWASP |
| ~~[§36](02-critical-execution-and-reliability/10-critical-interactivity.md)~~ | ~~Pager Invocation Blocking Agent Pipelines~~ | RA | **MERGED into [§10](02-critical-execution-and-reliability/10-critical-interactivity.md)** — pager blocking is a specific case of interactivity/TTY deadlock |
| [§37](01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md) | REPL / Interactive Mode Accidental Triggering | RA+FP | Python argparse subparser fallback behavior; structurally guaranteed in non-TTY context |
| [§38](01-critical-ecosystem-runtime-agent-specific/38-high-dependency-version-mismatch.md) | Runtime Dependency Version Mismatch | RA | Cobra and Clap docs on runtime dependency checking; Node.js engine field pattern |
| ~~[§39](04-critical-output-and-parsing/03-high-stderr-stdout.md)~~ | ~~Help Text Routed to Stdout~~ | RA | **MERGED into [§3](04-critical-output-and-parsing/03-high-stderr-stdout.md)** — routing help to stdout is a specific case of stderr/stdout stream discipline |
| [§40](01-critical-ecosystem-runtime-agent-specific/40-high-async-race-condition.md) | `parse()` vs `parseAsync()` Silent Race Condition | RA | Commander.js docs — explicit warning about async/sync mismatch |
| [§41](01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md) | Update Notifier Side-Channel Output Pollution | RA | `update-notifier` npm package behavior; Python pip version check behavior |
| [§42](01-critical-ecosystem-runtime-agent-specific/42-critical-debug-secret-leakage.md) | Debug / Trace Mode Secret Leakage | RA | Python Fire `--trace` flag — documented in python-fire README and issue tracker |
| [§43](01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md) | Tool Output Result Size Unboundedness | RA | jpoehnelt SKILL.md — Context Window Discipline axis; MCP spec `maxTokens` parameter |
| [§44](01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) | Agent Knowledge Packaging Absence | RA | jpoehnelt SKILL.md — entire premise; agentyper `--schema` flag; OpenClaw SKILL format |
| [§45](01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) | Headless Authentication / OAuth Browser Flow Blocking | RA+FP | agentyper docs — headless auth; structurally guaranteed: browser redirect in non-TTY = deadlock |
| [§46](01-critical-ecosystem-runtime-agent-specific/46-high-api-translation-loss.md) | API Schema to CLI Flag Translation Loss | RA | Comparison matrix research — every parser framework loses nested/union types in flag translation |
| [§47](01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md) | MCP Wrapper Schema Staleness | RA | MCP spec — tools are statically declared; no sync mechanism with CLI source of truth |
| ~~[§48](04-critical-output-and-parsing/02-critical-output-format.md)~~ | ~~Structured Output Envelope Absence~~ | RA | **MERGED into [§2](04-critical-output-and-parsing/02-critical-output-format.md)** — the envelope spec is the solution to output format & parseability |

#### §49–58: Extended research (CI/CD guides, POSIX docs, agent SDK discussions)

| # | Challenge | Source | Notes |
|---|-----------|--------|-------|
| [§49](01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md) | Async Job / Polling Protocol Absence | TD+FP | Async job patterns documented in CI/CD and deployment tool design; exit-code contract for "still running" is first-principles inference |
| [§50](01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) | Stdin Consumption Deadlock | TD+FP | stdin-as-default-input is a known Unix pattern; non-TTY deadlock is structurally guaranteed |
| [§51](01-critical-ecosystem-runtime-agent-specific/51-high-glob-expansion.md) | Shell Word Splitting and Glob Expansion | TD+FP | Word splitting and globbing are documented POSIX shell behaviors; agent-constructed string vulnerability is first-principles inference |
| [§52](01-critical-ecosystem-runtime-agent-specific/52-medium-command-tree-discovery.md) | Recursive Command Tree Discovery Cost | TD+FP | N+1 help calls documented in agent tool-use discussions; context window cost is first-principles inference |
| [§53](01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md) | Credential Expiry Mid-Session | TD+FP | Token expiry in long-running automation documented in AWS and OAuth guides; expiry-vs-denied ambiguity absorbed from authentication troubleshooting discussions |
| [§54](01-critical-ecosystem-runtime-agent-specific/54-high-conditional-args.md) | Conditional / Dependent Argument Requirements | TD+FP | Conditional required args is a known argparse/Click design challenge; one-at-a-time discovery cost is first-principles inference |
| [§55](01-critical-ecosystem-runtime-agent-specific/55-high-silent-truncation.md) | Silent Data Truncation | TD | API field length limits silently truncating on write documented in database ORM discussions and API client library issue trackers |
| [§56](01-critical-ecosystem-runtime-agent-specific/56-high-pipeline-exit-masking.md) | Exit Code Masking in Shell Pipelines | TD+FP | `pipefail` is documented POSIX/bash behavior; agent consequence is first-principles inference |
| [§57](01-critical-ecosystem-runtime-agent-specific/57-medium-locale-errors.md) | Locale-Dependent Error Messages | TD | `LC_MESSAGES=C` for English error normalization is documented in server administration guides; agent impact absorbed from internationalization discussions |
| [§58](01-critical-ecosystem-runtime-agent-specific/58-high-multiagent-conflict.md) | Multi-Agent Concurrent Invocation Conflict | TD+FP | Multi-agent concurrency (2024–2025); file locking for config writes is a documented Unix pattern; agent-specific framing is first-principles inference |

#### §59–68: Gemini AMI framework & Antigravity-cli manifesto

Discovered by reviewing two external agent-native CLI projects.

| # | Challenge | Source | Primary Artifact |
|---|-----------|--------|-----------------|
| [§59](01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md) | High-Entropy String Token Poisoning | RA | Gemini AMI: Output & Context — High-Entropy Masking section |
| [§60](01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) | OS Output Buffer Deadlock | RA | Antigravity: I/O & Formatting — Output Buffering; `PYTHONUNBUFFERED` pattern documented explicitly |
| [§61](01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) | Bidirectional Pipe Payload Deadlock | RA | Antigravity: I/O & Formatting — Pipe Deadlocks; 64 KB UNIX pipe buffer limit with exact mechanics |
| [§62](01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md) | $EDITOR and $VISUAL Trap | RA | Gemini AMI: Execution Flow — REPL/Editor Blocks; Antigravity: Interactivity & Prompts — $EDITOR Trap |
| [§63](01-critical-ecosystem-runtime-agent-specific/63-medium-column-width-corruption.md) | Terminal Column Width Output Corruption | RA | Antigravity: I/O & Formatting — Terminal Wrapping; `--width=0` solution described explicitly |
| [§64](01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md) | Headless Display and GUI Launch Blocking | RA | Gemini AMI: System Physics — Headless Display; Antigravity: Environment & Execution — Implicit Browser Fallbacks |
| [§65](01-critical-ecosystem-runtime-agent-specific/65-high-global-config-contamination.md) | Global Configuration State Contamination | RA | Antigravity: State & Concurrency — Global Configuration State Mutation; default-to-local pattern |
| [§66](01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md) | Symlink Loop and Recursive Traversal Exhaustion | RA | Antigravity: Environment & Execution — Symlink Death Spirals; inode tracking solution |
| [§67](01-critical-ecosystem-runtime-agent-specific/67-high-json5-input.md) | Agent-Generated Input Syntax Rejection | RA | Antigravity: Schema & Discoverability — Input Syntax Rigidity; JSON5 forgiving parser solution; REQ-48 |
| [§68](01-critical-ecosystem-runtime-agent-specific/68-high-stdout-pollution.md) | Third-Party Library Stdout Pollution | RA | Gemini AMI: Output & Context; Antigravity: I/O & Formatting — fd-level interception solution |
| [§69](01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) | Argument Order Ambiguity | FP | Derived from parser mode differences across argparse/Click/Cobra/Commander.js |
| [§70](01-critical-ecosystem-runtime-agent-specific/70-high-single-argument-arity.md) | Single-Argument Arity Forcing Agent Loop Overhead | FP | Derived from observed agent error: `ws delete` passed multiple paths, argparse rejected extras; UNIX convention (rm/cp/mv accept nargs=+) creates universal agent expectation |

---

## Confidence Summary

| Confidence | Count | Challenges |
|------------|-------|------------|
| **Very High** (TD+FP or RA+FP) | 30 | §1–5, §7–8, §10–14, §16, §18, §21, §23–24, §29, §34–35, §37, §45, §49–54, §56, §58 |
| **High** (RA only) | 18 | §38, §40–44, §46–47, §59–68 |
| **Medium** (TD only) | 17 | §6, §9, §15, §17, §19–20, §22, §25–28, §30–33, §55, §57 |

> **Active total: 65** (3 merged: §36→§10, §39→§3, §48→§2). RA+FP challenges (§34–35, §37, §45) counted as Very High.

---

## What This Means for Prioritization

**Highest confidence → implement first:**
- TD+FP challenges are both empirically attested AND structurally necessary. They will definitely occur in any agent using CLI tools.

**Research-backed (RA) challenges are specific and concrete:**
- These were confirmed by reading real code and docs. They're real but may not affect every tool — they depend on specific library choices (Commander.js, Python Fire, etc.).

**TD-only challenges need validation:**
- These are plausible based on patterns seen in training data but should be validated against your actual tooling before investing heavily in framework mitigations.

---

## What Is NOT a Source

- **Direct runtime experience**: these challenges were not discovered by actually running agents against CLI tools. There is no personal debugging history behind them.
- **User studies or empirical measurement**: no user studies, no telemetry, no measured frequency data. The "Very Common / Common / Situational" frequency ratings are estimates based on how often similar problems appear in training data — not measured rates.

---

*Written 2026-03-13. Revised 2026-03-13: §36, §39, §48 marked merged; confidence counts corrected to 30/18/17; personal paths removed; active links added. Revised 2026-03-19: §69 added. Revised 2026-03-26: §70 added. Revised 2026-05-07: §71 (FP), §72 (FP), §73 (FP) added; active total updated to 70. Revised 2026-05-07: §74 (FP) added; active total updated to 71. Covers CLI Agent Spec v1.6 — 71 active challenges (74 original, 3 merged).*
