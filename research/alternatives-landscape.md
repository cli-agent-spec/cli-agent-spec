# Alternative Solutions Landscape

> A comprehensive comparison of existing approaches to the agent-CLI integration problem, evaluated against the 73 failure modes in this specification.

Researched March 2026.

---

## Overview

No single existing solution addresses the full scope of the agent-CLI integration problem. The landscape fragments into six distinct layers:

| Layer | What it addresses | Representative solutions |
|---|---|---|
| Protocol | How agents and tool servers communicate | MCP, HTTP function calling |
| Framework | How CLI argument parsing and output are structured | Click, Cobra, Clap, Typer |
| Wrapper | How existing CLI tools are made machine-readable post-hoc | jc, jq, Nushell, PowerShell |
| Convention | Informal checklists for CLI authors | better-cli, DEV Community guides |
| Audit | Post-hoc reliability classification of production agent traces | EvidenceRun |
| Optimization | How agents adaptively learn to use existing CLIs | SkillOpt |

CLI Agent Spec occupies a seventh layer — **behavioral contract specification** — that none of these approaches formally addresses.

---

## 1. Model Context Protocol (MCP)

### What it is

MCP is a JSON-RPC 2.0 protocol (originally by Anthropic, donated to the Linux Foundation's Agentic AI Foundation in December 2025, adopted by OpenAI in March 2025) for connecting AI agents to external tools and data. An MCP server exposes *tools* (executable functions), *resources* (data), and *prompts* (templates) over STDIO or HTTP+SSE. Agents discover tools via `tools/list` and invoke them via `tools/call`. Every response is a typed JSON object.

### Coverage

**57.7%** across 65 failure modes (25 native ✓, 25 partial ~, 15 missing ✗) — highest score of any evaluated solution.

Challenges MCP resolves natively:

| Challenge | How MCP addresses it |
|---|---|
| §2 Output format | Every tool response is a typed JSON-RPC object — no text to parse |
| §8 ANSI/color leakage | Structurally impossible — responses are JSON, not terminal output |
| §9 Binary encoding | Binary blobs are base64 in typed content objects |
| §21 Schema discoverability | `tools/list` returns full JSON Schema for every tool |
| §26 Session management | Explicit session lifecycle defined in the protocol |
| §24 Authentication | Isolated to the transport layer, separate from tool logic |
| §37 REPL triggering | Impossible by protocol design |
| §57 Locale-dependent errors | JSON-RPC error objects are structured, not locale-formatted strings |

Challenges MCP misses entirely:

| Challenge | Why MCP cannot address it |
|---|---|
| §1 Exit code taxonomy | MCP replaces exit codes with `isError: true` — the 14-code taxonomy with `retryable` and `retry_after_ms` has no equivalent |
| §11 Timeout enforcement | Spec recommends timeouts; enforcement is left to client implementations |
| §12 Idempotency | `idempotentHint` is advisory only — not enforced or machine-checkable |
| §13 Partial failure / step manifests | No standard for multi-step operations, rollback, or completed/failed/skipped reporting |
| §19 Retry hints | No first-class `retryable`/`retry_after_ms` fields |
| §22 Schema versioning per response | Protocol versioning covers the whole protocol, not individual tool schema versions |
| §47 MCP wrapper schema staleness | When a wrapped CLI evolves, the hand-written MCP wrapper silently falls out of sync — no mechanism exists for this in any solution |

### Token cost

A typical CLI interaction costs ~200 tokens. A popular GitHub MCP server with 93 tools consumes ~55,000 tokens before a single call — a 275× overhead. Well-designed hierarchical MCP servers that expose a short index at init and return full schemas on demand close this gap significantly. Benchmarks from early 2026 show 33% worse task completion rates for naive MCP vs direct CLI approaches in inner-loop agent tasks; this reflects poor server design more than inherent protocol limitations.

Beyond token overhead, every MCP wrapper introduces an *abstraction tax* — a structural fidelity loss from the layer between agent and underlying tool. Constrained tool definitions sacrifice expressiveness; full-surface definitions consume prohibitive context. See the Poehnelt "MCP Abstraction Tax" analysis in §6 for the fidelity spectrum and its implications.

### What it requires of tool authors

Authors must implement a full JSON-RPC server: define JSON Schema for every tool, handle the MCP lifecycle (`initialize`, `tools/list`, `tools/call`, shutdown), and ship either a STDIO binary or HTTP service. SDKs exist for Python, TypeScript, Go, Java, and Kotlin. For an existing CLI tool, this means building and maintaining a separate server layer — the CLI itself does not become MCP-native without a wrapper.

### Relationship to this spec

**Complementary — different integration layers.** MCP defines the agent↔server protocol; this spec defines the subprocess behavioral contract. A CLI built to this spec is trivially wrappable in MCP (the manifest provides the JSON Schema, the response envelope maps directly to tool results, the exit code taxonomy maps to `isError`). A raw CLI requires bespoke wrapper code for each of the 67 failure modes. The two approaches are not in competition — they address sequential layers of the same stack.

---

## 2. OpenAPI for CLIs

### What it is

OpenAPI is a specification for HTTP APIs. Its application to CLIs takes two forms:

- **CLI → OpenAPI:** tools like the AWS CLI and Azure CLI expose `--output json` / `-o json` flags and generate OpenAPI-style schema documentation from their command trees
- **OpenAPI → CLI:** tools like `openapi-generator` produce CLI clients from an OpenAPI spec

### Coverage

**41.5%** across 65 failure modes (16 native ✓, 22 partial ~, 27 missing ✗) — tied with Cobra.

### Documented limitations of real implementations

| Tool | Limitation |
|---|---|
| Azure CLI | Some subcommands (e.g. `az aks command`) do not honour `--output json` |
| Azure CLI | `az --version` cannot produce JSON output (open issue) |
| AWS CLI | JSON skeleton format is not stable between CLI versions |
| AWS CLI | `aws s3 ls` returns text regardless of `--output` setting |
| Both | Exit code 0 returned for many error conditions even in JSON mode |

### Gaps

OpenAPI defines HTTP status codes (200, 400, 404, 429), which overlap partially with the exit code taxonomy but are separate — CLI exit codes have no standard OpenAPI representation. OpenAPI says nothing about interactive prompts, child process management, unbounded output, or any of the process-level behavioral contracts. Schema versioning covers the whole API, not individual response schemas per invocation.

### Relationship to this spec

**Complementary for HTTP-API-backed CLIs; limited for native subprocess CLIs.** OpenAPI is the right tool for CLIs that are generated from or backed by HTTP APIs. For CLIs that are native subprocesses, OpenAPI does not address the behavioral layer this spec targets.

---

## 3. CLI Frameworks

### Click (Python) — 23.8%

Click provides TTY detection (`click.isatty()`), color stripping, and confirm prompts. It does not natively enforce structured output, exit code taxonomy, retry hints, idempotency, pagination, or tool manifests.

**Key agent hazard:** `click.echo()` does not distinguish data from diagnostics — both go to stdout by default. JSON output mixed with progress messages is a common agent parsing failure.

### Typer (Python) — 19.2%

Built on Click; inherits its limitations and ranks below Click. `typer.prompt()` blocks indefinitely on non-TTY stdin — exactly the scenario agents operate in.

**Agentyper** (0.1.4, alpha): wraps Typer with `--yes`/`--answers` flags, `isatty()` detection, and structured output. Scores 29.2% — 10 points higher than Typer, demonstrating that the agent-friendly layer is implementable but requires deliberate work.

### Cobra (Go) — 41.5%

Used by Kubernetes, Docker, `gh`, Hugo. Go's type system provides UTF-8 safety and buffer/pipe deadlock immunity. `context.WithTimeout` integration is native. However, Cobra provides no JSON output primitive — every `--output json` flag in every Cobra-based tool is individually authored by the tool's maintainers. No framework-level primitives for exit code taxonomy, retry hints, idempotency, pagination, or tool manifests.

**Notable example:** The GitHub CLI (`gh`) built JSON output on top of Cobra with field selection (`gh pr list --json number,title,state`). This is strong practice, but it is the GitHub team's design — Cobra enforces nothing.

### Clap (Rust) — 43.1%

Highest score among parser frameworks. Rust's type system provides structural solutions for encoding safety (UTF-8 invariant), buffer deadlocks (async I/O safety), and locale issues (no locale-dependent formatting). The Rust CLI book explicitly recommends line-delimited JSON and `IsTerminal` detection for machine communication. `OutputFormat` enums with JSON/YAML/TOML variants compose naturally with `serde_json`.

**Gaps:** Same as Cobra — no framework-level primitives for exit code taxonomy, retry hints, idempotency, pagination, or tool manifests.

### Summary

No major CLI framework has adopted structured JSON output, a defined exit code taxonomy, or agent-specific behavioral contracts as framework-level primitives. All require the application author to implement these manually per command. CLI Agent Spec specifies what that manual implementation must produce.

---

## 4. Function Calling Standards

### OpenAI function calling / Anthropic tool use / Google Vertex AI

All three converge on the same pattern: the model receives JSON Schema definitions for available tools, outputs a structured call request, and the host executes it and returns the result. The standards define:

- **Input:** JSON Schema for parameters (name, type, description, required)
- **Output:** Structured JSON returned to the model
- **Error:** A boolean flag or error object alongside the result

**None of these standards define how the underlying tool should behave.** They define the interface between the model and the host application. How the host calls a CLI subprocess, handles exit codes, parses output, or manages timeouts is entirely outside their scope. A CLI wrapped as a function call inherits all 67 failure modes — the wrapper code must handle them individually, which is what this spec eliminates.

### MCP tool annotations (2025-11-25 spec)

The 2025-11-25 MCP spec added `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` — the only function-calling-adjacent standard addressing behavioral contracts. They are advisory only: the protocol does not enforce them, and they cover neither retry semantics, timeouts, partial failure, nor the full exit code taxonomy.

### Relationship to this spec

**Parallel — different interface boundaries.** Function calling standards address the model↔host boundary. This spec addresses the host↔subprocess boundary. Both are necessary; neither substitutes for the other.

---

## 5. Shell and Terminal Integration

### jc (JSON Convert)

Wraps ~100 standard Unix tools (`ls`, `ps`, `df`, `ifconfig`, etc.) with hardcoded text-to-JSON parsers. Practical workaround for specific tools; breaks when tools change their output format. Does not address exit codes, interactive prompts, retryability, or any behavioral contracts.

### jq

A JSON stream processor. Useful for consuming structured output from CLIs that already emit JSON; a workaround for CLIs that embed structured data in human-formatted text. Does nothing about exit codes, prompts, or unbounded output.

### Nushell

A shell that treats all data as structured objects rather than text streams (analogous to PowerShell's object pipeline). Commands pass typed tables and records through pipes. Nushell 0.108.0 (October 2025) added an optional MCP server.

**Key limitation:** Nushell's structure exists within the shell's pipeline — the CLI tools themselves do not change. When an agent calls `ls` through Nushell, Nushell parses `ls`'s text output into structured data using built-in parsers. The underlying CLI still has ambiguous exit codes, can prompt interactively, and can emit unbounded output. Agents that operate outside a Nushell environment (which is most agents) receive no benefit.

### PowerShell

Mature object pipeline with typed .NET objects. Excellent for PowerShell-native automation. Most CLI tools are not PowerShell cmdlets; most CI/CD and server environments run Linux; most agents trained on Unix idioms generate Bash patterns that fail in PowerShell. Does not address the broader ecosystem of Python/Go/Rust/Node subprocess CLIs.

---

## 6. Competing Specifications and Proposals

### "Rewrite Your CLI for AI Agents" — Justin Poehnelt

**Source:** [justin.poehnelt.com/posts/rewrite-your-cli-for-ai-agents](https://justin.poehnelt.com/posts/rewrite-your-cli-for-ai-agents/) — the primary source for the `jpoehnelt-scale` rubric in the comparison matrix. Reference implementation: [Google Workspace CLI (`gws`)](https://github.com/googleworkspace/cli).

The post frames the design tension as: *"Human DX optimizes for discoverability and forgiveness. Agent DX optimizes for predictability and defense-in-depth."* It proposes seven principles, each mapping directly to challenges in this spec:

| Principle | Spec challenge(s) | What the post adds |
|---|---|---|
| Raw JSON payloads (`--json` passthrough) | §46 API Schema Translation Loss | Eliminates flag translation entirely for API-backed CLIs — accept full API payloads directly |
| Runtime schema introspection (`gws schema <method>`) | §21 Schema Discoverability, §52 Recursive Discovery Cost | Machine-readable dump of method signatures, parameters, response types, and OAuth scopes |
| Context window discipline (field masks, NDJSON) | §4 Verbosity & Token Cost, §5 Pagination, §43 Unbounded Output | Mandatory field masks for API responses; "ALWAYS use field masks to avoid overwhelming your context window" |
| Input hardening against hallucinations | §34 Shell Injection, §35 Agent Hallucination Input Patterns, §59 Token Poisoning | Rejects path traversal (`../`), control characters below `0x20`, embedded `?`/`#` in resource IDs, percent-encoding — framed as: *"The agent is not a trusted operator"* |
| Shipping agent skills (YAML frontmatter + Markdown) | §44 Agent Knowledge Packaging Absence | Documents invariants agents cannot infer from help text: "Always use `--dry-run` for mutating operations" |
| Multi-surface architecture from a single source | §47 MCP Wrapper Schema Staleness | Both CLI and MCP server derived from the same Discovery Document — the only known concrete solution to §47 |
| Safety rails (`--dry-run`, response sanitization) | §23 Destructive Operations, §25 Prompt Injection | Pipes API responses through Google Cloud Model Armor to strip embedded prompt injection before returning to the agent |

**Scope:** The post is scoped to API-backed CLIs (Google Workspace APIs). It does not address exit code taxonomy, retry hints, timeouts, signal handling, partial failure, or any of §38–68 ecosystem/runtime challenges. The security framing ("agent is not a trusted operator") and the multi-surface / single-source-of-truth architecture are the two ideas with the widest applicability beyond API-backed tools.

**On §47 specifically:** The comparison matrix marks §47 (MCP Wrapper Schema Staleness) as universally unsolved. Poehnelt's approach — generating both the CLI command tree and the MCP tool definitions from a single upstream API Discovery Document — is the only known architectural pattern that eliminates drift by construction. This pattern is applicable wherever a CLI wraps a structured API with a machine-readable schema.

### "The MCP Abstraction Tax" — Justin Poehnelt

**Source:** [justin.poehnelt.com/posts/mcp-abstraction-tax](https://justin.poehnelt.com/posts/mcp-abstraction-tax/) — a direct follow-up to the "Rewrite Your CLI" post above, examining what MCP wrapping costs even when done correctly.

**Core thesis:** Every protocol layer between an agent and an API loses fidelity — an "abstraction tax." For MCP servers wrapping complex enterprise APIs, the costs compound: "the REST API itself is already an imperfect projection of the underlying data model," and MCP adds another abstraction layer on top.

#### The two-path problem

Developers wrapping an enterprise API (e.g. a CRM) in MCP face a structural dilemma:

| Path | Approach | Cost |
|---|---|---|
| Constrained tools | Expose `create_account`, `update_opportunity` | Lossy — cannot express complex operations like bulk updates with custom field recalculation |
| Full surface | Expose every API method with complete schemas | Theoretically complete, but "would consume a meaningful fraction of an agent's reasoning capacity" through token overhead |

Neither path escapes the abstraction tax. Constrained tools sacrifice fidelity; full-surface tools sacrifice context budget.

#### CLI + Skills as a middle path

The post positions CLI + Skills (on-demand discovery) as a third option: the agent pays "token cost only when relevant" rather than loading all tool schemas upfront. This maps directly to the spec's `tool manifest` design — the manifest is the structured form of what Poehnelt calls "incremental context cost" vs "upfront fidelity loss."

#### Fidelity spectrum

| Approach | Accessibility | Fidelity | Context cost |
|---|---|---|---|
| MCP (constrained) | High | Lower | Low upfront |
| MCP (full surface) | High | High | Prohibitive |
| CLI + Skills | Moderate | High | On-demand |
| Raw API + client libraries | Low | Maximum | Minimal |

These represent different optimization priorities, not competing solutions.

#### Spec challenge mappings

| Post concept | Spec challenge |
|---|---|
| Upfront tool schema token overhead | §4 Context window exhaustion |
| Constrained MCP tools losing expressiveness | §47 MCP wrapper schema staleness |
| On-demand `schema` / `--help` discovery | §52 Recursive discovery cost, §21 Schema discoverability |
| API opaque identifiers, polymorphic fields | §35 Agent hallucination input patterns |
| MCP iterates faster than the underlying API | §47 (schema drift as a symptom of the abstraction tax) |

**Relationship to the "Rewrite Your CLI" post:** The first post advocates for Discovery Documents to minimize §47 drift. This post acknowledges that even a perfectly synced wrapper carries a structural fidelity cost. The two posts form a coherent view: Discovery Documents minimize *drift* but do not eliminate the *abstraction tax* — the fidelity cost is inherent to the wrapping layer, not to tooling quality.

**Relationship to this spec:** The spec's `tool manifest` command (returning the full command tree as machine-readable JSON on demand) is the architectural answer to both concerns: it provides complete fidelity (no constrained-tool expressiveness loss), zero upfront context cost (manifest is loaded only when the agent needs to construct a call), and no wrapper layer (the CLI itself is the tool).

### Other community convergence (2025–2026)

Several independent sources converged on a ~10-rule checklist during 2025–2026:

| Source | Rules covered |
|---|---|
| "Keep the Terminal Relevant" (InfoQ, 2026) | `--json` flag, stdout/stderr separation, exit codes, idempotency, `--yes`/`--force`, TTY detection, schema introspection, NDJSON pagination, plus semantic versioning for output contracts and `--syntax-check` for early validation |
| better-cli / SKILL.md (GitHub: yogin16/better-cli) | 17 rules as an agent-installable skill targeting 40+ agent platforms |

These represent informal community knowledge, not normative specifications. No acceptance criteria, no machine-readable schemas, no tiered contracts, no enforcement mechanism.

### "CLI is the new MCP" narrative (early 2026)

A cluster of blog posts argued that direct CLI invocation is superior to MCP for inner-loop agent tasks:
- 35× better token efficiency in some benchmarks
- 33% better task completion rates in controlled comparisons
- Leverages existing maintained tool investment
- Unix composability preserved

Lambda AI's 450M-token tool-calling distillation dataset (May 2026) provides independent scale evidence: training samples average 20 turns per conversation with 10–15 tool calls per turn, collected via the Hermes Agent harness across 184 H100 GPUs over several days. This volume of agent–tool interaction confirms that tool-calling is not an edge case — it is the dominant inner-loop operation. It also demonstrates that model capability alone does not solve the behavioral contract problem: even a perfectly fine-tuned tool-calling model fails when the CLI it invokes has ambiguous exit codes, interactive prompts, or unstructured output.

The counterpoint (also well-represented): MCP is better for stateful, authenticated, multi-system coordination and cloud-hosted agent deployments. This debate does not produce a competing specification — it produces advocacy for fixing existing CLIs rather than wrapping them in MCP servers.

### AGENTS.md convention

A Markdown file placed in a repository that tells coding agents how to work with that codebase (build steps, test commands, conventions). Used by 60,000+ open-source projects; supported by Codex, Cursor, Gemini CLI, Copilot, and others. Addresses per-project instructions, not CLI behavioral contracts. Does not address exit codes, structured output, prompts, or any process-level guarantees.

### AI Manifest (ai-manifest.org)

A community standard for publishing AI service metadata at `/.well-known/ai.json`, combining OpenAPI schema discovery with JWKS-based cryptographic verification. Addresses service *discovery* — how agents find what tools exist — not the behavioral contracts of those tools after discovery. Complementary.

### AWS CLI Agent Orchestrator (awslabs/cli-agent-orchestrator)

An open-source multi-agent orchestration framework from AWS Labs that wraps Amazon Q CLI and Claude Code as worker agents in a supervisor/worker hierarchy. Orchestrates calls to existing CLIs rather than specifying how CLIs should behave. Does not define exit code standards, structured output envelopes, or tool manifests.

### EgisAI

**Source:** [egisai.co](https://egisai.co/) / [EgisLabs/egisai-sdk](https://github.com/EgisLabs/egisai-sdk) — runtime governance SDK for Python AI applications.

EgisAI intercepts LLM provider calls and tool invocations to enforce PII masking, policy rules, model allowlists, and audit logging before and after each call. One-line integration (`egisai.init()`) with 15+ AI frameworks. Targets engineering and security teams shipping production AI features, not CLI authors.

The SDK operates at the agent → LLM/tool boundary, not the host → subprocess boundary. It addresses adjacent challenges from the agent side:

| EgisAI concern | Spec challenge | Difference |
|---|---|---|
| PII leakage to third-party APIs | §25 Prompt injection, §59 Token poisoning | EgisAI sanitizes agent-side output before dispatch; spec requires CLIs to sanitize their own responses before returning them to the agent |
| Unauthorized tool access | §34 Shell injection | EgisAI restricts which tools agents may call; spec requires tools to reject dangerous inputs at registration |
| Audit trail | §33 Observability & audit trail | EgisAI audits at the agent layer; spec requires `request_id` and JSONL audit logs at the CLI layer |

**Relationship to this spec:** Complementary — agent-side governance vs. CLI-side behavioral contracts. EgisAI governs what the agent is permitted to invoke; this spec governs how CLIs must behave when invoked. Both are necessary in a production agent deployment; neither substitutes for the other.

### EvidenceRun — Agent Reliability Audit Taxonomy

**Source:** [evidencerun.com](https://www.evidencerun.com/) / [Substack: "12 Ways AI Agents Fail in Production"](https://getevidencerun.substack.com/p/12-ways-ai-agents-fail-in-production) (May 2026) — a structured failure taxonomy for production agent behavior, used as the basis for a commercial reliability audit service targeting enterprise-facing agent startups.

#### What it is

A 12-mode taxonomy derived from production incidents, red-team write-ups, and instrumented agent traces across refund bots, coding agents, research agents, sales-prospecting agents, and support copilots. The taxonomy is organized into three severity tiers and delivered as a buyer-ready "Agent Reliability Report" founders can use in investor, security, and enterprise sales conversations.

| Tier | Mode | Description |
|---|---|---|
| Critical | #3 PII exposure | Customer data, secrets, or prompt content leaks to a third-party tool, log, or downstream model |
| Critical | #5 Missing approval | High-impact actions execute without the human-in-the-loop check the workflow promises |
| Critical | #11 Unverifiable decisions | A decision was made; nobody can reconstruct what the agent saw, asked, or weighed |
| Critical | #12 No replay trail | Inputs, prompts, model versions, and tool outputs are not stored long enough for an after-the-fact audit |
| Operational | #1 Tool misuse | Agent calls a tool with the wrong args, wrong scope, or no need to call it at all |
| Operational | #2 Hidden retries | Silent retry loops on non-idempotent calls cause duplicate side effects nobody can see in the trace |
| Operational | #6 Runaway cost | Recursive calls, retry storms, or context bloat send a single run past the alarm threshold |
| Operational | #8 Silent failure | Tool returned an error; the agent returned success — the user is told something happened that didn't |
| Subtle | #4 Prompt injection | Untrusted content in inputs, attachments, or web pages overrides system instructions |
| Subtle | #7 Stale context | Agent acts on cached customer state, expired session data, or out-of-date documents |
| Subtle | #9 Wrong system access | Agent inherits service-account permissions far beyond what the workflow requires |
| Subtle | #10 Output drift | Customer-facing wording, format, or recommendations drift across runs in ways nobody noticed |

#### Mapping to this spec

EvidenceRun's taxonomy operates at the agent behavior layer; this spec operates at the CLI tool design layer. Most of EvidenceRun's 12 modes have root causes that live in CLI behavioral contracts:

| EvidenceRun mode | Spec challenges | Relationship |
|---|---|---|
| #1 Tool misuse | §2 Output format, §21 Schema discoverability, §35 Hallucination input patterns | Exit code taxonomy and arg validation requirements make misuse structurally detectable |
| #2 Hidden retries | §12 Idempotency / safe retries, §19 Retry hints | Near-perfect match: the spec's `retryable`/`side_effects` invariant is the only known design-time mechanism that addresses this mode per exit code |
| #3 PII exposure | §34 Shell injection, §59 Token poisoning | Spec controls structured output boundaries; EgisAI is the closer agent-side enforcement |
| #4 Prompt injection | §25 Prompt injection, §59 Token poisoning | Spec addresses the CLI trust boundary; CLI-side response sanitization (per Poehnelt's Model Armor approach) is the structural fix |
| #5 Missing approval | §23 Destructive operations | `side_effects` field enables agent-side approval gating; spec cannot enforce gating by design — enforcement is the agent's responsibility |
| #6 Runaway cost | §11 Timeout enforcement, §43 Unbounded output | Timeout signals and pagination requirements reduce runaway cost surface |
| #7 Stale context | None | Agent architecture concern; no CLI design addresses read/write time-delta in agent state |
| #8 Silent failure | §1 Exit code taxonomy, §6 Errors (entire part) | **Core value of this spec** — exit codes, structured error envelopes, and non-zero exits on failure are the direct structural fix |
| #9 Wrong system access | §30 Undeclared filesystem side effects, §53 Credential expiry | Manifest declarations enable least-privilege reasoning; IAM enforcement is external |
| #10 Output drift | §22 Schema versioning per response | Versioned `response-envelope` schema and regression scaffolding directly address drift |
| #11 Unverifiable decisions | §33 Observability & audit trail | `request_id`, JSONL audit logs, and structured response envelopes are the spec's contributions |
| #12 No replay trail | §33 Observability & audit trail, §22 Schema versioning | Structured, versioned, deterministic output makes replay possible; the spec provides the format |

10 of EvidenceRun's 12 modes trace directly to CLI behavioral gaps this spec addresses. The two without a CLI fix — #7 (Stale context) and partly #9 (Wrong system access / IAM enforcement) — are genuinely agent-architecture concerns.

#### Compounding and the spec's contribution

EvidenceRun emphasizes that failure modes compound in production: prompt injection (#4) + wrong system access (#9) = an attacker with write access to billing; hidden retries (#2) + silent failure (#8) = three invoices sent, system reports one. The spec's `side_effects` declarations and structured exit codes allow agents to implement defense-in-depth before a call lands — earlier in the stack than any audit can intervene.

#### Relationship to this spec

EvidenceRun is post-hoc audit; this spec is design-time prevention. EvidenceRun instruments one workflow, maps failures to the 12-mode taxonomy, and packages the evidence for enterprise buyers. This spec provides the behavioral contracts that make most of those failures structurally impossible or detectable at call time. A CLI built to this spec would score better on modes #1, #2, #8, #10, #11, and #12 by construction — not because the audit rubric changed, but because the failure mode was eliminated at the source.

**The spec as the substrate that makes EvidenceRun findings fixable:** EvidenceRun's 12 modes are high-level; the spec's 73 failure modes are granular sub-cases. "#1 Tool misuse" in EvidenceRun decomposes into at least 8 §N failure modes in the spec. An EvidenceRun audit tells a team which high-level mode fired. The spec tells CLI authors which specific behavioral contract to implement to prevent it from firing again.

---

## 7. SkillOpt — Text-Space Skill Optimization

**Source:** arXiv:2605.23904 — "SkillOpt: Executive Strategy for Self-Evolving Agent Skills" (Yang et al., Microsoft Research + Shanghai Jiao Tong / Tongji / Fudan universities, May 2026)

### What it is

SkillOpt is the first systematic text-space optimizer for agent skills. Rather than modifying model weights or wrapping CLIs in new protocols, it treats a compact natural-language *skill document* as the trainable state of a frozen agent. A separate optimizer model converts scored execution trajectories into bounded `add`/`delete`/`replace` edits on the skill document; a held-out validation gate accepts an edit only if it strictly improves performance on a disjoint selection split. The deployed output is a single `best_skill.md` file — 300–2,000 tokens, assembled from a median of 2.5 accepted edits across the entire optimization run.

The training loop deliberately mirrors deep-learning optimizer design:

| DL concept | SkillOpt equivalent |
|---|---|
| Mini-batch | Rollout batch of scored trajectories |
| Learning rate | Edit budget `Lₜ` — maximum edits applied per step |
| Validation / early stopping | Held-out selection gate (strict improvement required; ties rejected) |
| Momentum | Epoch-wise slow update in a protected `<!-- SLOW_UPDATE -->` markup region |
| Negative replay buffer | Rejected-edit buffer — failed edits recycled as negative feedback for later steps |

Each component is ablated. Removing bounded edits costs up to 22.5 points on SpreadsheetBench; removing the slow/meta update costs the same. The gains are robust to rollout batch size, reflection minibatch size, and learning-rate schedule — but sensitive to the presence of bounded text-space learning and validation gating.

### What it requires of CLIs

SkillOpt's training loop requires three prerequisites from any CLI it optimizes against:

**1. Automatic verifiers.** The held-out validation gate requires a reliable scalar success signal. Exit codes and output must be machine-interpretable without external oracles. A CLI where "success" requires reading human-formatted text and making a judgment call cannot support automatic validation gating — the optimizer learns from ambiguous signal and produces unstable skills. This maps directly to §1 (Exit Code Taxonomy) and §2 (Output Format).

**2. Deterministic, bounded output.** Non-deterministic output (§7) produces contradictory evidence batches — the optimizer may learn opposite rules from identical underlying behavior. Unbounded output (§43) inflates training cost: SearchQA already costs 213M tokens at 37.9M tokens per test-point gain.

**3. Harness-agnostic behavior.** The cross-harness transfer results show that skills trained in Codex can outperform skills trained natively in Claude Code. A SpreadsheetBench skill trained entirely inside the Codex execution harness transferred to Claude Code with a +59.7 point gain — slightly exceeding the in-domain Claude Code SkillOpt score of 80.4. The transferred rules are workbook-level procedures ("inspect structure before writing", "write evaluated static values, not formula references") — not harness-specific command sequences. CLIs whose correct usage depends on execution-environment conventions (env vars the harness happens to set, TTY state, workspace layout) produce non-transferable knowledge.

### What it can and cannot address

SkillOpt ameliorates *behavioral* failure modes: procedures, output format expectations, error interpretation, search discipline. It cannot address *structural* failure modes, which abort rollouts before any trajectory is logged:

| SkillOpt can learn around | SkillOpt cannot fix |
|---|---|
| §2 Unstructured output — learns format rules from failures | §10 TTY deadlock — rollout never completes |
| §4 Verbose output — optimizer selects compact procedures | §11 Hanging process — rollout exceeds training budget |
| §18 Poor error quality — learns to interpret error patterns | §25 Prompt injection — CLI-side output trust boundary |
| §21 Schema discoverability — can learn to probe `--help` | §34 Shell injection — CLI input validation issue |
| §44 Missing knowledge packaging — the optimized skill IS the knowledge | §45 Headless auth deadlock — structural TTY block |

This partition maps to a useful design principle: structural failure modes are the prerequisite layer that spec compliance must eliminate before skill optimization becomes effective.

### Key empirical results

Across 6 benchmarks, 7 target models, and 3 execution harnesses (direct chat, Codex CLI, Claude Code), SkillOpt is best or tied-best on all 52 evaluated (model × benchmark × harness) cells. The gains are largest on procedural benchmarks where reusable format and tool-use rules matter most:

| Benchmark | GPT-5.5 no skill | GPT-5.5 SkillOpt | Gain | Accepted edits |
|---|---|---|---|---|
| SpreadsheetBench | 41.8 | 80.7 | +38.9 | 4 |
| OfficeQA | 33.1 | 72.1 | +39.0 | 1 |
| LiveMathBench | 37.6 | 66.9 | +29.3 | 1 |
| DocVQA | 78.8 | 91.2 | +12.4 | 3 |
| SearchQA | 77.7 | 87.3 | +9.6 | 4 |
| ALFWorld | 83.6 | 95.5 | +11.9 | 2 |

The edit economy finding is striking: OfficeQA gains +39.0 points from a single accepted edit. The validation gate rejects the majority of what the optimizer proposes; the deployed skill is the tip of a discarded iceberg.

These results provide the first quantitative measure of the performance gap attributable to missing procedural knowledge (§44): zero-shot frontier models reach 33–42% accuracy on procedural benchmarks; SkillOpt-trained skills reach 67–81%.

### Relationship to this spec

**Complementary — optimization layer above spec.** This spec defines behavioral contracts CLIs must satisfy; SkillOpt is a training method for producing knowledge artifacts that help agents use conformant CLIs correctly. The two address sequential parts of the same problem:

1. A CLI that violates the spec (interactive prompts, ambiguous exit codes, unstructured output) blocks SkillOpt's rollout loop — structural failure modes abort training before any trajectory is logged
2. A CLI that satisfies the spec provides the stable, verifiable behavior that SkillOpt's validation gate requires
3. SkillOpt then discovers the domain-semantic procedures the spec's requirements alone cannot encode: search heuristics, formula-evaluation discipline, answer-format constraints, tool-use sequencing

The spec is the prerequisite; SkillOpt is a consumer of conformant CLIs that produces portable knowledge artifacts from execution evidence. Together they form a complete adaptation stack: spec compliance removes structural blockers; skill optimization discovers reusable procedures; the exported `best_skill.md` deploys across models and harnesses without further training.

**On §44 specifically:** SkillOpt produces exactly the kind of artifact §44 identifies as missing. The spec defines the problem (agents cannot infer domain heuristics from `--help`); SkillOpt provides a training-loop answer. The two are not in competition — the spec defines what the artifact must encode; SkillOpt provides a systematic method for producing it.

---

## 8. Universal Gaps

The following 23 challenges have **zero** native implementations across all 12 evaluated solutions, including MCP. They represent the genuinely novel territory this spec addresses:

| Challenge | Why no solution addresses it |
|---|---|
| §7 Output non-determinism | No framework enforces deterministic field ordering in responses |
| §11 Timeout enforcement | All solutions treat timeouts as advisory; none enforce them at the framework layer |
| §12 Idempotency / safe retries | Advisory hints exist (MCP `idempotentHint`, HTTP PUT convention) but none are enforceable |
| §13 Partial failure / step manifests | No standard for multi-step operation state reporting, rollback, or completed/failed/skipped breakdown |
| §15 Race conditions / concurrency | No framework-level protection against concurrent invocations of non-reentrant commands |
| §16 Signal handling & graceful cancellation | Click/Typer map SIGINT to exit 1 + "Aborted!" but leave SIGTERM unhandled; no framework auto-installs a SIGTERM handler that emits a partial JSON result and exits 143 |
| §17 Child process leakage | No standard requires commands to clean up child processes on timeout or signal |
| §19 Retry hints in error responses | `retryable` and `retry_after_ms` fields are absent from all framework primitives |
| §20 Environment / dependency discovery | No auto-generated `doctor` command convention exists in any framework |
| §22 Schema versioning per response | All versioning covers the whole API/protocol; no solution injects per-response schema version |
| §29 Working directory sensitivity | No framework flags or documents commands that produce different results based on CWD |
| §30 Undeclared filesystem side effects | MCP's `readOnlyHint` is advisory only; no framework provides declarative per-command tracking of files read or written |
| §31 Network proxy unawareness | Go's stdlib HTTP client respects proxy env vars by default (partial); Python's `requests` and Node.js `https` do not auto-read `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` |
| §32 Self-update / auto-upgrade behavior | No standard requires commands to suppress self-update prompts or side effects in automation |
| §33 Observability & audit trail | No framework auto-generates a UUID `request_id` per invocation, injects it into every response, or writes an append-only JSONL audit log |
| §47 MCP wrapper schema staleness | By definition, no solution — including MCP itself — provides a mechanism to detect when a wrapped CLI has evolved away from its wrapper schema |
| §49 Async job / polling protocol absence | No framework provides a standard `job_id` / `status_command` / `cancel_command` contract for long-running operations |
| §53 Credential expiry mid-session | No framework distinguishes "never authenticated" (exit 8), "credentials expired" (exit 10), and "insufficient permissions" (exit 8) with structured `expires_at` and `refresh_command` fields |
| §55 Silent data truncation | No framework emits a structured warning when output exceeds a size threshold |
| §58 Multi-agent concurrent invocation conflict | No framework provides per-instance state namespacing or advisory file locking for config writes to allow parallel agent invocations without conflict |
| §59 High-entropy string token poisoning | No framework sanitizes or flags outputs that could corrupt an agent's context (e.g. injected prompt strings) |
| §66 Symlink loop and recursive traversal exhaustion | No framework tracks visited inodes or enforces traversal depth limits automatically; Go's `filepath.WalkDir` does not follow symlinks (partial) |
| §67 Agent-generated input syntax rejection | No framework accepts JSON5 (trailing commas, comments, unquoted keys) for structured input flags; all require strict JSON that agents frequently violate |

---

## Comparison Summary

| Solution | Challenge coverage | Requires of tool authors | Key gap | vs. this spec |
|---|---|---|---|---|
| MCP | 57.7% | Full JSON-RPC server per tool | Exit code taxonomy, retry hints, step manifests, schema staleness | Complementary — different layer |
| OpenAPI (CLI) | 41.5% | Map every command/flag to schema | Exit codes, prompts, unbounded output | Complementary for HTTP-backed CLIs |
| Clap (Rust) | 43.1% | Author implements all contracts manually | No framework primitives for any agent contract | Complementary — spec defines what to implement |
| Cobra (Go) | 41.5% | Author implements all contracts manually | Same as Clap | Complementary |
| Click (Python) | 23.8% | Author implements all contracts manually | stdout/stderr mixing, no exit code taxonomy | Complementary |
| Typer (Python) | 19.2% | Author implements all contracts manually | `prompt()` blocks on non-TTY | Complementary |
| Function calling (OpenAI/Anthropic/Google) | 0% (different layer) | Write JSON Schema wrapper | Entire subprocess behavioral layer | Parallel — different boundary |
| jc / jq | Parsing workaround only | Nothing | All behavioral contracts | Workaround, not specification |
| Nushell / PowerShell | Parsing workaround only | Nothing for external CLIs | All behavioral contracts; environment dependency | Workaround |
| AGENTS.md | Per-repo instructions only | Write a Markdown file | All process-level contracts | Different scope |
| AI Manifest | Discovery only | Host `/.well-known/ai.json` | All behavioral contracts after discovery | Complementary |
| better-cli | Informal checklist | Write CLI following rules | No enforcement, no schemas, no tiered contracts | Informal predecessor of same problem space |
| EgisAI | 0% (different layer) | Add `egisai.init()` to agent code | CLI behavioral contracts entirely | Complementary — agent-side governance |
| EvidenceRun | N/A (audit taxonomy) | Instrument one agent workflow for tracing | Post-hoc only — no prevention mechanism; no structural enforcement at CLI or protocol layer | Complementary — post-hoc audit taxonomy vs. design-time behavioral contracts |
| SkillOpt | Behavioral failure modes only (structural modes abort rollouts) | CLI with automatic verifiers + deterministic output + harness-agnostic behavior | Cannot fix §10/§11/§25/§34/§45; requires training budget | Complementary — optimization layer above spec |

---

## References

### Primary sources

| Source | URL | Relevance |
|---|---|---|
| Justin Poehnelt — "You Need to Rewrite Your CLI for AI Agents" | https://justin.poehnelt.com/posts/rewrite-your-cli-for-ai-agents/ | Origin of the `jpoehnelt-scale` rubric; 7-principle framework; single-source-of-truth §47 solution |
| Justin Poehnelt — "The MCP Abstraction Tax" | https://justin.poehnelt.com/posts/mcp-abstraction-tax/ | Fidelity spectrum; two-path problem; CLI+Skills as middle path |
| Google Workspace CLI (`gws`) | https://github.com/googleworkspace/cli | Reference implementation of Poehnelt's principles |
| Google API Discovery Service | https://developers.google.com/discovery/v1/reference | Discovery Document format used as single source for CLI + MCP generation |
| Google Cloud Model Armor | https://cloud.google.com/model-armor | Response sanitization implementation for §25 prompt injection |
| Jeremiah Lowin — FastMCP 3.1 "Code Mode" | https://www.jlowin.dev/blog/fastmcp-3-1-code-mode | MCP server design using Skills-style on-demand discovery |

### Specifications and standards

| Source | URL | Relevance |
|---|---|---|
| Model Context Protocol (MCP) specification | https://spec.modelcontextprotocol.io/ | Protocol layer comparison; tool annotations (2025-11-25) |
| MCP GitHub repository (modelcontextprotocol) | https://github.com/modelcontextprotocol | SDK implementations for Python, TypeScript, Go, Java, Kotlin |
| OpenAPI Specification | https://spec.openapis.org/oas/latest.html | HTTP API schema layer; CLI→OpenAPI and OpenAPI→CLI patterns |
| Agent Skills standard (agentskills.io) | https://agentskills.io/ | Cross-agent skill format used by this project's distributable skills |
| AI Manifest standard | https://ai-manifest.org/ | `/.well-known/ai.json` service discovery |

### Frameworks and tools referenced

| Source | URL | Relevance |
|---|---|---|
| Click (Python) | https://click.palletsprojects.com/ | 23.8% coverage; TTY detection, prompt blocking |
| Typer (Python) | https://typer.tiangolo.com/ | 19.2% coverage; Agentyper extension |
| Cobra (Go) | https://cobra.dev/ | 41.5% coverage; used by `gh`, Kubernetes, Docker |
| Clap (Rust) | https://docs.rs/clap/ | 43.1% coverage; highest among parser frameworks |
| jc (JSON Convert) | https://github.com/kellyjonbrazil/jc | Text-to-JSON wrapper for ~100 Unix tools |
| Nushell | https://www.nushell.sh/ | Structured shell pipeline; 0.108.0 added MCP server |
| better-cli | https://github.com/yogin16/better-cli | 17-rule checklist as agent-installable skill |
| AWS CLI agent orchestrator | https://github.com/awslabs/cli-agent-orchestrator | Multi-agent CLI orchestration framework |
| EgisAI SDK | https://github.com/EgisLabs/egisai-sdk | Runtime governance interceptor; agent-side §25/§34/§33 adjacency |
| EvidenceRun | https://www.evidencerun.com/ | 12-mode agent reliability audit taxonomy; post-hoc diagnosis of production agent failures |
| EvidenceRun — "12 Ways AI Agents Fail in Production" | https://getevidencerun.substack.com/p/12-ways-ai-agents-fail-in-production | Primary taxonomy source; mapping between 12 modes and spec §N failure modes |

### Benchmark data

| Source | URL | Relevance |
|---|---|---|
| "CLI is the new MCP" benchmark data (2026) | *(multiple blog posts; no single canonical source)* | 35× token efficiency, 33% task completion rate comparisons |
| Lambda AI — Tool-Calling Token Distillation (May 2026) | https://lambda.ai/blog/creating-highly-efficient-agents-450m-tool-calling-tokens-distilled-for-post-training-from-top-open-source-models | 450M-token Hermes Agent harness dataset; 20 turns/sample, 10–15 tools/turn — scale evidence for agent-tool interaction volume |
| MCP GitHub server token analysis | *(derived from tools/list inspection of `github/github-mcp-server`)* | 93 tools = ~55,000 tokens at init |

### Research papers

| Source | URL | Relevance |
|---|---|---|
| SkillOpt: Executive Strategy for Self-Evolving Agent Skills | https://arxiv.org/abs/2605.23904 | First quantitative measurement of performance gap from missing procedural knowledge (§44); empirical evidence for §2/§4/§18 prerequisites; cross-harness transfer results; 52/52 best-or-tied across model × benchmark × harness |
