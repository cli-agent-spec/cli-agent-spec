# Schema: DiagnoseResult

**File:** [`diagnose-result.json`](diagnose-result.json)

> **Used by:** [`cli-agent-diagnose`](../skills/cli-agent-diagnose/SKILL.md) skill — returned as the top-level output of `diagnose.py`

---

## Purpose

`DiagnoseResult` is the output envelope returned by the `cli-agent-diagnose` tool. It maps a failed agent tool call trace to one or more §N failure modes from the CLI Agent Spec, delivers applicable workarounds, and provides ready-to-use memory and skill-patch strings the consuming agent can store to avoid repeating the failure.

---

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `"1.0"` | yes | Schema version for adapter compatibility checks |
| `matches` | `FailureModeMatch[]` | yes | Matched failure modes, sorted by confidence descending; empty array when `no_match` is true |
| `no_match` | boolean | yes | True when the trace has output but no failure mode matched above the confidence threshold |
| `trace_insufficient` | boolean | yes | True when stdout and stderr are too sparse to classify; check `suggested_context` |
| `suggested_context` | string[] | yes | Hints for what additional trace data would enable classification; non-empty only when `trace_insufficient` is true |
| `trace_summary` | string | yes | One-line human-readable summary of the parsed trace (commands seen, failure count, retry count) |

---

## FailureModeMatch fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `failure_mode_id` | integer ≥ 1 | yes | §N identifier from the CLI Agent Spec failure taxonomy |
| `title` | string | yes | Human-readable failure mode title from the challenge file |
| `confidence` | number 0.0–1.0 | yes | Classification confidence; ≥ 0.80 from deterministic matching, LLM-adjusted otherwise |
| `evidence` | string | yes | One sentence explaining what in the trace triggered this match |
| `workaround` | string | yes | Full text of the `### Agent Workaround` section from the challenge file |
| `memory` | string | yes | One-sentence fact to store in agent memory; prevents repeating this failure in future sessions |
| `skill_patch` | string | yes | Reusable rule to add to the agent system prompt or skill file; generalises beyond this specific call |
| `severity` | `"critical"` \| `"high"` \| `"medium"` \| `"low"` \| `"unknown"` | yes | Severity from the challenge file frontmatter |
| `spec_link` | string | yes | Relative path to the challenge file from the repo root |
| `limitation` | string | yes | `**Limitation:**` line from the Agent Workaround section; empty string if none |
| `source` | `"deterministic"` \| `"llm"` | yes | Whether the match came from deterministic signal matching or LLM classification |

---

## Examples

**Single-event trace, one high-confidence deterministic match:**

```json
{
  "schema_version": "1.0",
  "matches": [
    {
      "failure_mode_id": 10,
      "title": "Interactivity & TTY Requirements",
      "confidence": 0.95,
      "evidence": "stderr contains 'requires a TTY' with exit code 1 and no --yes flag in command",
      "workaround": "Pass --yes / --non-interactive to suppress TTY check ...",
      "memory": "gh pr create requires --yes when run without a TTY",
      "skill_patch": "Always pass --yes to gh commands that create or modify resources",
      "severity": "critical",
      "spec_link": "challenges/02-critical-execution-and-reliability/10-critical-interactivity.md",
      "limitation": "Some interactive commands have no --yes equivalent; check --help first",
      "source": "deterministic"
    }
  ],
  "no_match": false,
  "trace_insufficient": false,
  "suggested_context": [],
  "trace_summary": "1 command, 1 failure, 0 retries — gh pr create exited 1"
}
```

**Trace too sparse to classify:**

```json
{
  "schema_version": "1.0",
  "matches": [],
  "no_match": false,
  "trace_insufficient": true,
  "suggested_context": [
    "Include full stderr — current trace has only exit code with no output",
    "Include the command string so argument patterns can be matched"
  ],
  "trace_summary": "1 command, 1 failure — exit 1 with no output"
}
```

**No failure mode matched:**

```json
{
  "schema_version": "1.0",
  "matches": [],
  "no_match": true,
  "trace_insufficient": false,
  "suggested_context": [],
  "trace_summary": "1 command, 1 failure — custom domain error not covered by spec"
}
```

---

## Common mistakes

- **Using `no_match` and `trace_insufficient` interchangeably** — they are mutually exclusive states. `trace_insufficient` means the trace lacked enough data to attempt matching. `no_match` means matching was attempted and nothing scored above threshold.
- **Discarding low-confidence matches** — a `confidence` of 0.40–0.79 is still actionable; the workaround may apply even if the classification is uncertain. Read `evidence` to judge applicability.
- **Ignoring `limitation`** — every workaround has a `limitation` field. Apply the workaround only after reading what it cannot fix.
- **Storing `workaround` verbatim in memory** — use `memory` (one sentence) for the memory store; `workaround` is full prose for immediate application.
- **Skipping `skill_patch`** — `skill_patch` is a reusable rule intended for the system prompt or skill file, not just the current task. Storing it prevents entire categories of future failures.

---

## Agent interpretation

When `trace_insufficient` is true: do not attempt further classification. Collect the hints from `suggested_context`, re-run the failing command with additional instrumentation (capture stderr, include the full command string), and call diagnose again.

When `no_match` is true: the failure is either application-specific (not covered by the spec) or a novel failure mode. Escalate to the human operator with `trace_summary` and the raw trace.

When `matches` is non-empty: process in confidence order. For each match:
1. Apply `workaround` to the current invocation
2. Store `memory` in the agent's memory system tagged with the CLI name and `failure_mode_id`
3. Prepend `skill_patch` to the agent's active skill file or system prompt for this CLI

Critical-severity matches (`severity: "critical"`) should block any retry until the workaround is applied.

---

## Coding agent notes

The skill is invoked as a Python script, not a JSON API. Accepted input forms:
- **Positional argument:** `python diagnose.py '<json-string>'`
- **File:** `python diagnose.py --history messages.json`
- **Stdin:** `echo '<json>' | python diagnose.py`

Optional flag: `--llm` enables LLM classification for ambiguous candidates; requires `ANTHROPIC_API_KEY`. Without `--llm`, only deterministic matching runs (zero API cost).

Exit codes from the script:
- `0` — at least one match found
- `2` — `trace_insufficient`; output still contains JSON with `suggested_context`
- `3` — `no_match`; output still contains JSON

Always parse stdout as JSON regardless of exit code — the result object is always emitted.

---

## Implementation notes

`DiagnoseResult` is an internal output type for the `cli-agent-diagnose` skill only — it is not returned by CLI tools being evaluated. It does not use `ResponseEnvelope` as a wrapper because the diagnose tool outputs the result directly, not as a CLI command response.

The `source` field distinguishes deterministic matches (pattern-based signal matching against known §N indicators) from LLM matches (one API call per ambiguous candidate). Deterministic matches have confidence ≥ 0.80 by construction; LLM matches span the full 0.0–1.0 range based on the model's scored assessment.
