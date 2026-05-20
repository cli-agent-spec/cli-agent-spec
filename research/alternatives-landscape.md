# Alternative Solutions Landscape

> A comprehensive comparison of existing approaches to the agent-CLI integration problem, evaluated against the 67 failure modes in this specification.

Researched March 2026.

---

## Overview

No single existing solution addresses the full scope of the agent-CLI integration problem. The landscape fragments into four distinct layers:

| Layer | What it addresses | Representative solutions |
|---|---|---|
| Protocol | How agents and tool servers communicate | MCP, HTTP function calling |
| Framework | How CLI argument parsing and output are structured | Click, Cobra, Clap, Typer |
| Wrapper | How existing CLI tools are made machine-readable post-hoc | jc, jq, Nushell, PowerShell |
| Convention | Informal checklists for CLI authors | better-cli, DEV Community guides |

CLI Agent Spec occupies a fifth layer — **behavioral contract specification** — that none of these approaches formally addresses.

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

---

## 7. Universal Gaps

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

### Benchmark data

| Source | URL | Relevance |
|---|---|---|
| "CLI is the new MCP" benchmark data (2026) | *(multiple blog posts; no single canonical source)* | 35× token efficiency, 33% task completion rate comparisons |
| Lambda AI — Tool-Calling Token Distillation (May 2026) | https://lambda.ai/blog/creating-highly-efficient-agents-450m-tool-calling-tokens-distilled-for-post-training-from-top-open-source-models | 450M-token Hermes Agent harness dataset; 20 turns/sample, 10–15 tools/turn — scale evidence for agent-tool interaction volume |
| MCP GitHub server token analysis | *(derived from tools/list inspection of `github/github-mcp-server`)* | 93 tools = ~55,000 tokens at init |
