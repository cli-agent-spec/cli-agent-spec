# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **specification** (not an implementation) for building CLI tools that work reliably under AI agent orchestration. It defines 67 failure modes, 147 requirements across 3 tiers, 4 canonical JSON schemas, analysis of 12 existing frameworks, and design guides for CLI authors.

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

**Onboard a CLI tool before evaluation (run once per CLI):**
```
/cli-agent-onboard
```

**Evaluate a CLI against a single failure mode:**
```
/cli-agent-evaluate
```

**Guide implementing the spec in a CLI framework:**
```
/cli-agent-implement
```

## Architecture

### Directories

- `challenges/` — 67 failure modes in 7 parts (01=critical ecosystem, 02=execution, 03=security, 04=output, 05=environment, 06=errors, 07=observability). Failure modes are referenced as `§N`.
- `requirements/` — 147 requirements in 3 tiers: `f-NNN` (Framework-Automatic), `c-NNN` (Command Contract), `o-NNN` (Opt-In). Referenced as `REQ-{TIER}-{NNN}`.
- `schemas/` — 4 canonical JSON Schema draft-07 types, each with a `.json` (machine) and `.md` (human) companion: `exit-code`, `exit-code-entry`, `response-envelope`, `manifest-response`.
- `research/` — per-framework analysis (argparse, click, clap, cobra, typer, commander-js, pydantic, MCP, OpenAPI, etc.).
- `guides/` — design guides for CLI authors: positive conventions that cannot be expressed as enforceable requirements. See `guides/index.md`.
- `comparison-matrix.md` — 67 failure modes × 12 frameworks coverage table.

### Requirement tiers

| Tier | Prefix | Meaning |
|------|--------|---------|
| Framework-Automatic | `REQ-F` | Enforced by the framework without command author action |
| Command Contract | `REQ-C` | Declared by the command author at registration |
| Opt-In | `REQ-O` | Explicitly enabled by the application |


## Styling rules (apply to all documents)

1. **No trailing periods** in list items, table cells, or blockquotes. Periods only in prose paragraphs.
2. **Inline code** for all flag names, field names, constants, filenames, command invocations, and schema `$id` values.
3. **Verb-first** labels in `## Related` tables. Allowed verbs: `Provides` · `Consumes` · `Enforces` · `Specializes` · `Composes` · `Aggregates` · `Wraps` · `Sources` · `Exposes` · `Extends`
4. **Present tense** in all `description` fields.
5. **Agent-readable descriptions** (in `ExitCodeEntry`, `FlagEntry`, `ErrorDetail`): state the condition, ≤120 chars, no trailing period.

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
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
