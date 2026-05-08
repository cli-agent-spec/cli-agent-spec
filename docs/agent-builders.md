# FixLayer — Agent Tool Call Diagnostics

**Agent Tool Call Diagnostics**

---

## Your agent retries blindly. It doesn't have to.

FixLayer covers the full agent tool call lifecycle: prevent known failures before they run, fix bad calls inline, classify failures after the fact. Three modes, one §N taxonomy, zero blind retries.

[See an example](#example) · [Install cli-agent-diagnose](#install)

---

## The Problem

### Exit 0 doesn't mean it worked

The worst failures are silent. No error, no retry — just 3,200 tokens of output the agent didn't need, on a 30-commit repo. On a real project this is 100,000+ tokens per call.

**Without FixLayer**

```
# Agent calls git log to check history
$ git log
exit_code=0  ← looks fine
stdout: 331 lines
  commit 44243d62676bb947d871c5c...
  Author: dev@company.com
  Date:   Wed Apr 29 16:44:38 2026

      chore: add gstack skill routing...

  commit 0208d45387b00222b74750e0...
  Author: dev@company.com
  ...28 more commits, full details...

# No error. But agent pays the cost:
~3,200 tokens consumed
full SHA + email + date + body
for every commit since repo start
```

Tokens consumed: **~3,200** · grows with every commit

**With FixLayer**

```
# Same call
$ git log
stdout: 12,889 chars  exit_code=0

# FixLayer classifies:
§43 — Output Unboundedness
confidence: 0.88  severity: critical

# Workaround — fix this call:
git --no-pager log --format="%h %s" -n 20
# → 347 tokens (9× less)

# Memory — store for future sessions:
"git log returns all history by default;
 always add -n and --format for agent use"

# Skill patch — add to system prompt:
"When calling git log, always scope with
 -n <limit> and --format='%h %s'"
```

Returns: **workaround** + **memory** + **skill patch**

---

## How It Works

### Three modes. Full lifecycle.

Before the call, during the call, after the call. RTK has one mode. FixLayer has three.

**1 · Pre-flight — before the call** `zero tokens`

`preflight(["git", "log"])` inspects the command shape before anything runs. Flags §43 (no `-n` limit), §10 (editor will open), §19 (already failed in history). Returns the correct call instead. Wires into Claude Code as a PreToolUse hook — every Bash call screened automatically, no agent code change.

**2 · Inline wrapper — during the call** `zero tokens`

`fixlayer.run(["git", "log"])` is a drop-in for `subprocess.run`. Pre-flight transforms the command before running. Post-flight detects §N in the output and re-runs with the fix — one call, correct result, no second round-trip from your agent.

**3 · Post-hoc classifier — after the call** `~$0.01`

Pass any trace: raw dict, message history, Langfuse span, LangSmith run. Nine deterministic patterns match at zero cost. Ambiguous failures get one focused LLM call per candidate §N. Returns §N match, workaround, **memory** entry for the agent to store, and a **skill patch** — a rule that eliminates this failure class permanently.

> FixLayer reads the [CLI Agent Spec](https://github.com/cli-agent-spec/cli-agent-spec) directly at runtime — 71 named §N failure modes, each with a documented `### Agent Workaround` section. No separate model training. No taxonomy to maintain. The spec is the knowledge base.

---

## Example

### What you get back

A real trace from a stuck agent pipeline. The classifier catches it in under 200ms at zero token cost.

**Input trace**

```json
{
  "command":   "git",
  "args":      ["commit", "-m", "feat: update config"],
  "stdout":    "",
  "stderr":    "hint: Waiting for your editor to close the file...",
  "exit_code": 124
}
```

**FixLayer output**

```
§10 — Interactivity & TTY Requirements
95% confident · critical · source: deterministic · 0 tokens

exit_code=124 (timeout) + interactive prompt pattern detected in stderr:
"Waiting for your editor to close"

Workaround — apply immediately:
env = {
    **os.environ,
    "EDITOR":     "true",      # no-op editor, exits 0
    "GIT_EDITOR": "true",
    "PAGER":      "cat",
    "GIT_PAGER":  "cat",
}
result = subprocess.run(
    cmd, env=env,
    stdin=subprocess.DEVNULL,
    capture_output=True,
    timeout=30,
)
```

Limitation: tools that open `/dev/tty` directly still block — use timeout as circuit breaker

**Agent applies fix**

```python
# Option A — diagnostic: re-call with returned workaround
result = subprocess.run(
    ["git", "--no-pager", "log", "--format=%h %s", "-n", "20"],
    capture_output=True, text=True, timeout=30,
)
# Agent makes a second call with the fixed command.

# Option B — wrapper: one call, fixed transparently
from fixlayer.runner import run

result = run(["git", "log"])  # same call as before

# FixLayer rewrites it inline to:
#   git --no-pager log --format="%h %s" -n 20
# before subprocess even runs.

result.stdout          # → 20 lines, 1,391 chars
result.fixed           # → "§43 pre-flight: added --no-pager ..."
result.failure_mode_id # → 43

# No second call. No agent code change.
# Already-correct calls pass through untouched.
```

---

## Why FixLayer

### Built for the agent that can't ask for help

**Prevent before it happens**

Pre-flight checks the command shape before anything runs. `git log` without `-n`? Flagged as §43, corrected to `git --no-pager log --format="%h %s" -n 20` before the subprocess starts. Wire the PreToolUse hook once — every call screened automatically.

**Fix inline, no re-call**

The inline wrapper intercepts, transforms, and re-runs — returning the correct result in one call. Your agent code doesn't change. No second round-trip. No retry loop. The fix is invisible.

**The agent learns**

Every §N match returns a **memory** entry (one-liner the agent stores) and a **skill patch** (rule for the system prompt). The agent stops making the same mistake. RTK compresses every call forever. FixLayer eliminates failure classes permanently.

---

## The Taxonomy

### The only failure intelligence layer covering the full agent tool call lifecycle

Langfuse logs it. RTK compresses it. FixLayer fixes it — before it runs, while it runs, and after it fails.

| | |
|---|---|
| **3** | operating modes (pre · inline · post) |
| **71** | named §N failure modes |
| **3–15%** | production tool call failure rate |
| **32** | tools using Agent Skills format |

---

## Install

### Install in one command

Works as an installable agent skill or as a standalone Python script. No dependencies beyond the Anthropic SDK for the LLM stage — and that stage is optional for the nine zero-cost deterministic patterns.

**Claude Code / Claude agents**

```
# Install the skill
/install cli-agent-diagnose

# Then use it: paste a failed trace, get §N + workaround
```

**Standalone Python — deterministic only, zero tokens**

```bash
# Single failed trace
python diagnose.py \
  '{"command":"deploy","stderr":"Are you sure? [y/n]","exit_code":124}'

# Full message history from a run
python diagnose.py --history messages.json

# With LLM for ambiguous failures (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=... python diagnose.py '...' --llm
```

**Langfuse / LangSmith span**

```bash
# Pipe a span directly — format detected automatically
langfuse export span <id> | python diagnose.py
```

Community plugins for Langfuse and LangSmith registries — coming Sprint 3

---

## Before. During. After.

### The full agent tool call lifecycle.

Pre-flight prevents. The wrapper fixes inline. The classifier names what went wrong and teaches the agent not to repeat it. Open source. Zero blind retries.

[View on GitHub](https://github.com/cli-agent-spec/cli-agent-spec) · [Browse §N failure modes](https://github.com/cli-agent-spec/cli-agent-spec/blob/master/challenges/index.md)

---

*FixLayer · built on the [CLI Agent Spec](README.md) (71 failure modes · 154 requirements)*
