# Ecosystem Runtime Agent Specific

> Agent-specific patterns discovered from real frameworks, libraries, and multi-agent deployments.

**Failure modes:** 37 active · 3 merged elsewhere &nbsp;|&nbsp; 🔴 12 critical · 🟠 21 high · 🟡 4 medium

---

| File | Severity | Summary |
|------|----------|---------|
| [34-critical-shell-injection.md](34-critical-shell-injection.md) | 🔴 Critical | When an AI agent constructs CLI invocations — either as shell strings or by assembling argument arrays from LLM-gener... |
| [37-critical-repl-triggering.md](37-critical-repl-triggering.md) | 🔴 Critical | Some CLI tools expose a REPL (Read-Eval-Print Loop) or interactive shell mode — either as an explicit subcommand (`my... |
| [42-critical-debug-secret-leakage.md](42-critical-debug-secret-leakage.md) | 🔴 Critical | CLI frameworks often provide debug/trace modes that dump full invocation context to aid debugging |
| [43-critical-output-size-unboundedness.md](43-critical-output-size-unboundedness.md) | 🔴 Critical | Challenge #5 (Pagination & Large Output) addresses paginated *list* commands that return many items |
| [45-critical-headless-auth.md](45-critical-headless-auth.md) | 🔴 Critical | Many modern CLI tools implement authentication via OAuth flows that require a browser — typically an OAuth authorizat... |
| [50-critical-stdin-deadlock.md](50-critical-stdin-deadlock.md) | 🔴 Critical | Distinct from §10 (interactive prompts), some CLI tools silently read from stdin as a default fallback — not as a del... |
| [53-critical-credential-expiry.md](53-critical-credential-expiry.md) | 🔴 Critical | Agents often operate over sessions longer than credential lifetimes |
| [60-critical-output-buffer-deadlock.md](60-critical-output-buffer-deadlock.md) | 🔴 Critical | When a CLI tool's stdout is connected to a pipe rather than a TTY, the OS switches from line-buffered to fully-buffer... |
| [61-critical-pipe-payload-deadlock.md](61-critical-pipe-payload-deadlock.md) | 🔴 Critical | UNIX pipes have a finite kernel buffer (typically 64KB on Linux) |
| [62-critical-editor-trap.md](62-critical-editor-trap.md) | 🔴 Critical | Distinct from §37 (REPL triggering), many CLI tools invoke the user's `$EDITOR` or `$VISUAL` environment variable to ... |
| [64-critical-headless-gui.md](64-critical-headless-gui.md) | 🔴 Critical | Distinct from §45 (OAuth browser flow), many CLI tools launch GUI applications for operations unrelated to authentica... |
| [71-critical-noninteractive-installation.md](71-critical-noninteractive-installation.md) | 🔴 Critical | Agents operating in fresh environments must install the CLI before use; interactive install steps (license prompts, w... |
| [35-high-hallucination-inputs.md](35-high-hallucination-inputs.md) | 🟠 High | AI agents make systematically different input errors than human operators |
| [38-high-dependency-version-mismatch.md](38-high-dependency-version-mismatch.md) | 🟠 High | CLI tools written in interpreted languages (Python, Node |
| [40-high-async-race-condition.md](40-high-async-race-condition.md) | 🟠 High | Commander |
| [41-high-update-notifier.md](41-high-update-notifier.md) | 🟠 High | Many widely-deployed CLI tools (particularly in the npm/Commander |
| [46-high-api-translation-loss.md](46-high-api-translation-loss.md) | 🟠 High | CLI tools that wrap HTTP APIs (the majority of developer-facing CLIs) suffer from "translation loss" — the API's nati... |
| [47-high-mcp-schema-staleness.md](47-high-mcp-schema-staleness.md) | 🟠 High | The MCP-wrapped CLI pattern is the most effective approach for making legacy CLIs agent-compatible: wrap an existing ... |
| [49-high-async-job-polling.md](49-high-async-job-polling.md) | 🟠 High | Many CLI operations are inherently asynchronous — deployments, builds, data migrations, batch exports |
| [51-high-glob-expansion.md](51-high-glob-expansion.md) | 🟠 High | When agents construct CLI invocations as shell strings and pass them to a shell executor, the shell performs word spl... |
| [54-high-conditional-args.md](54-high-conditional-args.md) | 🟠 High | Many commands have arguments only required when another argument takes a specific value: `--auth-type oauth` requires... |
| [55-high-silent-truncation.md](55-high-silent-truncation.md) | 🟠 High | CLI tools that write to remote APIs often silently truncate field values that exceed API limits: descriptions > 255 c... |
| [56-high-pipeline-exit-masking.md](56-high-pipeline-exit-masking.md) | 🟠 High | When a CLI tool is used in a shell pipeline (`tool | jq ' |
| [58-high-multiagent-conflict.md](58-high-multiagent-conflict.md) | 🟠 High | Distinct from §15 (race conditions within a single invocation), this is about multiple independent agent instances in... |
| [59-high-high-entropy-tokens.md](59-high-high-entropy-tokens.md) | 🟠 High | JWTs, API keys, UUIDs, base64 blobs, and cryptographic hashes in tool output consume hundreds of LLM tokens each — ye... |
| [65-high-global-config-contamination.md](65-high-global-config-contamination.md) | 🟠 High | Distinct from §28 (config file shadowing on READ), this challenge is about tools that WRITE to global configuration f... |
| [66-high-symlink-loop.md](66-high-symlink-loop.md) | 🟠 High | When a CLI tool performs recursive directory traversal (copy, delete, archive, search) and encounters a circular syml... |
| [67-high-json5-input.md](67-high-json5-input.md) | 🟠 High | LLMs frequently generate near-valid structured input that strict parsers reject: JSON with trailing commas, inline co... |
| [68-high-stdout-pollution.md](68-high-stdout-pollution.md) | 🟠 High | Distinct from §3 (command author stream discipline) and §41 (update notifiers), this challenge is about deeply embedd... |
| [69-high-argument-order-ambiguity.md](69-high-argument-order-ambiguity.md) | 🟠 High | CLI parsers differ on whether options may appear after positional arguments or subcommands — agents construct invocations in LLM-natural order, causing silent misparsing or outright rejection |
| [70-high-single-argument-arity.md](70-high-single-argument-arity.md) | 🟠 High | Commands that accept only one positional argument force agents to loop N times for N items — each iteration a separate process launch, auth check, and round trip — instead of one variadic call |
| [72-high-integration-artifact-drift.md](72-high-integration-artifact-drift.md) | 🟠 High | Agent-facing integration artifacts (OpenAPI specs, AGENTS.md, skill files) drift from the CLI binary as it evolves — ... |
| [73-high-documentation-accuracy-drift.md](73-high-documentation-accuracy-drift.md) | 🟠 High | AGENTS.md and agent-facing docs become inaccurate over time — flag names change, commands are removed, env vars rename... |
| [44-medium-knowledge-packaging.md](44-medium-knowledge-packaging.md) | 🟡 Medium | Agents consuming a CLI tool have two information sources: the tool's `--help` text (or `--schema` if available) and a... |
| [52-medium-command-tree-discovery.md](52-medium-command-tree-discovery.md) | 🟡 Medium | Most CLIs require N+1 help calls to discover the full command surface: one call to list top-level subcommands, then o... |
| [57-medium-locale-errors.md](57-medium-locale-errors.md) | 🟡 Medium | Distinct from §2 (locale-invariant serialization of numbers/dates), many CLI tools embed raw OS or runtime error mess... |
| [63-medium-column-width-corruption.md](63-medium-column-width-corruption.md) | 🟡 Medium | Tools that format output based on terminal width (`$COLUMNS`, `shutil |

---

**Merged (redirect stubs):**

- [36-critical-pager-blocking.md](36-critical-pager-blocking.md) → consolidated into [§10 interactivity](../02-critical-execution-and-reliability/10-critical-interactivity.md)
- [39-high-help-to-stdout.md](39-high-help-to-stdout.md) → consolidated into [§3 stderr-stdout](../04-critical-output-and-parsing/03-high-stderr-stdout.md)
- [48-high-output-envelope.md](48-high-output-envelope.md) → consolidated into [§2 output-format](../04-critical-output-and-parsing/02-critical-output-format.md)

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§34](34-critical-shell-injection.md) | 🔴 Critical | Common | Hard | High | High | Medium |
| [§37](37-critical-repl-triggering.md) | 🔴 Critical | Situational | Hard | High | Critical | Low |
| [§42](42-critical-debug-secret-leakage.md) | 🔴 Critical | Situational | Hard | Low | Low | High |
| [§43](43-critical-output-size-unboundedness.md) | 🔴 Critical | Common | Hard | Critical | High | Critical |
| [§45](45-critical-headless-auth.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§50](50-critical-stdin-deadlock.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§53](53-critical-credential-expiry.md) | 🔴 Critical | Common | Hard | High | High | Low |
| [§60](60-critical-output-buffer-deadlock.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§61](61-critical-pipe-payload-deadlock.md) | 🔴 Critical | Situational | Hard | High | Critical | Low |
| [§62](62-critical-editor-trap.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§64](64-critical-headless-gui.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§35](35-high-hallucination-inputs.md) | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§38](38-high-dependency-version-mismatch.md) | 🟠 High | Common | Medium | High | High | Low |
| [§40](40-high-async-race-condition.md) | 🟠 High | Common (Node.js ecosystem) | Hard | High | High | Low |
| [§41](41-high-update-notifier.md) | 🟠 High | Common (Node.js/npm ecosystem) | Medium | Medium | Medium | Medium |
| [§46](46-high-api-translation-loss.md) | 🟠 High | Common | Medium | High | Medium | Medium |
| [§47](47-high-mcp-schema-staleness.md) | 🟠 High | Common | Hard | High | High | Low |
| [§49](49-high-async-job-polling.md) | 🟠 High | Common | Hard | High | High | Medium |
| [§51](51-high-glob-expansion.md) | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§54](54-high-conditional-args.md) | 🟠 High | Common | Hard | High | Medium | Low |
| [§55](55-high-silent-truncation.md) | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§56](56-high-pipeline-exit-masking.md) | 🟠 High | Common | Hard | Medium | Low | Low |
| [§58](58-high-multiagent-conflict.md) | 🟠 High | Situational | Hard | Medium | High | Low |
| [§59](59-high-high-entropy-tokens.md) | 🟠 High | Common | Medium | High | Low | High |
| [§65](65-high-global-config-contamination.md) | 🟠 High | Common | Hard | Medium | High | Low |
| [§66](66-high-symlink-loop.md) | 🟠 High | Situational | Hard | Medium | Critical | Low |
| [§67](67-high-json5-input.md) | 🟠 High | Common | Easy | High | Medium | Low |
| [§68](68-high-stdout-pollution.md) | 🟠 High | Common | Medium | Medium | Low | High |
| [§69](69-high-argument-order-ambiguity.md) | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§70](70-high-single-argument-arity.md) | 🟠 High | Common | Easy | Medium | Medium | Low |
| [§71](71-critical-noninteractive-installation.md) | 🔴 Critical | Common | Easy | Low | Critical | Low |
| [§72](72-high-integration-artifact-drift.md) | 🟠 High | Common | Medium | High | Medium | Low |
| [§73](73-high-documentation-accuracy-drift.md) | 🟠 High | Common | Hard | High | Medium | Low |
| [§44](44-medium-knowledge-packaging.md) | 🟡 Medium | Very Common | Easy | High | High | Medium |
| [§52](52-medium-command-tree-discovery.md) | 🟡 Medium | Very Common | Easy | High | Medium | High |
| [§57](57-medium-locale-errors.md) | 🟡 Medium | Situational | Easy | High | Low | Medium |
| [§63](63-medium-column-width-corruption.md) | 🟡 Medium | Common | Easy | Medium | Low | Medium |
