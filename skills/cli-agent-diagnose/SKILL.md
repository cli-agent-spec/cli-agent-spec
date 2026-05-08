---
name: cli-agent-diagnose
description: Post-hoc CLI failure classifier. Given a failed agent tool call trace (stdout, stderr, exit code, command), classifies the failure against the CLI Agent Spec §N taxonomy, returns applicable workarounds, and produces ready-to-store memory and skill-patch strings. Also ships a transparent subprocess runner wrapper and a Claude Code PreToolUse hook for proactive interception.
license: MIT
compatibility: Requires Python 3.10+. LLM classification mode requires ANTHROPIC_API_KEY. Deterministic mode runs with zero API cost.
---

# CLI Agent Diagnose

Classify a failed CLI tool call against the CLI Agent Spec failure taxonomy and get an actionable workaround.

## Operating Modes

This skill ships three components that can be used independently:

| Mode | File | When to use |
|------|------|-------------|
| **Diagnose** | `diagnose.py` | Post-hoc: agent has a failed trace and wants to classify it |
| **Runner** | `runner.py` | Inline: agent wraps `subprocess.run` to auto-apply workarounds before and after each call |
| **Preflight hook** | `preflight_hook.py` | Proactive: intercepts Bash tool calls in Claude Code before they run |

---

## Mode 1 — Diagnose (Post-Hoc Classification)

### Inputs

Provide one of:

- **Positional JSON string** — a single trace event:
  ```json
  {"command": "gh pr create", "stdout": "", "stderr": "requires a TTY", "exit_code": 1}
  ```
- **`--history FILE`** — path to a JSON file containing an agent message history list (OpenAI format, LangSmith run, or Langfuse span)
- **stdin** — same JSON, piped

Optional flags:
- **`--llm`** — enable LLM classification for ambiguous candidates (requires `ANTHROPIC_API_KEY`; adds ~$0.01 per ambiguous candidate)
- **`--challenges-dir PATH`** — override the path to the `challenges/` directory

### Step 1 — Prepare the trace

Format the failed call as a JSON object with these fields:

| Field | Required | Description |
|-------|----------|-------------|
| `command` | yes | The exact command string that failed |
| `stdout` | yes | Full captured stdout (empty string if none) |
| `stderr` | yes | Full captured stderr (empty string if none) |
| `exit_code` | yes | Integer exit code |

For message history input, pass the full conversation list as a JSON array. The parser extracts tool call / tool result pairs automatically from OpenAI, LangSmith, and Langfuse formats.

### Step 2 — Run the classifier

```bash
# Single trace
uv run python skills/cli-agent-diagnose/diagnose.py '{"command": "gh pr create", "stdout": "", "stderr": "requires a TTY", "exit_code": 1}'

# From file
uv run python skills/cli-agent-diagnose/diagnose.py --history agent_run.json

# With LLM classification
ANTHROPIC_API_KEY=... uv run python skills/cli-agent-diagnose/diagnose.py '...' --llm
```

Exit codes from the script:
- `0` — at least one §N match found; result JSON on stdout
- `2` — trace too sparse to classify; result JSON on stdout with `suggested_context`
- `3` — no failure mode matched; result JSON on stdout

Always parse stdout as JSON regardless of exit code — the `DiagnoseResult` object is always emitted.

### Step 3 — Interpret the result

The output is a `DiagnoseResult` object (schema: [`schemas/diagnose-result.json`](../../schemas/diagnose-result.json)):

**When `trace_insufficient` is true:**
Collect hints from `suggested_context`, re-capture the failing command with full stdout/stderr, and re-run the classifier.

**When `no_match` is true:**
The failure is application-specific or not yet covered by the spec. Report `trace_summary` to the user and escalate.

**When `matches` is non-empty:**
Process matches in confidence order:
1. Read `evidence` — one sentence explaining why this §N was triggered
2. Apply `workaround` to the current invocation attempt
3. Store `memory` in the agent's memory system, tagged with CLI name and `failure_mode_id`
4. Add `skill_patch` to the system prompt or active skill file for this CLI
5. Note `limitation` — the workaround's coverage boundary

Critical-severity matches (`"severity": "critical"`) must be resolved before retrying.

### Step 4 — Store memory and patch

```python
# memory — one-liner for the agent memory store
agent_memory.add(f"[{cli_name} §{match.failure_mode_id}] {match.memory}")

# skill_patch — reusable rule for system prompt / skill file
skill_file.prepend(match.skill_patch)
```

The `memory` field prevents the agent from repeating the same failure in future sessions. The `skill_patch` generalises the fix beyond this specific call — it should be retained across sessions.

---

## Mode 2 — Runner (Inline Subprocess Wrapper)

`runner.py` is a transparent drop-in replacement for `subprocess.run`. Import it in agent code that calls CLIs:

```python
from skills.cli_agent_diagnose.runner import run

# Identical call signature to subprocess.run
result = run(["git", "log", "--oneline"])

# result is a subprocess.CompletedProcess with one addition:
# result.fix — §N annotation if any transformation occurred (None otherwise)
```

The runner applies two-stage interception:

1. **Pre-flight** — transforms the command before execution using a zero-cost pattern table (e.g., injects `--no-pager` into `git log`, adds `--json` flag for CLIs that support it)
2. **Post-flight** — if output signals a §N failure mode, applies the workaround and re-runs once

The caller's code is unchanged. If `result.fix` is not None, the agent can log or store the applied §N for observability.

---

## Mode 3 — Preflight Hook (Claude Code Integration)

`preflight_hook.py` intercepts Bash tool calls in Claude Code before they execute. If a command matches a known §N failure pattern, it emits an advisory message with the corrected invocation.

**Install into `.claude/settings.json`:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "uv run python /path/to/skills/cli-agent-diagnose/preflight_hook.py"
      }]
    }]
  }
}
```

The hook reads tool input as JSON from stdin and writes an advisory to stdout. It never blocks (exit 0 only). To enable hard-blocking, change the exit code logic in `preflight_hook.py`.

---

## Rules

- Always parse stdout as JSON — the result object is emitted even when exit code is 2 or 3
- Do not retry the failing command until a `critical`-severity match is resolved
- Store both `memory` and `skill_patch` after any match — discarding either leaves future sessions exposed to the same failure
- For `trace_insufficient`: collect more context before re-classifying; do not loop on the same sparse trace
- Deterministic mode (no `--llm`) is sufficient for most common failures; add `--llm` only when confidence scores are all below 0.50
