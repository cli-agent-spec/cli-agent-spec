# CLI Agent Spec

**Your CLI tool works perfectly for humans. For AI agents, it silently hangs, corrupts data, leaks secrets, and exhausts context windows — and you would never know.**

This is a specification for building CLI tools that AI agents can call reliably: **73 documented failure modes**, **155 requirements** to eliminate them, machine-readable schemas an agent can consume directly, and design guides for CLI authors.

> **No existing CLI framework covers more than 58% of these failure modes.**

---

## What's going wrong right now

AI agents call CLI tools constantly — to deploy infrastructure, query APIs, manage files, run pipelines. Most tools were never designed for this. Here is what agents actually encounter:

```bash
# Agent calls a list command. The tool pages output and waits for keypress.
# The agent never receives a response. The pipeline stalls. Forever.
$ kubectl get pods   # opens less, waits for input

# Agent deploys to staging. The command times out at 30s, returns exit 1.
# exit 1 means "error" — but does it mean "nothing happened" or "half-deployed"?
# The agent retries. Now it's deployed twice.
$ deploy --env staging   # exit 1 — but why? safe to retry?

# Agent reads a list of users. One username contains an emoji.
# The JSON serializer crashes on non-ASCII. The agent gets no output, no error.
$ tool users list   # silent failure on emoji in username

# Agent passes a flag after the subcommand — natural LLM ordering.
# The parser silently treats --output as a positional argument value.
# The agent receives plain text it can't parse. Exit code: 0.
$ tool list users --output json   # parsed as: list "users" "--output" "json"
```

These are not edge cases. They are the **default behavior** of most CLI tools today — including tools from major companies. The cost falls on the agent: wasted tokens, stalled pipelines, data corruption from blind retries, cascading failures with no root cause.

---

## What this spec defines

**73 failure modes** — each documented with severity, frequency, detectability, token cost, time cost, and context cost from the agent's perspective. Grouped into 7 parts: ecosystem/runtime, execution, security, output, environment, errors, and observability.

**155 requirements** across 3 tiers:

| Tier | Count | Who implements it |
|------|-------|------------------|
| **F** — Framework-Automatic | 78 | The framework enforces it; command authors get it for free |
| **C** — Command Contract | 29 | Command authors declare it at registration |
| **O** — Opt-In | 48 | Applications enable it explicitly |

**4 JSON schemas** — machine-readable type definitions for exit codes, response envelopes, tool manifests, and error details. Generate typed structs for your language directly from the schemas.

**A comparison matrix** — 12 existing frameworks (argparse, Click, Cobra, Clap, Typer, Commander.js, and more) scored against all 71 failure modes. No framework exceeds 58%.

---

## The three contracts that matter most

**Exit codes** — 14 named codes (0–13) with machine-readable guarantees per code: `retryable: true/false`, `side_effects: "none" | "partial" | "complete"`. An agent receiving exit 11 (`CONFLICT`) knows the operation is safe to retry. Receiving exit 6 (`PARTIAL_FAILURE`) knows it must inspect state before retrying. See [`exit-code.json`](schemas/exit-code.json).

**Response envelope** — every command wraps its output in `{ ok, data, error, warnings, meta }`. The same keys are always present. Agents never parse free-text to determine success or failure. See [`response-envelope.json`](schemas/response-envelope.json).

**Tool manifest** — `tool manifest --output json` returns the complete command tree: every subcommand, flag, type, description, exit code map, and example. One call replaces O(N) `--help` iterations and eliminates trial-and-error argument discovery. See [`manifest-response.json`](schemas/manifest-response.json).

---

## What's in this repo

| Path | Contents |
|------|----------|
| [`challenges/`](challenges/index.md) | 71 failure modes, each with problem, impact, solutions, 0–3 evaluation rubric, and agent workaround |
| [`requirements/`](requirements/index.md) | 154 requirements with acceptance criteria, wire format, and examples |
| [`schemas/`](schemas/index.md) | JSON Schema draft-07 definitions for all 4 types |
| [`guides/`](guides/index.md) | Design guides: positive conventions that cannot be expressed as enforceable requirements |
| [`IMPLEMENTING.md`](IMPLEMENTING.md) | Implementation guide: wave-based order, goal-based paths, invariants, codegen |
| [`comparison-matrix.md`](comparison-matrix.md) | 71 failure modes × 12 frameworks coverage table |
| [`research/`](research/index.md) | Per-framework analysis and competitive landscape (MCP, OpenAPI, function calling) |
| [`skills/`](https://github.com/cli-agent-spec/cli-agent-spec/tree/master/skills) | Agent skills for evaluating CLIs and guiding implementation |

---

## Start here

**I want to understand the problem** → [`challenges/index.md`](challenges/index.md) — browse by severity. Start with §10 (interactive blocking), §43 (output size), §50 (stdin deadlock), §62 (editor trap).

**I want to implement this in my framework** → [`IMPLEMENTING.md`](IMPLEMENTING.md) — wave-based implementation order, or pick a goal-based path:
- [Fewer agent retries](IMPLEMENTING.md#path-a-fewer-retries) — 15 requirements
- [Less context consumed](IMPLEMENTING.md#path-b-less-context-consumed) — 14 requirements
- [Less token spend](IMPLEMENTING.md#path-c-less-token-spend) — 12 requirements

**I want to evaluate my existing CLI** → use the agent skills below, or read [`challenges/checklist.md`](challenges/checklist.md) for a self-assessment.

**I want to add a failure mode or requirement** → [`AGENTS.md`](AGENTS.md)

---

## Agent skills

Four installable skills for [Agent Skills-compatible](https://agentskills.io) agents (Claude Code, Cursor, Gemini CLI, Copilot, and others):

| Skill | Purpose |
|-------|---------|
| [`cli-agent-onboard`](https://github.com/cli-agent-spec/cli-agent-spec/blob/master/skills/cli-agent-onboard/SKILL.md) | Profile a CLI tool once — detects runtime, binary, flags, timeout method |
| [`cli-agent-evaluate`](https://github.com/cli-agent-spec/cli-agent-spec/blob/master/skills/cli-agent-evaluate/SKILL.md) | Score a CLI against a single failure mode (0–3), with applicable agent workaround |
| [`cli-agent-implement`](https://github.com/cli-agent-spec/cli-agent-spec/blob/master/skills/cli-agent-implement/SKILL.md) | Guide implementing the spec in a CLI framework, tier by tier |
| [`cli-agent-diagnose`](skills/cli-agent-diagnose/SKILL.md) | Classify a failed CLI call against §N taxonomy, return workaround + memory string |

```bash
# Install (run inside your agent)
npx skills install romamo/cli-agent-spec/skills/cli-agent-onboard
npx skills install romamo/cli-agent-spec/skills/cli-agent-evaluate
npx skills install romamo/cli-agent-spec/skills/cli-agent-implement
npx skills install romamo/cli-agent-spec/skills/cli-agent-diagnose
```

---

## Contributing

The spec is a living document. New failure modes are documented when confirmed against real tooling. New requirements follow from new failure modes.

Before contributing, read [`AGENTS.md`](AGENTS.md) for conventions: file format, required sections, naming rules, and how to run `/validate-links` to verify cross-references after any edit.

---

*CLI Agent Spec v1.6 — 71 failure modes · 154 requirements · 4 schemas · 12 frameworks evaluated*
