---
name: cli-agent-diagnose
description: Classify a failed agent CLI tool call against the CLI Agent Spec §N failure taxonomy. Given a failed command with stdout, stderr, and exit code, identifies the matching failure mode, returns an actionable workaround, and produces a memory string and skill patch to prevent recurrence. Use when a CLI invocation fails and you need to understand why and how to work around it.
license: MIT
compatibility: Requires Python 3.10+. LLM mode requires ANTHROPIC_API_KEY and the anthropic package (installed on-the-fly via uv --with).
---

# CLI Agent Diagnose

Classify a failed CLI tool call and get an actionable §N workaround.

## Available scripts

- **`scripts/diagnose.py`** — Post-hoc classifier: given a trace (command, stdout, stderr, exit code), returns §N matches with workarounds
- **`scripts/runner.py`** — Inline subprocess wrapper: drop-in for `subprocess.run` that applies §N fixes transparently
- **`scripts/preflight_hook.py`** — Claude Code PreToolUse hook: intercepts Bash calls before they run and advises on §N risks

---

## Inputs

- **Trace** — one of:
  - A failed call visible in the current conversation (construct the JSON yourself)
  - A JSON object the user supplies: `{"command": "...", "stdout": "...", "stderr": "...", "exit_code": N}`
  - A path to a JSON file containing an agent message history (OpenAI format, LangSmith, or Langfuse)

---

## Step 1 — Build the trace JSON

Construct a JSON object from the failed call. All four fields are required:

| Field | Source |
|-------|--------|
| `command` | Exact command string that failed |
| `stdout` | Full captured stdout (empty string if none) |
| `stderr` | Full captured stderr (empty string if none) |
| `exit_code` | Integer exit code; use `124` if the command timed out |

If the user describes the failure in prose, extract these four fields from the description.

---

## Step 2 — Run the classifier

```bash
uv run scripts/diagnose.py '<trace-json>'
```

For a message history file:
```bash
uv run scripts/diagnose.py --history <path>
```

To enable LLM classification for ambiguous candidates (~$0.01 per ambiguous candidate):
```bash
uv run --with anthropic scripts/diagnose.py '<trace-json>' --llm
```

**Always parse stdout as JSON** — the result object is emitted regardless of exit code.

Exit codes:
- `0` — at least one §N match found
- `2` — trace too sparse; see `suggested_context` for what to collect
- `3` — no failure mode matched

---

## Step 3 — Interpret the result

**When `trace_insufficient` is true:**
Report the `suggested_context` hints to the user. Do not re-run on the same sparse trace — collect the missing context first, then re-classify.

**When `no_match` is true:**
The failure is application-specific or not yet in the spec. Report `trace_summary` to the user and ask for more context or escalate.

**When `matches` is non-empty:**
Process matches in confidence order (highest first):

1. Read `evidence` — one sentence explaining why §N was triggered
2. Apply `workaround` to the current invocation
3. Note `limitation` — the boundary of what the workaround covers
4. Queue `memory` and `skill_patch` for Step 5

Critical-severity matches (`"severity": "critical"`) must be resolved before retrying.

---

## Step 4 — Emit the result to the user

```
## Diagnosis Result

**Trace:** <command> (exit <exit_code>)
**Match:** §<N> — <title> (<severity>, confidence <confidence>)
**Evidence:** <evidence>

### Workaround
<workaround>

### Limitation
<limitation>
```

If `no_match` or `trace_insufficient`:
```
## Diagnosis Result

**Trace:** <trace_summary>
**Status:** <No match found | Trace insufficient>
<suggested_context as a bulleted list, or escalation note>
```

---

## Step 5 — Store memory and skill patch

After any successful match, store both immediately:

1. **Memory** — add a memory entry tagged with the CLI name and `§N`:
   > `[<cli-name> §<N>] <memory field from match>`

2. **Skill patch** — prepend to the system prompt or active skill file for this CLI:
   > `<skill_patch field from match>`

Discarding either leaves future sessions exposed to the same failure.

---

## Rules

- Always parse stdout as JSON regardless of exit code
- Do not retry a `critical`-severity failure before applying its workaround
- For `trace_insufficient`: collect more context, then re-classify — do not loop on the same sparse trace
- Use `--llm` only when all confidence scores are below 0.50; deterministic mode handles most common failures
- If the user provides a prose description rather than a structured trace, construct the JSON yourself rather than asking them to format it

---

## Optional: Preflight hook (proactive interception)

Install `scripts/preflight_hook.py` to intercept Bash tool calls in Claude Code before they run. Add to `.claude/settings.json` (use the absolute installed path):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "uv run python ~/.claude/skills/cli-agent-diagnose/scripts/preflight_hook.py"
      }]
    }]
  }
}
```

The hook reads tool input from stdin and writes an advisory to stdout. It never blocks (exit 0 only).
