---
name: fixlayer-report
description: Generate a FixLayer HTML audit report from a tool execution trace file (JSONL, JSON array, or single-event JSON). Classifies all Bash calls against the CLI Agent Spec §N taxonomy, then renders a self-contained HTML report in the FixLayer design system with per-match triggering events, workarounds, memory strings, and action items. Use when the user has a tool-execution log and wants a visual audit report.
---

# FixLayer Report

## Runtime requirements

- Requires Python 3.10+
- Requires `cli-agent-diagnose` installed alongside this skill

Generate a self-contained HTML audit report from a tool execution trace.

## Available scripts

- **`scripts/generate_report.py`** — Runs the classifier and renders the HTML report in one command

---

## Inputs

- **Trace file** — a path to one of:
  - Claude Code PostToolUse hook log (JSONL — one record per line with `tool_name`, `tool_input`, `tool_response`)
  - OpenAI message history (JSON array)
  - Single-event trace (JSON object with `command`, `stdout`, `stderr`, `exit_code`)

---

## Step 1 — Run the report generator

```bash
uv run scripts/generate_report.py <trace-file>
```

The script:
1. Calls `cli-agent-diagnose/scripts/diagnose.py --explain` on the trace
2. Collects session stats (tool counts, durations, retries)
3. Renders a self-contained HTML report in the FixLayer design system
4. Prints the output path to stdout

Optional flags:

```bash
# Custom output path
uv run scripts/generate_report.py trace.jsonl --out reports/audit.html

# Override challenges/ directory (if not running from the repo)
uv run scripts/generate_report.py trace.jsonl --challenges-dir /path/to/challenges
```

---

## Step 2 — Open the report

```bash
open $(uv run scripts/generate_report.py <trace-file>)
```

Or pipe the path:
```bash
uv run scripts/generate_report.py trace.jsonl | xargs open
```

---

## Step 3 — Interpret and act

Read the report sections in order:

1. **Verdict strip** — pass/fail and the §N codes found
2. **Match cards** — for each §N: evidence, triggering tool calls, workaround, limitation
3. **Store** — add the memory entry and skill patch from each match before the next session
4. **Action items** — ordered list of what to resolve before retrying

---

## Rules

- Always store both `memory` and `skill_patch` from each match — the report surfaces them but does not store them automatically
- If the report shows a §53 match on traces that ran `diagnose.py` itself, treat it as a likely false positive — check whether the "401" appeared in `diagnose.py`'s own JSON output
- Re-run after applying workarounds to confirm the failure modes are gone
