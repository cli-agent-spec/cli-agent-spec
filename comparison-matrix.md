# CLI Framework Comparison Matrix

This document compares twelve CLI-related solutions against the 71 agent-compatibility failure modes catalogued in *CLI Agent Spec: Complete Failure Mode Reference* (v1.6). Each cell records how well a solution addresses that failure mode — natively, partially, or not at all. Use this matrix to quickly identify which solutions cover which failure modes, where universal gaps exist, and what a new framework must build from scratch.

How to read: Part 1 is the primary reference table. Parts 2–7 derive analysis from it. The ratings come directly from the per-solution research files; where a research file provided explicit rationale, that rationale is summarised in Part 3.

**Per-solution source files** (evidence and rationale behind each column's ratings):

| Solution | Research file |
|----------|--------------|
| argparse | [`research/argparse.md`](research/argparse.md) |
| typer | [`research/typer.md`](research/typer.md) |
| click | [`research/click.md`](research/click.md) |
| python-fire | [`research/python-fire.md`](research/python-fire.md) |
| pydantic | [`research/pydantic.md`](research/pydantic.md) |
| openapi | [`research/openapi.md`](research/openapi.md) |
| cobra | [`research/cobra.md`](research/cobra.md) |
| clap | [`research/clap.md`](research/clap.md) |
| commander-js | [`research/commander-js.md`](research/commander-js.md) |
| mcp | [`research/mcp.md`](research/mcp.md) |
| agentyper | [`research/agentyper.md`](research/agentyper.md) |
| jpoehnelt-scale | [`research/jpoehnelt-skills.md`](research/jpoehnelt-skills.md) |

---

## Solutions Evaluated

| Name | Type | Language | Version | Maturity |
|------|------|----------|---------|----------|
| argparse | Framework / parser | Python | Ships with CPython (3.13/3.14) | Stable |
| typer | Framework / parser | Python | 0.15.x | Stable |
| click | Framework / parser | Python | 8.1.x | Stable |
| python-fire | Framework / parser | Python | 0.6.0 | Stable (slow-moving) |
| pydantic | Schema / validation library | Python | 2.x | Stable |
| openapi | Specification / protocol | Language-agnostic | 3.1 | Stable (spec) |
| cobra | Framework / parser | Go | 1.8.x | Stable |
| clap | Framework / parser | Rust | 4.5.x | Stable |
| commander-js | Framework / parser | JavaScript / Node.js | 12.x | Stable |
| mcp | Agent protocol | Language-agnostic | 2025-11-25 | Stable (spec) |
| agentyper | Framework / parser | Python | 0.1.4 | Alpha |
| jpoehnelt-scale | Evaluation rubric | Language-agnostic | — | Stable (rubric) |

---

## Rating Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | **Native** — handled automatically, no author effort required |
| ~ | **Partial** — supported but incomplete or requires explicit author work |
| ✗ | **Missing** — not addressed by the solution |

---

## Part 1: Failure Mode Coverage Matrix

Rows are the 71 active failure modes (severity and frequency for priority context). Columns are the twelve solutions. Failure modes §36, §39, and §48 were merged into §10, §3, and §2 respectively and are omitted.

| # | Failure mode | Sev | Freq | argparse | typer | click | python-fire | pydantic | openapi | cobra | clap | commander-js | mcp | agentyper | jpoehnelt-scale |
|---|-----------|-----|------|----------|-------|-------|-------------|----------|---------|-------|------|--------------|-----|-----------|-----------------|
| **Part I: Output & Parsing** |
| 1 | Exit Codes & Status Signaling | Crit | V.Common | ~ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ~ | ~ | ✗ |
| 2 | Output Format & Parseability | Crit | V.Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ✗ | ✗ | ✓ | ~ | ✓ |
| 3 | Stderr vs Stdout Discipline | High | V.Common | ✓ | ~ | ~ | ✗ | ✗ | ✗ | ✓ | ✓ | ~ | ~ | ~ | ✗ |
| 4 | Verbosity & Token Cost | Med | V.Common | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ~ | ~ | ✗ | ~ | ~ | ✓ |
| 5 | Pagination & Large Output | High | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ✗ | ✓ |
| 6 | Command Composition & Piping | Med | Common | ~ | ~ | ~ | ~ | ✗ | ✗ | ~ | ~ | ~ | ✗ | ✗ | ~ |
| 7 | Output Non-Determinism | Med | Common | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ |
| 8 | ANSI & Color Code Leakage | High | Common | ✓ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ✓ | ✗ | ✓ | ~ | ~ |
| 9 | Binary & Encoding Safety | High | Sit. | ~ | ~ | ~ | ✗ | ~ | ~ | ✓ | ✓ | ~ | ✓ | ✗ | ✗ |
| **Part II: Execution & Reliability** |
| 10 | Interactivity & TTY Requirements | Crit | Common | ✓ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✓ | ✗ |
| 11 | Timeouts & Hanging Processes | Crit | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✗ | ✗ |
| 12 | Idempotency & Safe Retries | Crit | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| 13 | Partial Failure & Atomicity | Crit | Common | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 14 | Argument Validation Before Side Effects | High | Common | ✓ | ~ | ✓ | ✗ | ✓ | ~ | ✓ | ✓ | ~ | ~ | ✓ | ~ |
| 15 | Race Conditions & Concurrency | High | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| 16 | Signal Handling & Graceful Cancellation | High | Sit. | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ~ | ✗ | ✗ |
| 17 | Child Process Leakage | Med | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Part III: Errors & Discoverability** |
| 18 | Error Message Quality | High | V.Common | ~ | ~ | ~ | ✗ | ✓ | ~ | ~ | ✓ | ~ | ✓ | ✓ | ~ |
| 19 | Retry Hints in Error Responses | High | V.Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 20 | Environment & Dependency Discovery | Med | Common | ✗ | ✗ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ✗ | ✗ | ✗ |
| 21 | Schema & Help Discoverability | Med | V.Common | ~ | ~ | ~ | ~ | ✓ | ✓ | ~ | ~ | ~ | ✓ | ✓ | ✓ |
| 22 | Schema Versioning & Output Stability | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✗ | ~ | ✗ | ~ |
| **Part IV: Security** |
| 23 | Side Effects & Destructive Operations | Crit | Common | ✗ | ✗ | ~ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ~ | ✗ | ✓ |
| 24 | Authentication & Secret Handling | Crit | Common | ✗ | ✗ | ~ | ✗ | ✓ | ~ | ~ | ~ | ~ | ✓ | ✗ | ~ |
| 25 | Prompt Injection via Output | Crit | Sit. | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✓ |
| 74 | Credential Scope Declaration Absence | Crit | Common | ✗ | ✗ | ✗ | ✗ | ~ | ✓ | ✗ | ✗ | ✗ | ~ | ~ | ~ |
| **Part V: Environment & State** |
| 26 | Stateful Commands & Session Management | High | Common | ✗ | ✗ | ✗ | ~ | ✗ | ~ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| 27 | Platform & Shell Portability | Med | Common | ✓ | ~ | ~ | ~ | ~ | ~ | ✓ | ✓ | ~ | ✓ | ~ | ✗ |
| 28 | Config File Shadowing & Precedence | High | Common | ✗ | ✗ | ~ | ✗ | ✓ | ✗ | ✓ | ~ | ✗ | ✗ | ✗ | ✗ |
| 29 | Working Directory Sensitivity | Med | Common | ✗ | ✗ | ~ | ✗ | ~ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ✗ |
| 30 | Undeclared Filesystem Side Effects | Med | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| 31 | Network Proxy Unawareness | High | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ✗ | ✗ | ✗ |
| 32 | Self-Update & Auto-Upgrade Behavior | High | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| **Part VI: Observability** |
| 33 | Observability & Audit Trail | Med | V.Common | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ~ | ✗ | ✗ |
| **Part VII: Ecosystem, Runtime & Agent-Specific** |
| 34 | Shell Injection via Agent-Constructed Commands | High | Common | ~ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✗ | ✓ |
| 35 | Agent Hallucination Input Patterns | High | Common | ~ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ~ | ~ | ✓ |
| 37 | REPL / Interactive Mode Accidental Triggering | Crit | Sit. | ~ | ✗ | ~ | ✗ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | ~ |
| 38 | Runtime Dependency Version Mismatch | High | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✗ | ✗ | ✗ |
| 40 | parse()/parseAsync() Silent Race Condition | High | Common | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ |
| 41 | Update Notifier Side-Channel Output Pollution | High | Common | ✓ | ~ | ~ | ✗ | ✓ | ✓ | ~ | ~ | ✗ | ✓ | ✓ | ~ |
| 42 | Debug / Trace Mode Secret Leakage | Crit | Sit. | ~ | ~ | ~ | ✗ | ~ | ✓ | ~ | ~ | ~ | ~ | ✓ | ~ |
| 43 | Tool Output Result Size Unboundedness | Crit | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ✓ |
| 44 | Agent Knowledge Packaging Absence | Med | V.Common | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ~ | ✓ |
| 45 | Headless Authentication / OAuth Blocking | Crit | Common | ✗ | ✗ | ~ | ✗ | ✗ | ~ | ~ | ~ | ~ | ✓ | ~ | ✓ |
| 46 | API Schema to CLI Flag Translation Loss | High | Common | ✗ | ~ | ✗ | ~ | ~ | ✗ | ✗ | ~ | ✗ | ✓ | ~ | ~ |
| 47 | MCP Wrapper Schema Staleness | High | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ |
| 49 | Async Job / Polling Protocol Absence | High | Common | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| 50 | Stdin Consumption Deadlock | Crit | Common | ~ | ~ | ~ | ✗ | ✓ | ✓ | ~ | ~ | ~ | ✓ | ~ | ✗ |
| 51 | Shell Word Splitting and Glob Expansion | High | Common | ~ | ~ | ~ | ✗ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ | ~ |
| 52 | Recursive Command Tree Discovery Cost | Med | V.Common | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ~ | ~ |
| 53 | Credential Expiry Mid-Session | Crit | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ |
| 54 | Conditional / Dependent Argument Requirements | High | Common | ~ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ~ | ~ | ✗ |
| 55 | Silent Data Truncation | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 56 | Exit Code Masking in Shell Pipelines | High | Common | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ~ | ~ | ✗ | ✓ | ✗ | ✗ |
| 57 | Locale-Dependent Error Messages | Med | Sit. | ~ | ~ | ~ | ✗ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ | ✗ |
| 58 | Multi-Agent Concurrent Invocation Conflict | High | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ~ | ✗ | ✗ |
| 59 | High-Entropy String Token Poisoning | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 60 | OS Output Buffer Deadlock | Crit | Common | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| 61 | Bidirectional Pipe Payload Deadlock | Crit | Sit. | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ~ | ~ | ✗ | ✓ | ✗ | ✗ |
| 62 | $EDITOR and $VISUAL Trap | Crit | Common | ✓ | ✓ | ~ | ✗ | ✓ | ✓ | ~ | ✓ | ~ | ✓ | ✓ | ~ |
| 63 | Terminal Column Width Output Corruption | Med | Common | ~ | ~ | ~ | ✗ | ✓ | ✓ | ~ | ~ | ~ | ✓ | ~ | ✗ |
| 64 | Headless Display and GUI Launch Blocking | Crit | Common | ✓ | ✓ | ~ | ✗ | ✓ | ✓ | ~ | ~ | ~ | ✓ | ~ | ✓ |
| 65 | Global Configuration State Contamination | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ~ | ~ | ✗ | ~ | ✗ | ✗ |
| 66 | Symlink Loop and Recursive Traversal Exhaustion | High | Sit. | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 67 | Agent-Generated Input Syntax Rejection | High | Common | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ |
| 68 | Third-Party Library Stdout Pollution | High | Common | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ~ | ~ | ✗ | ~ | ✗ | ✗ |
| 69 | Argument Order Ambiguity | High | Common | ~ | ~ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ✓ | ~ | ~ |
| 70 | Single-Argument Arity Restriction | High | Common | ~ | ~ | ~ | ✗ | ~ | ~ | ~ | ~ | ~ | ~ | ~ | ~ |
| 71 | Non-Interactive Installation Absence | Crit | Common | ~ | ~ | ~ | ~ | ✗ | ~ | ✓ | ✓ | ~ | ✗ | ~ | ~ |
| 72 | Integration Artifact Version Drift | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ✓ | ~ | ~ |
| 73 | Documentation Accuracy Drift | High | Common | ✗ | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ✗ | ✗ | ✓ | ~ | ~ |

**Notes:**
- §36, §39, §48 omitted — merged into §10 (Interactivity), §3 (Stderr/Stdout), §2 (Output Format) respectively.
- §40 (parse()/parseAsync() race): Commander.js ✗ as the source of the bug; all other frameworks are immune by design (synchronous or protocol-level).
- §47 (MCP Schema Staleness): All solutions ✗ — no framework provides a CLI-to-MCP schema sync mechanism. MCP itself has no native solution to drift in its own wrappers.
- §60/§61 (Buffer/Pipe Deadlock): Go (cobra) and Rust (clap) are structurally safe; pydantic/openapi not applicable; Python/JS frameworks require explicit mitigation.
- §69 (Argument Order Ambiguity): MCP ✓ — JSON-based invocation has no argument ordering concerns by design. All parser-based frameworks are ~ — mechanisms exist (`parse_intermixed_args`, persistent flags) but are not on by default.
- §70 (Single-Argument Arity): All frameworks ~ except python-fire ✗ — `nargs="+"` is available in every parser but not enforced; python-fire maps Python function signatures and lacks explicit arity declaration support.
- §71 (Non-Interactive Installation): Go (cobra) and Rust (clap) ✓ — static binary releases are naturally non-interactive. MCP ✗ — protocol, does not govern installation. pydantic ✗ — validation library, not a distribution mechanism.
- §72/§73 (Artifact Drift / Documentation Drift): MCP ✓ — tool definitions ARE the integration artifact and documentation, structurally co-versioned. All file-based artifact solutions are ~ at best (code-first generation) or ✗ (no generation capability).
- §74 (Credential Scope Declaration): OpenAPI ✓ — `securitySchemes` and per-operation `security` requirements are native OpenAPI features. MCP ~ — auth layer present at server level but per-tool scope declaration is not yet a built-in primitive.

---

## Part 2: Coverage Scores

Coverage % = (✓ + 0.5 × ~) / 71 × 100, rounded to one decimal place.

| Solution | ✓ Native | ~ Partial | ✗ Missing | Coverage % |
|----------|----------|-----------|-----------|------------|
| mcp | 28 | 27 | 16 | **58.5%** |
| pydantic | 18 | 26 | 27 | **43.7%** |
| openapi | 17 | 27 | 27 | **43.0%** |
| clap | 14 | 32 | 25 | **42.3%** |
| cobra | 11 | 36 | 24 | **40.8%** |
| jpoehnelt-scale | 12 | 20 | 39 | **31.0%** |
| agentyper | 10 | 24 | 37 | **31.0%** |
| argparse | 10 | 19 | 42 | **27.5%** |
| click | 2 | 30 | 39 | **23.9%** |
| commander-js | 1 | 29 | 41 | **21.8%** |
| typer | 3 | 22 | 46 | **19.7%** |
| python-fire | 1 | 8 | 62 | **7.0%** |

**Sorted by Coverage % descending:**

| Rank | Solution | ✓ | ~ | ✗ | Coverage % |
|------|----------|---|---|---|------------|
| 1 | mcp | 28 | 27 | 16 | **58.5%** |
| 2 | pydantic | 18 | 26 | 27 | **43.7%** |
| 3 | openapi | 17 | 27 | 27 | **43.0%** |
| 4 | clap | 14 | 32 | 25 | **42.3%** |
| 5 | cobra | 11 | 36 | 24 | **40.8%** |
| 6 | jpoehnelt-scale | 12 | 20 | 39 | **31.0%** |
| 6 | agentyper | 10 | 24 | 37 | **31.0%** |
| 8 | argparse | 10 | 19 | 42 | **27.5%** |
| 9 | click | 2 | 30 | 39 | **23.9%** |
| 10 | commander-js | 1 | 29 | 41 | **21.8%** |
| 11 | typer | 3 | 22 | 46 | **19.7%** |
| 12 | python-fire | 1 | 8 | 62 | **7.0%** |

**Key observations (v1.7 update — §69–74):**
- **OpenAPI rises to #3** (was tied #4) — earns the only ✓ for §74 (Credential Scope Declaration) via native `securitySchemes` + per-operation `security` declarations.
- **MCP extends to #1 at 58.5%** — earns ✓ for §69 (argument ordering irrelevant in JSON invocation), §72 and §73 (tool definitions are the artifact; drift is structurally impossible), keeping its structural advantage.
- **Cobra and Clap gain ✓ for §71** (static binary releases are non-interactive by construction) but lose ground on §72/§73 (no artifact generation).
- No solution exceeds 59% coverage across 71 failure modes. The space remains wide open.
- **Pydantic jumps to #2** (33% → 45%) because the §34–68 challenges include many where pydantic's type system, SecretStr, and immutable-by-default model behaviour provide structural protection (buffer safety, locale invariance, no stdout output, no subprocess invocation, no GUI operations).
- **MCP extends its lead** (52% → 58%) — protocol-level design protects against most I/O, subprocess, GUI, and locale failure modes structurally.
- **Cobra and Clap gain ground** due to Go/Rust type-system and stdlib advantages in §60/§61/§51/§57/§56.
- **Typer falls to #11** (14% → 19%, but relative rank drops): it acquires ✓ for §62/$EDITOR and §64/headless GUI (never opens either), but has no improvements elsewhere and adds more ✗ rows.
- **Commander.js drops to #10** — inherits the §40 async race condition ✗ and the §41 update-notifier ✗ that afflict the npm ecosystem specifically.
- **jpoehnelt-scale drops from #6 to #6 (tied)** — its evaluation rubric axes were defined for §1–33; the new §34–68 challenges are implementation-specific and mostly outside its rubric scope.

---

## Part 3: Per-Failure-Mode Analysis

### §1. Exit Codes & Status Signaling

- **Best covered by:** None. No solution achieves ✓.
- **Partially covered by:** argparse, typer, click, pydantic, openapi, cobra, clap, commander-js, mcp, agentyper
- **Gap in all solutions:** Yes. All frameworks handle 0 (success) and 2 (usage/parse error) reliably, but none enforce a complete, standard exit code taxonomy covering NOT_FOUND (5), TIMEOUT (7), RATE_LIMITED (9), CONFLICT (6), PERMISSION_DENIED (8), PRECONDITION (4). MCP replaces exit codes with `isError: true` + JSON-RPC error codes, which is structurally different but semantically equivalent.
- **Key insight:** Exit code richness is one of the cheapest wins to implement in a new framework — it costs nothing at runtime but dramatically improves agent retry logic.

---

### §2. Output Format & Parseability

- **Best covered by:** mcp (✓), jpoehnelt-scale (✓)
- **Partially covered by:** pydantic, openapi, cobra, agentyper
- **Gap in all solutions:** Partial. MCP natively returns structured JSON content. jpoehnelt-scale defines the target (Axis 1). All parser frameworks produce no structured output by default; developers must implement it per command.
- **Key insight:** This is the single highest-impact gap for parser frameworks — structured output must be a framework primitive, not a per-command choice.

---

### §3. Stderr vs Stdout Discipline

- **Best covered by:** argparse (✓), cobra (✓), clap (✓)
- **Partially covered by:** typer, click, commander-js, mcp, agentyper
- **Gap in all solutions:** Partial. The three strong performers enforce it by design. MCP uses the protocol boundary (JSON-RPC on stdout, stderr for logging) rather than stream separation. Python frameworks handle error routing but not application-level output discipline.
- **Key insight:** Stream discipline is solvable at the framework level — the solutions that get it right do so through APIs that route stdout and stderr correctly by default.

---

### §4. Verbosity & Token Cost

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** pydantic, cobra, clap, mcp, agentyper
- **Gap in all solutions:** Partial. jpoehnelt-scale defines it precisely in Axis 4 (Context Window Discipline). No implementation framework provides a token-budget-aware verbosity system. Pydantic's `exclude_unset`/`exclude_defaults` is the closest mechanism.
- **Key insight:** Token cost is a genuinely new concern (not in pre-LLM CLI design); no existing framework was built with a context window budget in mind.

---

### §5. Pagination & Large Output

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** openapi, mcp
- **Gap in all solutions:** Yes — in implementations. jpoehnelt-scale defines it; MCP paginates list operations at the protocol level but not individual tool results. No parser framework provides a pagination primitive.
- **Key insight:** Unbounded output is a context-window crisis waiting to happen. Default limits (e.g., 20 items) and `next_cursor` metadata must be built into the framework's list-command abstraction.

---

### §6. Command Composition & Piping

- **Best covered by:** None achieves ✓.
- **Partially covered by:** argparse, typer, click, python-fire, cobra, clap, commander-js, jpoehnelt-scale
- **Gap in all solutions:** Yes. Python-fire's method chaining is the most distinctive composition model; all parser frameworks support basic stdin/stdout piping via the OS but provide no structured pipe protocol. MCP explicitly lacks composition primitives.
- **Key insight:** Pipe-based composition relies on stable, machine-readable output formats — solving §2 (output format) is a prerequisite for solving this challenge.

---

### §7. Output Non-Determinism

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic, commander-js
- **Gap in all solutions:** Yes. Pydantic's `model_dump_json()` has deterministic field ordering; commander-js's `sortSubcommands`/`sortOptions` stabilises help output. No framework suppresses volatile fields (timestamps, random IDs) or separates them from stable data.
- **Key insight:** The `data`/`meta` envelope pattern is the right fix — volatile fields belong in `meta`, stable data in `data`, so change-detection can compare `data` alone.

---

### §8. ANSI & Color Code Leakage

- **Best covered by:** argparse (✓), clap (✓), mcp (✓)
- **Partially covered by:** typer, click, cobra, agentyper, jpoehnelt-scale
- **Gap in all solutions:** Partial. Argparse produces zero color by design. Clap's `ColorChoice::Auto` is the strongest active handling. MCP cannot leak ANSI because responses are typed JSON. Click/Typer strip color when not a TTY but edge cases exist.
- **Key insight:** Frameworks that produce no color by default (argparse) or that actively detect TTY state (clap) are safer than those that require application code to strip ANSI.

---

### §9. Binary & Encoding Safety

- **Best covered by:** cobra (✓), clap (✓), mcp (✓)
- **Partially covered by:** argparse, typer, click, pydantic, openapi, commander-js
- **Gap in all solutions:** Partial. Cobra (Go) and Clap (Rust) are safe by construction of their type systems. MCP uses base64 for all binary. Python frameworks depend on locale settings and are fragile.
- **Key insight:** Encoding safety is solved structurally in Rust (UTF-8 type invariant) and Go (byte streams + stdlib), and by protocol design in MCP (base64). Python frameworks need explicit UTF-8 sanitization.

---

### §10. Interactivity & TTY Requirements

- **Best covered by:** argparse (✓), agentyper (✓)
- **Partially covered by:** click, cobra, clap, commander-js, mcp
- **Gap in all solutions:** Partial. Argparse never prompts — a structural advantage from its narrow scope. Agentyper's `--yes`/`--answers`/`isatty()` detection is the most complete active solution. Typer is a notable danger: `typer.prompt()` blocks indefinitely on non-TTY stdin.
- **Key insight:** The safest approach is to never prompt interactively and require all input at invocation time via `--answers` — agentyper's model.

---

### §11. Timeouts & Hanging Processes

- **Best covered by:** None achieves ✓.
- **Partially covered by:** cobra, clap, commander-js, mcp
- **Gap in all solutions:** Yes — no framework enforces timeouts automatically. Cobra + `context.WithTimeout` and Clap + `tokio::time::timeout` require explicit wiring. MCP spec recommends timeouts but leaves enforcement to client implementations.
- **Key insight:** A framework that wraps every command in a timeout by default — with a structured JSON timeout error on expiry — would solve a Critical/Very-Common failure mode no existing framework addresses.

---

### §12. Idempotency & Safe Retries

- **Best covered by:** None achieves ✓.
- **Partially covered by:** openapi (HTTP method semantics), mcp (`idempotentHint` annotation)
- **Gap in all solutions:** Yes. MCP's `idempotentHint` is advisory only. OpenAPI's GET/PUT/HEAD idempotency is a convention, not an enforcement. No framework provides `--idempotency-key` support or enforces at-most-once delivery.
- **Key insight:** Idempotency declaration is a low-cost annotation (`idempotent: bool` on a command registration) with high agent-safety payoff — agents can retry safely with confidence.

---

### §13. Partial Failure & Atomicity

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic (all-or-nothing validation)
- **Gap in all solutions:** Yes. No framework provides a step manifest, completed/failed/skipped reporting, or rollback primitives. Pydantic's partial credit is for its atomic model validation, not for multi-step operation management.
- **Key insight:** Multi-step commands need a step manifest emitted before execution and a progress update after each step — so on timeout or failure the agent knows exactly what completed.

---

### §14. Argument Validation Before Side Effects

- **Best covered by:** argparse (✓), click (✓), pydantic (✓), cobra (✓), clap (✓), agentyper (✓)
- **Partially covered by:** typer, openapi, commander-js, mcp
- **Gap in all solutions:** No universal gap — six solutions get this right natively. The critical missing piece is enforcement: frameworks must make it structurally impossible to initiate side effects inside a validation phase.
- **Key insight:** This is the best-covered high-severity failure mode in the matrix. Any new framework should inherit this property from its parser/validator foundation.

---

### §15. Race Conditions & Concurrency

- **Best covered by:** None achieves ✓.
- **Partially covered by:** mcp (JSON-RPC request correlation)
- **Gap in all solutions:** Yes. No framework provides file locking, lock timeouts, session-scoped temp directories, or optimistic concurrency. MCP's partial credit is for JSON-RPC ID correlation, not concurrency safety.
- **Key insight:** Advisory file locking with a structured `LOCK_HELD` error (including `retry_after_ms`) would address the most common scenario at low implementation cost.

---

### §16. Signal Handling & Graceful Cancellation

- **Best covered by:** None achieves ✓.
- **Partially covered by:** typer, click, cobra, clap, mcp
- **Gap in all solutions:** Yes — no framework installs SIGTERM handlers automatically. Click/Typer map SIGINT to `Abort` (exit 1 + "Aborted!") but leave SIGTERM unhandled. Cobra and Clap provide clean integration points but require manual wiring. MCP has `notifications/cancelled` as a structured equivalent.
- **Key insight:** Auto-installing a SIGTERM handler that emits a partial JSON result and exits 143 is a framework responsibility that no existing solution automates.

---

### §17. Child Process Leakage

- **Best covered by:** None achieves ✓.
- **Partially covered by:** None.
- **Gap in all solutions:** Yes — universal miss. No framework tracks spawned child processes or ensures their termination on parent exit. This is one of two challenges (with §15) where not a single solution even partially addresses it at the framework level.
- **Key insight:** Tracking child PIDs in a session file and forwarding SIGTERM to them is a small, tractable feature that eliminates a silent reliability hole.

---

### §18. Error Message Quality

- **Best covered by:** pydantic (✓), clap (✓), mcp (✓), agentyper (✓)
- **Partially covered by:** argparse, typer, click, openapi, cobra, commander-js, jpoehnelt-scale
- **Gap in all solutions:** Partial. Four solutions achieve native structured errors. The gap is that even ✓ solutions don't always include all required fields: `code`, `field`, `message`, `input`, `constraint`, `retryable`, `retry_after_ms`.
- **Key insight:** Pydantic's `ValidationError.errors()` format — with machine-readable `type`, precise `loc` path, and constraint `ctx` — is the gold standard to emulate in any new framework.

---

### §19. Retry Hints in Error Responses

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic (constraint context enables self-correction), openapi (HTTP Retry-After convention)
- **Gap in all solutions:** Yes. No framework returns structured `retryable: bool`, `retry_after_ms: int`, or retry guidance in error responses. This is a high-severity, very-common failure mode with zero native solutions.
- **Key insight:** Adding `retryable` and `retry_after_ms` to a standard error envelope costs nothing to implement but gives agents the information to decide whether to retry, back off, or abort.

---

### §20. Environment & Dependency Discovery

- **Best covered by:** None achieves ✓.
- **Partially covered by:** click, pydantic, openapi, cobra, clap, commander-js
- **Gap in all solutions:** Yes. No framework provides a built-in `doctor` command that verifies environment requirements, system dependencies, and credential availability before commands run.
- **Key insight:** A framework-generated `tool doctor` command that checks all declared dependencies and prints structured pass/fail results would address this completely.

---

### §21. Schema & Help Discoverability

- **Best covered by:** pydantic (✓), openapi (✓), mcp (✓), agentyper (✓), jpoehnelt-scale (✓)
- **Partially covered by:** argparse, typer, click, python-fire, cobra, clap, commander-js
- **Gap in all solutions:** Partial. Five solutions achieve native schema discoverability. The remaining gap across all solutions is: no framework combines machine-readable JSON Schema, versioned output contracts, and per-command `--schema` flags in a single coherent system.
- **Key insight:** OpenAPI, MCP, Pydantic, and agentyper each provide schema discoverability through different mechanisms — a new framework should adopt JSON Schema as the common representation.

---

### §22. Schema Versioning & Output Stability

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic, openapi, cobra, clap, mcp
- **Gap in all solutions:** Yes. No solution injects a schema version into every response that increments on breaking changes. OpenAPI has `info.version` but it describes the API as a whole. MCP versions the protocol but not individual tool schemas.
- **Key insight:** Injecting `meta.schema_version` into every response, with the framework enforcing that breaking output changes bump the major version, is a completely novel feature.

---

### §23. Side Effects & Destructive Operations

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** click, openapi, cobra, mcp
- **Gap in all solutions:** Yes — in implementations. jpoehnelt-scale defines the target (Axis 6). Click's `click.confirm()` provides a guard but no declarative metadata. MCP's `destructiveHint` is advisory. No parser framework has a `--dry-run` primitive or `danger_level` annotation built in.
- **Key insight:** Requiring every mutating command to declare a `danger_level` and support `--dry-run` at the framework level would bring this from zero to ✓ with no per-command effort.

---

### §24. Authentication & Secret Handling

- **Best covered by:** pydantic (✓), mcp (✓)
- **Partially covered by:** click, openapi, cobra, clap, commander-js, jpoehnelt-scale
- **Gap in all solutions:** Partial. Pydantic's `SecretStr` and MCP's transport-layer auth isolation are genuinely strong. The remaining gap: no framework auto-redacts secret fields in audit logs or enforces the pattern that secrets come only from env vars or files.
- **Key insight:** Auto-redacting fields whose names match `token|secret|password|key|credential|auth` in all log/audit output is a zero-configuration safety net.

---

### §25. Prompt Injection via Output

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** argparse (no dynamic output), mcp
- **Gap in all solutions:** Yes — in implementations. jpoehnelt-scale defines it (Axis 6 level 3). Argparse's "partial" is structural: it produces no dynamic output from user data. MCP's partial is that servers SHOULD sanitize but the protocol doesn't enforce it.
- **Key insight:** Tagging external data with `"_trusted": false` in the response envelope is the minimum viable defense; full sanitization (stripping embedded instructions) is the gold standard.

---

### §26. Stateful Commands & Session Management

- **Best covered by:** mcp (✓)
- **Partially covered by:** python-fire (within-invocation chaining), openapi (cookie sessions)
- **Gap in all solutions:** Yes — in parser frameworks. MCP's explicit session lifecycle is the only native solution. All parser frameworks treat each invocation as stateless.
- **Key insight:** Session isolation (`--context <name>`) allows agents to run concurrent workflows without state collision — a small feature with large reliability benefits.

---

### §27. Platform & Shell Portability

- **Best covered by:** argparse (✓), cobra (✓), clap (✓), mcp (✓)
- **Partially covered by:** typer, click, python-fire, pydantic, openapi, commander-js, agentyper
- **Gap in all solutions:** Partial. Static binary solutions (Cobra/Clap) and protocol-based solutions (MCP) are inherently portable. Python frameworks inherit Python's portability. Commander.js requires a Node.js runtime which creates version dependency risk.
- **Key insight:** Static binaries (Go, Rust) eliminate runtime dependency issues entirely — a meaningful advantage for agent tool distribution.

---

### §28. Config File Shadowing & Precedence

- **Best covered by:** pydantic (✓), cobra (✓ via Viper)
- **Partially covered by:** click, clap
- **Gap in all solutions:** Partial. Pydantic's `BaseSettings` and Cobra+Viper both implement documented layered precedence. The remaining frameworks either skip config files entirely or implement ad-hoc precedence with no transparency.
- **Key insight:** Injecting `meta.config_sources` (list of loaded config files) and `meta.effective_config_hash` into every response would give agents config-change detection without a separate `--show-config` call.

---

### §29. Working Directory Sensitivity

- **Best covered by:** None achieves ✓.
- **Partially covered by:** click, pydantic, cobra, clap
- **Gap in all solutions:** Yes. No framework normalises relative paths to absolute, injects `meta.cwd` into responses, or provides `--cwd` overrides. Click's `Path(resolve_path=True)` and Clap's `std::fs::canonicalize()` are the nearest capabilities, but they are opt-in, not default.
- **Key insight:** Injecting `meta.cwd` into every response and defaulting all path outputs to absolute paths would close this failure mode at the framework level.

---

### §30. Undeclared Filesystem Side Effects

- **Best covered by:** None achieves ✓.
- **Partially covered by:** mcp (`readOnlyHint`, `openWorldHint`)
- **Gap in all solutions:** Yes. MCP's partial credit is for its advisory `readOnlyHint`. No solution provides declarative tracking of which files a command reads or writes.
- **Key insight:** Declarative `side_effects` metadata on command registration — even as advisory documentation — would be a start.

---

### §31. Network Proxy Unawareness

- **Best covered by:** None achieves ✓.
- **Partially covered by:** cobra (Go's default `http.ProxyFromEnvironment`), clap (Rust's `reqwest`), commander-js
- **Gap in all solutions:** Yes. Go's stdlib HTTP client respects proxy env vars by default — the strongest automatic behavior. Python's `requests` requires explicit proxy config. Node.js `https` does not auto-read proxy vars.
- **Key insight:** A framework HTTP client that respects `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` by default — and includes proxy context in network error messages — would close this without per-command work.

---

### §32. Self-Update & Auto-Upgrade Behavior

- **Best covered by:** agentyper (✓) — structural: no self-update implemented
- **Gap in all solutions:** Yes — for tools that do implement self-update. No framework provides a mechanism to suppress auto-update in non-interactive mode or prevent binary replacement during execution.
- **Key insight:** Suppressing update checks when `isatty(stdout) == false` or `CI=true` is the critical behavior; surfacing update availability as `meta.update_available` rather than as stdout prose is the output discipline piece.

---

### §33. Observability & Audit Trail

- **Best covered by:** None achieves ✓.
- **Partially covered by:** cobra, clap, mcp
- **Gap in all solutions:** Yes. No framework injects `meta.request_id`, `meta.trace_id`, or `meta.duration_ms` automatically, and none writes an append-only audit log by default.
- **Key insight:** Generating a UUID `request_id` per invocation and writing a JSONL audit log entry costs zero application developer effort if the framework handles it automatically.

---

### §34. Shell Injection via Agent-Constructed Commands

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** argparse, typer, click, cobra, clap, commander-js, mcp
- **Gap in all solutions:** Yes — in enforcement. jpoehnelt-scale names this as an Axis 5 (Input Hardening) requirement. Go's `exec.Command(name, args...)` and Rust's `Command::new(name).args(...)` take arrays and never invoke a shell by default, making them structurally safer. Python and Node.js frameworks provide no enforcement and leave `subprocess(shell=True)` as an option.
- **Key insight:** The framework must prohibit shell-string subprocess invocation at the API level, raising a registration error if a command passes a joined string instead of an array.

---

### §35. Agent Hallucination Input Patterns

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** most solutions
- **Gap in all solutions:** Partial — no solution actively rejects agent-specific attack patterns. Pydantic and OpenAPI can express `pattern` constraints but don't ship with agent-specific rejection rules. jpoehnelt-scale names the specific patterns (path traversal `../`, percent-encoding `%2F`, embedded query params `?foo=bar` in path fields).
- **Key insight:** A framework-level input sanitizer that rejects path traversal sequences, percent-encoded separators, and embedded query strings in resource ID fields would close this at zero per-command effort.

---

### §37. REPL / Interactive Mode Accidental Triggering

- **Best covered by:** pydantic (✓), openapi (✓), cobra (✓), clap (✓), mcp (✓), agentyper (✓)
- **Not susceptible:** pydantic, openapi (libraries/specs with no CLI entry point), cobra, clap (no REPL mode exists), mcp (protocol-level), agentyper (TTY-gated)
- **Affected:** python-fire (✗ — `--interactive` drops to IPython), typer (✗ — depends on config)
- **Key insight:** python-fire is uniquely dangerous here. Any framework with an `--interactive` or `--shell` mode must gate it behind an explicit `isatty()` check and refuse to enter REPL mode in non-TTY contexts.

---

### §38. Runtime Dependency Version Mismatch

- **Best covered by:** None achieves ✓.
- **Partially covered by:** openapi (server requirements), cobra (go.mod), clap (Cargo.lock), commander-js (engines field)
- **Gap in all solutions:** Yes. No framework provides a runtime preflight check that validates declared dependency versions before command execution. The partial solutions (lockfiles, `engines` field) document but don't enforce at runtime.
- **Key insight:** A `tool doctor` command that validates all declared runtime dependencies (including Node.js version, Python version, binary tools) and exits with a structured pass/fail JSON report is the correct solution.

---

### §40. parse()/parseAsync() Silent Race Condition

- **Best covered by:** All frameworks except commander-js (✓ by non-susceptibility)
- **Affected:** commander-js (✗ — the source of the footgun: calling `parse()` when `parseAsync()` is needed silently drops async middleware)
- **Gap:** Commander.js-specific. All other frameworks are either synchronous (Python, Go, Rust) or use protocol-level async (MCP).
- **Key insight:** Commander.js users must use `parseAsync()` whenever any command handler is async. A linting rule or framework wrapper that detects and enforces this at registration time would eliminate the bug class entirely.

---

### §41. Update Notifier Side-Channel Output Pollution

- **Best covered by:** argparse (✓), pydantic (✓), openapi (✓), mcp (✓), agentyper (✓)
- **Affected:** commander-js (✗ — `update-notifier` is an npm ecosystem norm), python-fire (✗)
- **Partially covered by:** typer, click, cobra, clap, jpoehnelt-scale
- **Key insight:** Frameworks that produce no stdout prose by default (argparse, pydantic, mcp) are immune. The npm ecosystem's convention of printing update notices to stdout is a category error for agent tools — update availability belongs in `meta.update_available` in the JSON response.

---

### §42. Debug / Trace Mode Secret Leakage

- **Best covered by:** openapi (✓ — spec only, no debug mode), agentyper (✓ — secrets redacted in debug)
- **Affected:** python-fire (✗ — `--trace` exposes full call stack including argument values)
- **Partially covered by:** most frameworks
- **Key insight:** Python Fire's `--trace` flag is uniquely dangerous. Any debug/trace mode must redact values for arguments whose names match secret patterns (`token`, `key`, `password`, `secret`, `credential`) before emitting stack traces or argument dumps.

---

### §43. Tool Output Result Size Unboundedness

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** pydantic, openapi, mcp, agentyper
- **Gap in all solutions:** Yes — in parser frameworks. No framework enforces a hard response size cap or truncates with a structured indicator. MCP's `maxTokens` parameter is advisory. jpoehnelt-scale's Axis 4 defines the requirement but doesn't implement it.
- **Key insight:** A framework-level `TOOL_MAX_RESPONSE_BYTES` cap with structured truncation metadata (`meta.truncated: true`, `meta.truncated_at_bytes`) would solve this without per-command work.

---

### §44. Agent Knowledge Packaging Absence

- **Best covered by:** jpoehnelt-scale (✓)
- **Partially covered by:** openapi, mcp, agentyper
- **Gap in all solutions:** Yes — no framework ships a machine-consumable skill/knowledge file alongside the tool binary. OpenAPI specs and MCP tool descriptions are the closest; jpoehnelt-scale's Axis 7 defines the SKILL.md concept explicitly.
- **Key insight:** A `tool generate-skills` command that produces an agent-consumable skill manifest (use cases, examples, common patterns) is the correct implementation.

---

### §45. Headless Authentication / OAuth Browser Flow Blocking

- **Best covered by:** mcp (✓), jpoehnelt-scale (✓)
- **Partially covered by:** click, openapi, cobra, clap, commander-js, agentyper
- **Gap in all solutions:** Partial. MCP uses transport-layer auth that never requires browser flows. jpoehnelt-scale names the multi-surface auth pattern. All parser frameworks leave auth flow control to the command author.
- **Key insight:** Any command that opens a browser for authentication must declare `requires_browser: true` in its metadata, with a `--token-env-var` alternative that accepts a pre-obtained token from the environment.

---

### §46. API Schema to CLI Flag Translation Loss

- **Best covered by:** mcp (✓)
- **Partially covered by:** typer, python-fire, pydantic, clap, agentyper, jpoehnelt-scale
- **Gap in all solutions:** Partial. MCP takes direct JSON input, eliminating the translation layer entirely. Parser frameworks that derive from Pydantic models (typer, agentyper) preserve more type information than hand-coded flags, but still lose union types and nested structures.
- **Key insight:** Accepting `--raw-payload <json>` as a direct passthrough for complex structured input — bypassing flag translation entirely — is the most pragmatic solution.

---

### §47. MCP Wrapper Schema Staleness

- **Best covered by:** None achieves ✓ or ~.
- **Affected:** mcp (✗ — the protocol itself has no drift detection mechanism for wrappers)
- **Gap in all solutions:** Universal. No solution provides a mechanism to detect or prevent drift between a CLI's native schema and its MCP wrapper representation.
- **Key insight:** A `tool mcp-validate` command that diffs the current CLI schema against a deployed MCP schema file and reports structural drift is the correct solution — and must be built from scratch.

---

### §49. Async Job / Polling Protocol Absence

- **Best covered by:** None achieves ✓.
- **Partially covered by:** openapi (async operation patterns), mcp (can return job descriptors)
- **Gap in all solutions:** Yes. No framework provides a standard `job_id` / `status_command` / `cancel_command` contract for long-running operations. MCP's partial credit is for its ability to return structured results, not for a built-in polling protocol.
- **Key insight:** Any command that exceeds a threshold duration should return a job descriptor immediately and expose `job status <id>` and `job cancel <id>` subcommands — a framework-generatable pattern.

---

### §50. Stdin Consumption Deadlock

- **Best covered by:** pydantic (✓), openapi (✓), mcp (✓) — structurally immune (no stdin consumption)
- **Partially covered by:** argparse, typer, click, cobra, clap, commander-js, agentyper
- **Affected:** python-fire (✗ — may consume stdin unexpectedly)
- **Key insight:** The framework must enforce a stdin size cap (default 64 KB) and auto-register `--input-file` for any command that consumes stdin, redirecting large payloads to file-based input.

---

### §51. Shell Word Splitting and Glob Expansion

- **Best covered by:** pydantic (✓), openapi (✓), cobra (✓), clap (✓), mcp (✓) — immune by design or structurally safe
- **Partially covered by:** argparse, typer, click, commander-js, agentyper, jpoehnelt-scale
- **Affected:** python-fire (✗ — no subprocess API discipline)
- **Key insight:** Go's `exec.Command(name, args...)` and Rust's `Command::new(name).args(args)` take argument arrays and never invoke a shell, making them structurally immune. Python frameworks must explicitly use `subprocess.run([...], shell=False)` — not enforced by any framework.

---

### §52. Recursive Command Tree Discovery Cost

- **Best covered by:** openapi (✓ — single spec document), mcp (✓ — lists all tools at session start)
- **Partially covered by:** agentyper, jpoehnelt-scale
- **Gap in all solutions:** Yes — for parser frameworks. All parser frameworks require N help calls to discover N subcommands.
- **Key insight:** A `tool manifest` command that returns the entire command tree in one JSON call is the parser framework equivalent of OpenAPI's spec document or MCP's `tools/list`.

---

### §53. Credential Expiry Mid-Session

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic, openapi, mcp
- **Gap in all solutions:** Yes. No framework distinguishes between "never authenticated" (exit 8), "credentials expired" (exit 10), and "insufficient permissions" (exit 8) with structured error fields including `expires_at` and `refresh_command`.
- **Key insight:** The framework's HTTP client should intercept 401/403 responses and map them to the correct structured error type automatically, before command code sees the response.

---

### §54. Conditional / Dependent Argument Requirements

- **Best covered by:** None achieves ✓.
- **Partially covered by:** most solutions (argparse groups, pydantic model_validators, openapi allOf/oneOf, clap conflicts_with/requires)
- **Gap in all solutions:** Yes. No solution exposes conditional argument dependencies in its machine-readable schema — agents cannot discover them without making a failing call first.
- **Key insight:** Declaring conditional requirements in the command schema (`requires: [{if: "--format=csv", then: "--separator"}]`) and validating them in Phase 1 closes this entirely. Clap's `requires_if` and `conflicts_with` are the closest existing primitives.

---

### §55. Silent Data Truncation

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic (max_length constraints), openapi (maxLength schema)
- **Gap in all solutions:** Yes. No solution detects when a value returned from a backend has been truncated, or prevents writing a value that exceeds a backend field limit before submission.
- **Key insight:** Commands that write to size-limited fields must declare `max_bytes: N` per field; the framework validates write payloads and detects read truncation by comparing returned length against declared limits.

---

### §56. Exit Code Masking in Shell Pipelines

- **Best covered by:** pydantic (✓), openapi (✓), mcp (✓) — not susceptible (no shell pipeline involvement)
- **Partially covered by:** cobra, clap
- **Affected:** argparse, typer, click, python-fire, commander-js, agentyper (✗ — no pipefail guidance)
- **Key insight:** Go's `exec.Cmd` and Rust's `Command` both expose exit status for each process explicitly. Python's `subprocess.run()` also captures exit codes correctly when used with arrays — the risk is in shell string commands. The framework should document `pipefail` requirements and warn at startup if not set.

---

### §57. Locale-Dependent Error Messages

- **Best covered by:** pydantic (✓), openapi (✓), cobra (✓), clap (✓), mcp (✓)
- **Partially covered by:** argparse, typer, click, commander-js, agentyper
- **Affected:** python-fire (✗)
- **Key insight:** Go and Rust emit English-only messages by design. Python's locale-dependent error messages from subprocesses are the core risk. The framework must set `LC_ALL=C` in all spawned subprocess environments before they produce any output.

---

### §58. Multi-Agent Concurrent Invocation Conflict

- **Best covered by:** None achieves ✓.
- **Partially covered by:** cobra, clap, mcp
- **Gap in all solutions:** Yes. No framework provides per-instance state namespacing or advisory file locking for config writes. Go and Rust frameworks can implement file locking easily but don't do so by default.
- **Key insight:** An `--instance-id` flag that namespaces all per-instance state (config cache, credential cache, temp directories, lock files) allows parallel agent invocations without conflict.

---

### §59. High-Entropy String Token Poisoning

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic (SecretStr masks values in repr)
- **Gap in all solutions:** Yes. No framework automatically detects and masks high-entropy strings (JWTs, API keys, base64 tokens) in JSON output. Pydantic's `SecretStr` requires explicit opt-in per field.
- **Key insight:** A framework-level regex scan for JWT three-part structure and base64 patterns (≥40 chars) in output fields, with replacement by semantic summaries (`[JWT: sub=..., exp=...]`), provides zero-configuration protection.

---

### §60. OS Output Buffer Deadlock

- **Best covered by:** pydantic (✓), openapi (✓), cobra (✓), clap (✓), commander-js (✓), mcp (✓)
- **Affected:** argparse, typer, click, python-fire, agentyper (✗ — Python buffers stdout by default in non-TTY)
- **Key insight:** Go and Rust flush stdout immediately. Node.js flushes automatically. Python buffers stdout in non-TTY mode unless `PYTHONUNBUFFERED=1` is set or `sys.stdout.reconfigure(line_buffering=True)` is called. The framework must do this in its bootstrap before any output.

---

### §61. Bidirectional Pipe Payload Deadlock

- **Best covered by:** pydantic (✓), openapi (✓), mcp (✓) — no bidirectional pipe usage
- **Partially covered by:** cobra, clap
- **Affected:** argparse, typer, click, python-fire, commander-js, agentyper (✗)
- **Key insight:** Go's `io.Pipe` and Rust's explicit async I/O make partial reads easier to implement correctly. Python's `subprocess.communicate()` internally handles the 64 KB buffer limit by using threads, but direct `stdin.write()` + `stdout.read()` sequences deadlock. The framework must enforce a stdin size cap (REQ-F-054) to prevent this class of deadlock.

---

### §62. $EDITOR and $VISUAL Trap

- **Best covered by:** argparse (✓), typer (✓), pydantic (✓), openapi (✓), clap (✓), mcp (✓), agentyper (✓)
- **Partially covered by:** click, cobra, commander-js, jpoehnelt-scale
- **Affected:** python-fire (✗ — may invoke system commands including editor)
- **Key insight:** Most frameworks are immune because they never invoke `$EDITOR`. Click's `click.edit()` is the primary risk in the Python ecosystem. The framework must set `EDITOR=true` and `VISUAL=true` in all spawned subprocess environments when not a TTY.

---

### §63. Terminal Column Width Output Corruption

- **Best covered by:** pydantic (✓), openapi (✓), mcp (✓) — JSON output, no wrapping
- **Partially covered by:** argparse, typer, click, cobra, clap, commander-js, agentyper
- **Affected:** python-fire (✗ — terminal-width-dependent formatting)
- **Key insight:** Any framework that emits prose or formatted text must respect `$COLUMNS` only in TTY mode. In JSON mode and non-TTY mode, all text wrapping must be disabled entirely. Pydantic/MCP are immune because their output is structured data with no line wrapping.

---

### §64. Headless Display and GUI Launch Blocking

- **Best covered by:** argparse (✓), typer (✓), pydantic (✓), openapi (✓), mcp (✓), jpoehnelt-scale (✓)
- **Partially covered by:** click, cobra, clap, commander-js, agentyper
- **Affected:** python-fire (✗)
- **Key insight:** Frameworks that never invoke GUI operations are immune. The risk is in commands that call `webbrowser.open()`, `xdg-open`, or platform-native `open`. The framework must detect headless mode and return URLs/paths in the JSON response rather than launching them.

---

### §65. Global Configuration State Contamination

- **Best covered by:** None achieves ✓.
- **Partially covered by:** pydantic, cobra, clap, mcp
- **Gap in all solutions:** Yes. No framework defaults config writes to the nearest local scope. Pydantic's `BaseSettings` has a precedence model but no local-vs-global scope enforcement. Cobra's Viper can write to any path.
- **Key insight:** Defaulting all config writes to a local scope (nearest `.tool-config` in the directory hierarchy) and requiring an explicit `--global` flag for global writes eliminates silent global state mutation.

---

### §66. Symlink Loop and Recursive Traversal Exhaustion

- **Best covered by:** None achieves ✓.
- **Partially covered by:** cobra (Go's `filepath.Walk` can be configured)
- **Gap in all solutions:** Yes — universal miss for automatic loop detection. Go's `filepath.WalkDir` does not follow symlinks by default, providing partial protection. No framework tracks visited inodes or enforces traversal depth limits automatically.
- **Key insight:** Inode tracking (storing visited device+inode pairs in a set) with configurable `--max-depth` is a small, tractable implementation that eliminates an entire class of infinite-loop vulnerabilities.

---

### §67. Agent-Generated Input Syntax Rejection

- **Best covered by:** None achieves ✓.
- **Partially covered by:** python-fire (some argument forgiveness), pydantic (lenient validators possible), clap (some lenient parsing)
- **Gap in all solutions:** Yes. No framework accepts JSON5 (trailing commas, comments, unquoted keys) for structured input flags. All frameworks require strict JSON, which agents frequently violate.
- **Key insight:** Using a forgiving JSON parser (JSON5 or similar) for all structured input flags, with normalization to strict JSON before validation, eliminates a class of perfectly valid-intent inputs that fail on syntax.

---

### §68. Third-Party Library Stdout Pollution

- **Best covered by:** pydantic (✓), openapi (✓) — library-only, no stdout output
- **Partially covered by:** cobra, clap, mcp
- **Affected:** argparse, typer, click, python-fire, commander-js, agentyper (✗ — all vulnerable to dependency stdout pollution)
- **Key insight:** Go and Rust crates rarely print to stdout by convention. Python and npm packages do so frequently. The framework must intercept fd 1 before any imports, capturing non-framework stdout writes and reclassifying them as `warnings[]` with `code: "THIRD_PARTY_STDOUT"`.

---

## Part 4: Gap Analysis

### Universally Missing (✗ in all solutions)

These failure modes have no solution with a ✓ rating.

| # | Failure mode | Severity | Why no solution covers it |
|---|-----------|----------|---------------------------|
| 1 | Exit Codes & Status Signaling | Critical | Existing frameworks handle 0/1/2 but not the full 9-code taxonomy |
| 11 | Timeouts & Hanging Processes | Critical | Requires framework-level enforcement; all frameworks leave it to applications |
| 12 | Idempotency & Safe Retries | Critical | No declaration mechanism or enforcement exists in any framework |
| 13 | Partial Failure & Atomicity | Critical | Multi-step semantics are entirely above framework level in all solutions |
| 15 | Race Conditions & Concurrency | High | No parser framework provides locking primitives |
| 16 | Signal Handling & Graceful Cancellation | High | All frameworks leave signal wiring to applications |
| 17 | Child Process Leakage | Medium | Not in scope for any existing framework |
| 19 | Retry Hints in Error Responses | High | Novel requirement; no framework has modeled it |
| 20 | Environment & Dependency Discovery | Medium | A `doctor` command requires framework convention to be useful |
| 22 | Schema Versioning & Output Stability | High | Per-command schema versioning is a novel concept |
| 29 | Working Directory Sensitivity | Medium | Framework-level cwd injection not implemented anywhere |
| 31 | Network Proxy Unawareness | High | Only Go/Rust solve this via stdlib; no framework enforces it |
| 32 | Self-Update & Auto-Upgrade Behavior | High | No framework manages update suppression |
| 33 | Observability & Audit Trail | Medium | Request IDs and audit logs require framework-level hooks not present anywhere |
| 47 | MCP Wrapper Schema Staleness | High | No sync mechanism exists between CLI schemas and MCP wrapper schemas |
| 49 | Async Job / Polling Protocol Absence | High | No standard job descriptor protocol exists in any framework |
| 53 | Credential Expiry Mid-Session | Critical | No framework distinguishes expiry from denial with structured error fields |
| 55 | Silent Data Truncation | High | No framework detects or reports write-side truncation |
| 58 | Multi-Agent Concurrent Invocation Conflict | High | No framework provides instance-ID namespacing or advisory config locking |
| 59 | High-Entropy String Token Poisoning | High | No framework auto-detects or masks high-entropy output fields |
| 66 | Symlink Loop and Recursive Traversal Exhaustion | High | No framework tracks visited inodes in traversal utilities |
| 67 | Agent-Generated Input Syntax Rejection | High | No framework accepts JSON5 for structured input flags |

### Partially Covered Everywhere (~ in most solutions, no ✓)

| # | Failure mode | Best Partial | Gap to ✓ |
|---|-----------|-------------|----------|
| 1 | Exit Codes | argparse, clap (0/2 taxonomy) | Full 9-code table + named constants + enforcement |
| 6 | Command Composition & Piping | python-fire (chaining), cobra | Structured pipe protocol with stable output contracts |
| 7 | Output Non-Determinism | pydantic (deterministic `model_dump`) | `data`/`meta` separation + stable sort declarations |
| 10 | Interactivity & TTY | argparse (structural), agentyper (active) | Framework-wide `--answers` pattern + `isatty()` as default |
| 22 | Schema Versioning | openapi, mcp (protocol version) | Per-command `meta.schema_version` injected automatically |
| 38 | Dependency Version Mismatch | cobra, clap (lockfiles) | Runtime preflight check with structured pass/fail report |
| 54 | Conditional Argument Requirements | clap (requires_if), pydantic | Declarative schema + Phase 1 enforcement + schema export |
| 65 | Global Config Contamination | cobra+Viper, pydantic | Default-to-local scope with `--global` flag required for global writes |

### Well Served (✓ in 3+ solutions)

| # | Failure mode | Solutions with ✓ | Recommendation |
|---|-----------|-----------------|----------------|
| 14 | Argument Validation Before Side Effects | argparse, click, pydantic, cobra, clap, agentyper | Adopt pydantic validation + two-phase enforcement |
| 3 | Stderr vs Stdout Discipline | argparse, cobra, clap | Adopt the `cmd.ErrOrStderr()` / `cmd.OutOrStdout()` pattern |
| 9 | Binary & Encoding Safety | cobra, clap, mcp | Adopt base64 for binary fields; Rust/Go type guarantees; UTF-8 sanitization |
| 21 | Schema & Help Discoverability | pydantic, openapi, mcp, agentyper, jpoehnelt-scale | Adopt JSON Schema via `model_json_schema()` + `--schema` flag |
| 27 | Platform & Shell Portability | argparse, cobra, clap, mcp | Python stdlib or static binary distribution; protocol-level portability |
| 18 | Error Message Quality | pydantic, clap, mcp, agentyper | Adopt pydantic's structured `ValidationError` format |
| 37 | REPL Mode Prevention | pydantic, openapi, cobra, clap, mcp, agentyper | Gate all REPL/interactive modes behind `isatty()` check |
| 62 | $EDITOR/$VISUAL Trap | argparse, typer, pydantic, openapi, clap, mcp, agentyper | Set `EDITOR=true` in subprocess env; declare non-interactive alternatives |
| 64 | Headless GUI Blocking | argparse, typer, pydantic, openapi, mcp, jpoehnelt-scale | Return URLs/paths in JSON response instead of launching GUI |

---

## Part 5: Solution Archetypes

### Parser Frameworks (argparse, click, typer, cobra, clap, commander-js, python-fire)

**What they're good at:**
- Argument parsing, type coercion, and help generation
- Validation before execution (all except python-fire)
- Stream separation (cobra, clap, argparse)
- Shell portability (all)
- Low barrier to entry for command authors

**What they're blind to:**
- Output format — universally left to the developer
- Timeouts, signals, idempotency, observability — entirely out of scope
- Retry hints, schema versioning, pagination — not modeled
- Agent-specific failure modes (prompts, ANSI, token cost) — addressed inconsistently

**Within-archetype ranking for agent use:** Cobra > Clap > argparse > Click > Typer > Commander.js > Python-Fire

The Go and Rust frameworks (cobra, clap) outperform their Python and JavaScript counterparts primarily because their type systems and standard libraries provide structural encoding safety, stream separation, locale invariance, and safe subprocess invocation — not because they were designed with agents in mind.

---

### Schema / Validation Libraries (pydantic, openapi)

**What they're good at:**
- Schema definition and export (JSON Schema)
- Input validation with structured, machine-readable errors
- Authentication patterns (pydantic's `SecretStr`, openapi's `securitySchemes`)
- Config precedence (pydantic-settings)
- LLM tool registration (pydantic's native integration with OpenAI/Anthropic SDKs)
- Structural immunity to many agent-specific I/O failure modes (no subprocess invocation, no stdout output, no GUI operations, no locale-dependent output)

**What they're blind to:**
- Output discipline — neither enforces stdout/stderr routing
- Operational concerns — timeouts, signals, observability are entirely out of scope
- They describe interfaces and validate data; they do not run commands or emit outputs

**v1.4 observation:** Pydantic rises to #2 overall (45%) because its "not applicable" ratings across §50/§51/§56/§57/§60/§61/§62/§63/§64/§68 count as ✓ (immune by design). A combined pydantic + parser framework achieves the highest possible baseline.

---

### Agent Protocols (mcp)

**What it's good at:**
- Structured, typed responses — the only solution where output format is ✓ by construction
- ANSI / binary safety — impossible to violate by design
- Schema discoverability at session start
- Authentication isolation from tool arguments
- Session lifecycle management
- Cancellation via `notifications/cancelled`
- Tool annotations for destructive/idempotent/read-only hints
- Immune to most I/O and environment failure modes (no stdout buffering issues, no locale sensitivity, no shell word-splitting)

**What it's blind to:**
- Exit codes (replaced by `isError: true`, structurally different)
- Retry hints (advisory annotations only, no structured `retry_after_ms`)
- Working directory context
- Composition / piping
- Timeouts (recommended but not enforced)
- Tool schema versioning and drift detection

**Unique position:** MCP scores highest (57.7%) because it solves the hardest problems structurally. Its remaining gaps are in operational reliability (retries, timeouts, concurrency) and completeness (working directory, composition, schema versioning).

---

### Agent-First CLIs (agentyper)

**What it's good at:**
- Auto-injected `--schema`, `--format`, `--yes`, `--answers` on every command
- `isatty()` auto-detection for format selection
- Pydantic-based structured errors
- Drop-in Typer replacement for migration
- Debug mode secret redaction; update suppression in non-TTY

**What it's blind to:**
- 37 of 65 failure modes at the ✓ level
- All operational reliability concerns (timeouts, signals, idempotency, partial failure)
- All concurrency, credential expiry, and input syntax concerns
- Observability, pagination, config precedence

**Unique position:** agentyper is the only Python framework explicitly designed for agent ergonomics, yet at v0.1.4 scores 29.2%. It is the right philosophical foundation but needs the execution-reliability, security, and environment layers.

---

### Evaluation Rubrics (jpoehnelt-scale)

**What it's good at:**
- Defining the target state for output format, schema discoverability, input hardening, dry-run, prompt injection, and context window discipline
- Unique Axis 7 (knowledge packaging) — scoring whether a CLI ships agent-consumable skill files
- Unique Axis 5 (input hardening) — naming agent-specific attack patterns (path traversals, percent-encoding, hallucinated query params)
- Multi-surface readiness framing (MCP + CLI + headless auth as complementary, not competing)

**What it's blind to:**
- Exit codes (no scoring axis)
- Timeouts, signals, idempotency, partial failure, observability, config shadowing, race conditions, and most §34–68 implementation-specific challenges

**v1.4 observation:** jpoehnelt-scale drops from #6 to tied-#6 and its gap to other solutions widens on §34–68 because those challenges are implementation-specific and outside its rubric scope.

---

## Part 6: Requirements Coverage

This section maps the P0 requirements from the requirements catalogue to existing solutions.

### P0 Requirements vs Existing Solutions

| Req ID | Name | argparse | typer | click | pydantic | cobra | clap | mcp | agentyper |
|--------|------|----------|-------|-------|----------|-------|------|-----|-----------|
| REQ-F-001 | Standard Exit Code Table | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-F-002 | Exit Code 2 for Validation Failures | ✓ | ~ | ~ | ~ | ✗ | ~ | ✗ | ~ |
| REQ-F-003 | JSON Output Mode Auto-Activation | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ~ |
| REQ-F-004 | Consistent JSON Response Envelope | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-F-005 | Locale-Invariant Serialization | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ |
| REQ-F-006 | Stdout/Stderr Stream Enforcement | ✓ | ~ | ~ | ✗ | ✓ | ✓ | ~ | ~ |
| REQ-F-007 | ANSI/Color Code Suppression | ✓ | ~ | ~ | ✗ | ✗ | ✓ | ✓ | ~ |
| REQ-F-008 | NO_COLOR and CI Environment Detection | ✗ | ~ | ~ | ✗ | ✗ | ~ | ✓ | ~ |
| REQ-F-009 | Non-Interactive Mode Auto-Detection | ✓ | ✗ | ~ | ✗ | ✗ | ~ | ~ | ✓ |
| REQ-F-010 | Pager Suppression | ✓ | ✓ | ~ | ✓ | ✗ | ✓ | ✓ | ✓ |
| REQ-F-011 | Default Timeout Per Command | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-F-012 | Timeout Exit Code and JSON Error | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-F-013 | SIGTERM Handler Installation | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-F-014 | SIGPIPE Handler Installation | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-F-015 | Validate-Before-Execute Phase Order | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |
| REQ-F-044 | Shell Argument Escaping Enforcement | ✗ | ✗ | ✗ | ✓ | ~ | ~ | ✓ | ✗ |
| REQ-F-047 | REPL Mode Prohibition in Non-TTY | ~ | ✗ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ |
| REQ-F-051 | Debug/Trace Mode Secret Redaction | ~ | ~ | ~ | ~ | ~ | ~ | ~ | ✓ |
| REQ-F-052 | Response Size Hard Cap | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-F-053 | Stdout Unbuffering in Non-TTY Mode | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ |
| REQ-F-062 | Glob Expansion Prevention | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ |
| REQ-F-065 | Pipeline Exit Code Propagation | ✗ | ✗ | ✗ | ✓ | ~ | ~ | ✓ | ✗ |
| REQ-O-001 | --output Format Flag | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ~ |
| REQ-O-003 | --limit and --cursor Pagination Flags | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-F-018 | Pagination Metadata on List Commands | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-F-019 | Default Output Limit | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-C-001 | Command Declares Exit Codes | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-C-002 | Command Declares Danger Level | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ~ | ✗ |
| REQ-C-003 | Mutating Commands Declare effect Field | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ |
| REQ-C-004 | Destructive Commands Must Support --dry-run | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-C-005 | Interactive Commands Must Support --yes | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ~ | ✓ |
| REQ-C-006 | All Args Validated in Phase 1 | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ |
| REQ-C-012 | Commands with Network I/O Support --timeout | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-C-013 | Error Responses Include Code and Message | ✗ | ✗ | ~ | ✓ | ~ | ~ | ✓ | ✓ |
| REQ-O-021 | --confirm-destructive Flag | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ |
| REQ-O-033 | --headless / --token-env-var Auth Flags | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ~ |

**Notes on the P0 table:**
- REQ-F-001 (standard exit code table): ✗ across all solutions — must be built from scratch.
- REQ-F-011/012 (default timeout + timeout JSON error): ✗ universally — the most critical unresolved P0.
- REQ-F-013/014 (SIGTERM/SIGPIPE handlers): ✗ universally — must be implemented in the new framework.
- REQ-F-044/062 (shell escaping + glob prevention): pydantic, cobra, clap, mcp earn ✓ through structural immunity (no subprocess invocation or array-form APIs).
- REQ-F-053 (stdout unbuffering): Python frameworks universally ✗; Go/Rust/Node structurally immune.
- REQ-C-006 (all args validated in phase 1): best-covered P0, with six ✓ solutions.

---

## Part 7: Recommendations

### What to Build (gaps no solution covers)

**Tier 1 — Critical P0 gaps (build first):**

1. **Default timeout per command with structured timeout error** (REQ-F-011, REQ-F-012): No solution enforces a wall-clock timeout automatically. The framework must wrap every command in a timeout, emit `{"ok": false, "error": {"code": "TIMEOUT"}}` to stdout, and exit with code 7.

2. **SIGTERM handler that emits partial JSON before exit** (REQ-F-013): No parser framework installs a SIGTERM handler. The framework must install one at startup, invoke cleanup hooks, emit a `{"ok": false, "partial": true, "error": {"code": "CANCELLED"}}` response, and exit with code 143.

3. **SIGPIPE handler** (REQ-F-014): No framework suppresses Python/Node `BrokenPipeError` automatically. One-line fix; high-polish signal for agents using pipes.

4. **9-code exit table with named constants** (REQ-F-001, REQ-F-002): Define and enforce the full table (0–9) and provide named constants. Validate at command registration.

5. **JSON output mode auto-activation on non-TTY** (REQ-F-003): No Python/JS parser framework does this automatically. Auto-switch to JSON when `isatty(stdout) == False`, `CI=true`, or `NO_COLOR` is set.

6. **Consistent JSON response envelope** (REQ-F-004): The `ok`/`data`/`error`/`warnings`/`meta` envelope must be a framework primitive that wraps all output.

7. **Stdout unbuffering in non-TTY mode** (REQ-F-053): Set `PYTHONUNBUFFERED=1` and call `sys.stdout.reconfigure(line_buffering=True)` in bootstrap — before any output.

8. **Pipeline exit code propagation** (REQ-F-065): Use `set -o pipefail` or language-level equivalent for all internal shell pipelines; warn at startup if not set.

**Tier 2 — High-priority operational gaps:**

9. **Retry hints in error responses** (REQ-C-014): Add `retryable: bool` and `retry_after_ms: int` to the standard error envelope.

10. **Pagination primitives** (REQ-F-018, REQ-F-019): Default 20-item limits on list commands, `has_more`/`next_cursor`/`truncated` in response envelope, `--limit` / `--cursor` flags injected automatically.

11. **Request ID, trace ID, and duration in every response** (REQ-F-024, REQ-F-039): Generate UUID `request_id` per invocation; read `TOOL_TRACE_ID` from env; measure `duration_ms`.

12. **Append-only audit log** (REQ-F-026): Write JSONL audit entries with secret redaction to `~/.local/share/<toolname>/audit.jsonl` after every invocation.

13. **Secret field auto-redaction** (REQ-F-034): Pattern-match argument and field names against `token|secret|password|key|credential|auth`; replace values with `"[REDACTED]"` in logs and audit output.

14. **Credential expiry structured error** (REQ-F-063): Distinguish UNAUTHENTICATED (exit 8) vs CREDENTIALS_EXPIRED (exit 10) vs PERMISSION_DENIED (exit 8) with `expires_at` and `refresh_command` fields.

15. **Glob expansion prohibition** (REQ-F-062): The subprocess API must require array-form invocation; raise `SHELL_STRING_PROHIBITED` at registration time if a joined string is passed.

16. **Subprocess locale normalization** (REQ-F-066): Set `LC_ALL=C` in all spawned subprocess environments to ensure English error messages.

17. **tool manifest command** (REQ-O-041): Return the entire command tree in one JSON call, eliminating N+1 `--help` discovery cost.

---

### What to Adopt (existing solutions worth incorporating)

| Adopt from | What to adopt | Why |
|------------|---------------|-----|
| **Pydantic v2** | `model_json_schema()` for schema export; `ValidationError.errors()` for structured errors; `SecretStr` for credential handling; `BaseSettings` for config precedence | Best-in-class in each category; native LLM SDK integration; structural immunity to many I/O failure modes |
| **argparse** | Exit code 2 for validation failures; `exit_on_error=False` for programmatic wrapping; `parse_known_args()` for pass-through; `suggest_on_error` | Reliable POSIX conventions with 12 years of stability |
| **Cobra + Viper** | `cmd.ErrOrStderr()` / `cmd.OutOrStdout()` API design; `SilenceUsage=true`; layered config precedence (flag > env > file > default) | Best stream discipline and config model in the evaluated set |
| **Clap** | `ColorChoice::Auto` for ANSI detection; `ErrorKind` enum as the model for a Python error-kind taxonomy; array-form subprocess invocation as default; `--color=never` wiring | Best ANSI handling; most complete error categorisation; structurally immune to glob expansion |
| **MCP** | Tool annotation model (`idempotentHint`, `destructiveHint`, `readOnlyHint`); base64 binary transport; session lifecycle pattern; `notifications/cancelled` for structured cancellation; return URLs in JSON instead of launching GUI | Protocol-level solutions to failure modes that CLIs approach heuristically |
| **agentyper** | `--answers` JSON pre-supply pattern for interactive commands; `--schema` auto-injection; `isatty()` auto-detection for format; debug mode secret redaction | Unique patterns not found elsewhere; directly usable as foundation |
| **jpoehnelt-scale** | Axis 5 input hardening checklist (path traversals, percent-encoding, embedded query params); Axis 7 knowledge packaging concept; "agent is not a trusted operator" security posture | Conceptual grounding not found in any code framework |
| **OpenAPI 3.1** | JSON Schema 2020-12 as the schema representation format; `operationId` as stable operation identifiers; `securitySchemes` for auth documentation | Standard-compliant, LLM-SDK-compatible schema format |

---

### What to Avoid (patterns not to replicate)

1. **Human-readable default output** (Click, Typer, python-fire, Commander.js): Default to machine-readable output; human display is the opt-in mode.

2. **`click.echo_via_pager()` / pager invocation** (Click, some Cobra tools): Never invoke a pager. Set `PAGER=cat` in the process environment at startup.

3. **`typer.prompt()` / `typer.confirm()` without non-interactive fallback** (Typer, Click): Any interactive call that can block must have a non-interactive bypass. Auto-detect non-TTY and fail immediately with a structured error.

4. **`python-fire`'s stdout pollution**: Writing help, trace, and error output to stdout is a fundamental violation. All non-data output belongs on stderr.

5. **Help text to stdout** (Commander.js default): Help output must go to stderr in non-TTY contexts.

6. **Unhandled SIGTERM** (argparse, typer, click, commander-js, python-fire): Install a handler that produces structured output before exiting.

7. **`print()` / `console.log()` for structured output**: Never allow command authors to write to stdout directly. Require a typed `output()` function that the framework serializes.

8. **Magic number exit codes** (all parser frameworks): Use named constants (`ExitCode.NOT_FOUND`). Validate exit codes against the declared table at registration time.

9. **`python-fire`'s `--interactive` mode**: Any REPL or interactive mode must be disabled or gated behind a TTY check.

10. **Rich tables as default output** (Typer with Rich): Decorative formatting is opt-in for humans, not the framework default.

11. **Per-command ad-hoc config loading** (most frameworks): Config file loading must be centralized with a declared, documented precedence order.

12. **Update-notifier as stdout prose** (Commander.js ecosystem): Update availability belongs in `meta.update_available` in the JSON envelope, not stdout prose.

13. **`subprocess(shell=True)` or shell string invocation**: Always use array-form subprocess invocation. The framework must raise an error if a shell string is passed to its subprocess API.

14. **`$EDITOR` invocation without TTY check**: Never open an editor in non-TTY mode. Set `EDITOR=true` and `VISUAL=true` in all subprocess environments when not a TTY.

15. **Defaulting config writes to global scope**: All config writes must default to local scope. Global writes require explicit `--global` flag.

---

*CLI Agent Spec v1.6 — 71 active failure modes, 12 solutions evaluated. Updated 2026-05-07.*
