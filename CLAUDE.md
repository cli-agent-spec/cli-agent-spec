# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **specification** (not an implementation) for building CLI tools that work reliably under AI agent orchestration. It defines 73 failure modes, 155 requirements across 3 tiers, 4 canonical JSON schemas, analysis of 12 existing frameworks, and design guides for CLI authors.

There is no build system, test runner, or package manager. All content is markdown and JSON.

## Common commands

**Validate cross-links** (broken file references, schema↔requirement symmetry, index completeness):
```
/validate-links
```

**Validate schemas manually:**
```bash
npm install -g ajv-cli
ajv compile -s "schemas/*.json" --spec=draft7
```

**Full autonomous audit (install → onboard → readiness → evaluate → report):**
```
/cli-agent-audit
```

**Onboard a CLI tool before evaluation (run once per CLI):**
```
/cli-agent-onboard
```

**Score how proactively agent-ready a CLI is (docs, integrations, setup, workflows):**
```
/cli-agent-readiness
```

**Evaluate a CLI against a single failure mode:**
```
/cli-agent-evaluate
```

**Evaluate a CLI against multiple failure modes (batch):**
```
/cli-agent-evaluate-batch
```

**Generate a perspective-specific report from findings (dev / agent-dev / runtime / issues / all):**
```
/cli-agent-report
```

**Guide implementing the spec in a CLI framework:**
```
/cli-agent-implement
```

**Classify a failed agent CLI call against §N failure modes and get a workaround:**
```
/cli-agent-diagnose
```

## Architecture

### Directories

- `challenges/` — 71 failure modes in 7 parts (01=critical ecosystem, 02=execution, 03=security, 04=output, 05=environment, 06=errors, 07=observability). Failure modes are referenced as `§N`.
- `requirements/` — 154 requirements in 3 tiers: `f-NNN` (Framework-Automatic), `c-NNN` (Command Contract), `o-NNN` (Opt-In). Referenced as `REQ-{TIER}-{NNN}`.
- `schemas/` — 4 canonical JSON Schema draft-07 types, each with a `.json` (machine) and `.md` (human) companion: `exit-code`, `exit-code-entry`, `response-envelope`, `manifest-response`. Plus `diagnose-result` (skill-internal, not a canonical spec type).
- `research/` — per-framework analysis (argparse, click, clap, cobra, typer, commander-js, pydantic, MCP, OpenAPI, etc.).
- `guides/` — design guides for CLI authors: positive conventions that cannot be expressed as enforceable requirements. See `guides/index.md`.
- `comparison-matrix.md` — 71 failure modes × 12 frameworks coverage table.

### Requirement tiers

| Tier | Prefix | Meaning |
|------|--------|---------|
| Framework-Automatic | `REQ-F` | Enforced by the framework without command author action |
| Command Contract | `REQ-C` | Declared by the command author at registration |
| Opt-In | `REQ-O` | Explicitly enabled by the application |


## Styling rules (apply to all documents)

1. **No trailing periods** in headings, labels, list items, table cells, blockquotes, or UI copy. Periods only in prose paragraphs. Exception: intentional staccato rhythm used as a rhetorical device (e.g., "Before. During. After.").
2. **Inline code** for all flag names, field names, constants, filenames, command invocations, and schema `$id` values.
3. **Verb-first** labels in `## Related` tables. Allowed verbs: `Provides` · `Consumes` · `Enforces` · `Specializes` · `Composes` · `Aggregates` · `Wraps` · `Sources` · `Exposes` · `Extends`
4. **Present tense** in all `description` fields.
5. **Agent-readable descriptions** (in `ExitCodeEntry`, `FlagEntry`, `ErrorDetail`): state the condition, ≤120 chars, no trailing period.
6. **Em dash sparingly.** Two legitimate uses only: (a) double parenthetical aside (`Any tool — bash, API, file — can...`); (b) dramatic reveal after a build-up (`no retry — just 3,200 tokens`). For everything else use the correct mark: colon to introduce a list or explanation, semicolon to join related clauses, comma for a participial phrase, period to separate sentences, parentheses for a label aside. Maximum one em dash per paragraph.

## Failure mode file format

Required sections in order: `### The Problem` → `### Impact` → `### Solutions` → `### Evaluation` → `### Agent Workaround`

- `### Solutions` is for CLI authors and framework designers only — no agent-side content here
- `### Agent Workaround` must include a `**Limitation:**` line; generic only, no tool-specific instructions
- Evaluation: 0–3 scoring table when four states are meaningful; binary pass/fail otherwise

When adding a failure mode: assign next `§N`, place in correct part folder, add rows to `challenges/index.md` and the part's `index.md`, add row to `challenges/sources.md`, create/update requirements.

## Requirement file format

Required sections in order: `## Description` → `## Acceptance Criteria` → `## Schema` → `## Wire Format` → `## Example` → `## Related`

When adding a requirement: assign next `NNN` within the tier, add row to `requirements/index.md`, link schema file(s), add to `Related` table of each schema used.

## Schema file format

Each type needs two files: `<name>.json` + `<name>.md`. The `.md` has 8 sections in order: Title+Used-by → `## Purpose` → `## Values`/field table → `## Examples` → `## Common mistakes` → `## Agent interpretation` → `## Coding agent notes` → `## Implementation notes`

JSON schema rules: draft-07, `$id` matches filename without extension, all properties have `description`, use `$ref` by filename, no language-specific content.

When adding a schema: create both files, add row to `schemas/index.md`, reference `.json` from requirements that use the type.

## Guide file format

Guides capture positive design principles that cannot be expressed as enforceable requirements. No fixed section order — content drives structure. Required elements:

- Opening blockquote stating the core principle
- At least one `## Related` table linking back to failure modes and requirements that enforce the mechanics described
- No acceptance criteria (guides are not verifiable contracts)
- No wire format (guides describe intent, not protocol)

When adding a guide: create `guides/<name>.md`, add a row to `guides/index.md`.

## Key invariant (not enforced by code generators)

`retryable: true` implies `side_effects: "none"` in `ExitCodeEntry` — this must be validated at framework registration time.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Full autonomous audit of a CLI (install + evaluate + report) → invoke /cli-agent-audit
- Onboard CLI before evaluation → invoke /cli-agent-onboard
- Score CLI proactive readiness (docs, integrations, setup, workflows) → invoke /cli-agent-readiness
- Evaluate CLI against one failure mode → invoke /cli-agent-evaluate
- Evaluate CLI against multiple failure modes / severity / part → invoke /cli-agent-evaluate-batch
- Generate fix list for CLI author from findings → invoke /cli-agent-report mode=dev
- Generate integration guide for agent builder from findings → invoke /cli-agent-report mode=agent-dev
- Generate runtime brief for an AI agent from findings → invoke /cli-agent-report mode=runtime
- Generate issues/problems report for an agent using a CLI → invoke /cli-agent-report mode=issues
- Generate all reports + index + LinkedIn post → invoke /cli-agent-report mode=all
- Guide implementing the spec in a CLI framework → invoke /cli-agent-implement
- Validate cross-links and spec consistency → invoke /validate-links
- Classify a failed agent CLI call / diagnose why a CLI invocation failed → invoke /cli-agent-diagnose
