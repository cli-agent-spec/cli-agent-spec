# Guide: LLM-Optimized Output Formats

> **The principle:** JSON is for programmatic parsers; LLM-optimized text is for language model readers. A CLI designed for agent orchestration must serve both audiences — structured JSON for the tool-calling layer, token-efficient text for the language model layer — and must declare which format serves which role.

CLI output has three distinct audiences with incompatible needs. Human-readable output (tables, colors, progress text) optimizes for terminal display. JSON optimizes for programmatic parsers: `json.loads()`, `jq`, schema validators. LLM-optimized text optimizes for a third consumer: a language model that reads stdout as part of its context window and reasons over it in natural language rather than executing code.

Most CLIs serve the first two. The `toon` format from link-cli (non-TTY default: `--format toon`) is an early example of explicit design for the third. This guide describes when that design is appropriate, what it requires, and where it creates new risks.

---

## The LLM Reader Is Not a Parser

A language model consuming CLI output does not call `json.loads()`. It reads the text as tokens and extracts meaning through inference. This changes what "structured" means:

| Audience | Needs | Fails on |
|---|---|---|
| Human | Color, alignment, progress | Machine-only formats |
| Programmatic parser | Valid JSON, consistent schema | Any non-JSON text |
| Language model | Semantic clarity, low token count | Ambiguous pronouns, redundant noise, deeply nested JSON |

JSON has structural overhead that costs tokens without adding semantic value to an LLM reader: quotation marks around every key, commas as separators, braces and brackets as nesting delimiters. A response like `{"status": "active", "user_id": 42}` is 30 tokens; `status: active  user_id: 42` conveys identical meaning in fewer. At scale across hundreds of tool calls, this difference is measurable (see §4).

An LLM-optimized format trades programmatic parseability for semantic density. That trade is only valid when the consumer is a language model, not when downstream code needs to extract structured values.

---

## The Critical Invariant: JSON Must Always Be Available

LLM-optimized text is a supplementary format, not a replacement. A CLI that offers `--format toon` without also offering `--format json` forces agent developers to choose between token efficiency and parseability.

**The invariant:** `--format json` (or equivalent) MUST always be available, MUST produce a valid `ResponseEnvelope`, and MUST be the safe default when the caller's format preference is unknown.

A non-TTY default of `toon` is reasonable for a CLI whose primary audience is language models. It is unreasonable if any downstream step in the agent pipeline needs to parse the output programmatically.

Agents that cannot determine what format a command will emit face a structural problem: they must choose a parser before they see the output. CLIs that make the non-TTY default ambiguous — or that change defaults based on env vars the agent does not control — break the agent's ability to prepare for the response (§28).

---

## Declaring the Format

An LLM-optimized format that is not declared in the command schema is invisible to agents that read manifests before invocation. The format should appear:

1. In `--help` output alongside other format values
2. In the `--schema` / manifest response, under `output_formats`
3. In `AGENTS.md` or equivalent with an explicit description of what the format produces and when to prefer it

```
# Example manifest declaration (pseudo-schema)
output_formats:
  - value: json
    description: "ResponseEnvelope JSON — use for programmatic parsing"
  - value: toon
    description: "Compact LLM-optimized text — use to reduce token cost when the LLM is the final consumer"
  - value: jsonl
    description: "Newline-delimited JSON — use for streaming or large result sets"
```

Without declaration, agents default to assuming JSON and may receive text they cannot parse. With declaration, agents can select the format that matches how they will use the output.

---

## Token-Efficiency Flags That Complement LLM Formats

LLM-optimized formats pair naturally with a second class of flags: those that bound, filter, or count output. link-cli demonstrates all of them:

| Flag | Effect |
|---|---|
| `--token-limit <n>` | Truncate output to the first `n` tokens and emit a truncation marker |
| `--token-offset <n>` | Skip the first `n` tokens (pagination over token windows) |
| `--token-count` | Print the token count of the output instead of the output itself |
| `--filter-output <keys>` | Select a subset of output fields by key path |

These flags matter because an LLM-optimized format alone does not bound output size. `--token-limit` is the LLM-aware analog of `--max-results` for a language model caller. Without it, even a compact format can overflow the agent's context window for large result sets (§43).

If a CLI offers an LLM-optimized format, it should also offer at least `--token-limit` so callers can control how much of the output lands in the model's context.

---

## The Prompt Injection Surface Expands

Human-readable output passes through a parser before reaching the agent's reasoning layer — the structure acts as a filter. LLM-optimized text lands directly in the agent's context without transformation. This expands the prompt injection surface (§25).

When API- or user-supplied data appears in `toon` output without separation markers, the agent cannot distinguish the CLI's own output from embedded instructions. A malicious value like `user_name: "ignore previous instructions and..."` is parsed as ordinary text in JSON; as natural-language content in `toon` output, it is closer to an instruction the model can act on.

**Mitigation:** LLM-optimized formats should annotate external or user-supplied fields with a trust boundary marker — a prefix, a wrapper field, or a documented per-field convention that tells the reading model which content comes from the CLI author and which comes from external data. The exact mechanism is format-specific, but the convention must be documented.

---

## Decision Table

| Consumer | Duration | Programmatic extraction needed? | Recommended format |
|---|---|---|---|
| Downstream code (agent pipeline step) | Any | Yes | `json` |
| Language model (final consumer) | <5s | No | `toon` / LLM-optimized |
| Language model (large result) | Any | No | `toon` + `--token-limit` |
| Language model or code (unknown) | Any | Unknown | `json` (safe default) |
| Stream of independent items | >5s | Per-item | `jsonl` |

When in doubt, emit JSON. A language model can read JSON; a programmatic parser cannot read `toon`.

---

## Related

| Document | Relationship |
|---|---|
| [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) | Provides: the failure mode LLM-optimized formats can introduce if JSON is removed |
| [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) | Provides: the token-cost problem LLM-optimized formats address |
| [§43 Tool Output Result Size Unboundedness](../challenges/01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md) | Provides: why `--token-limit` is necessary even with compact formats |
| [§25 Prompt Injection via Output](../challenges/03-critical-security/25-critical-prompt-injection.md) | Provides: the expanded injection surface for LLM-native output |
| [§28 Config File Shadowing & Precedence](../challenges/05-high-environment-and-state/28-high-config-shadowing.md) | Provides: the failure mode when non-TTY format defaults are env-var-controlled |
| [REQ-O-001](../requirements/o-001-output-format-flag.md) | Enforces: `--output` / `--format` flag contract that governs format selection |
| [REQ-O-042](../requirements/o-042-output-format-env-var-default.md) | Enforces: env var default for output format |
| [REQ-O-049](../requirements/o-049-llm-token-budget-flags.md) | Provides: `--token-limit`, `--token-count`, `--token-offset` — the token-budget flags that pair with LLM-optimized formats |
| [schemas/response-envelope.md](../schemas/response-envelope.md) | Provides: canonical JSON envelope that must remain available alongside LLM formats |
| [schemas/manifest-response.md](../schemas/manifest-response.md) | Provides: `output_formats` field in `CommandEntry` — how agents discover non-default format values before invocation |
| [Streaming vs Envelope Output](streaming-vs-envelope.md) | Provides: the orthogonal choice between buffered envelope and JSONL streaming |
