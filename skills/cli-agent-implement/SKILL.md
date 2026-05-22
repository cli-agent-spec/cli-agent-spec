---
name: cli-agent-implement
description: Guide implementing the CLI Agent Spec specification in a CLI framework or tool. Audits command naming against Unix conventions, walks through requirements tier-by-tier (REQ-F → REQ-C → REQ-O), generates language-specific schema types, and verifies acceptance criteria. Use when building or extending a CLI framework to support AI agent orchestration.
---

# CLI Agent Implement

## Runtime requirements

- Requires a CLI framework project to implement into
- Requires language-specific codegen tools when schema type generation is requested

Guide an agent through implementing the CLI Agent Spec specification.

## Setup

Read [`references/IMPLEMENTING.md`](references/IMPLEMENTING.md) fully before proceeding.

---

## Step 0 — Audit naming conventions

Read [`references/guides/unix-naming-conventions.md`](references/guides/unix-naming-conventions.md) fully.

Then inspect the target CLI's existing command tree (run `tool --help` and enumerate subcommands):

1. **Corpus alignment** — which row in the "Training Corpus Alignment" table best describes this tool? Name it. This determines which patterns to prioritize.
2. **Verb audit** — for each subcommand, check whether it uses a verb from the "Command Naming" table. Flag non-standard verbs (e.g. `upsert` instead of `apply`, `nuke` instead of `delete`) as recommendations.
3. **Flag audit** — check whether the tool has `--format json`, `--dry-run`, `--output`, `--verbose`, `--no-*` variants. Flag any missing from the "Flags worth inheriting" table that are relevant to the tool's domain.
4. **Override audit** — check whether the tool uses positional arguments, combined short flags, or locale-dependent output. Flag these as issues to address during REQ-F implementation.

Produce a short report:
- **Corpus:** `<name>`
- **Naming gaps:** list of non-standard verbs with suggested replacements
- **Missing flags:** list of high-value flags not yet present
- **Override issues:** list of Unix mechanics inherited that need replacing

This is advisory — naming gaps do not block requirement implementation. Present findings and proceed to Step 1.

---

## Step 1 — Understand the target

Ask (if not already provided):

- What language and framework is being implemented?
- Is this a new framework or extending an existing one?
- Which tier to start from? (Default: always REQ-F first)

---

## Step 2 — Generate schema types

Before implementing requirements, generate language-specific types from the schemas.

Read [`references/schemas/codegen-guide.md`](references/schemas/codegen-guide.md) and follow the workflow for the user's language. Schema files are in `references/schemas/`.

**Post-generation invariant** — code generators do not enforce this:

> `retryable: true` implies `side_effects: "none"` in `ExitCodeEntry`

Add the validation snippet for the user's language from the "Validation after generation" section in the codegen guide.

---

## Step 3 — Implement requirements tier by tier

Read [`references/requirements/index.md`](references/requirements/index.md) for the full list.

Implement in this order:

### Tier 1 — REQ-F (Framework-Automatic)

These establish the exit code table, response envelope, and phase boundary that everything else depends on. Start here.

Suggested order:
1. `REQ-F-001` — `ExitCode` enum, 14-code table
2. `REQ-F-004` — JSON response envelope (`ok`, `data`, `error`, `warnings`, `meta`)
3. `REQ-C-001` — command registration with `exit_codes` map
4. `REQ-C-013` — wire `ExitCode` into `error.code`
5. `REQ-F-002` — validation/execution phase boundary for `ARG_ERROR`
6. Remaining REQ-F requirements

### Tier 2 — REQ-C (Command Contract)

After all REQ-F requirements pass. These are declared by the command author at registration.

### Tier 3 — REQ-O (Opt-In)

Implement as the application needs them — these are explicitly enabled.

---

## Step 4 — Work through each requirement

For each requirement file at `references/requirements/<id>.md`:

1. Read the file — focus on **Acceptance Criteria** and **Wire Format**
2. Implement until every acceptance criterion is satisfied
3. Validate output matches the **Wire Format** JSON exactly
4. Check the **Related** table for dependencies to implement first

---

## Step 5 — Verify

When a tier is complete, re-read every requirement's **Acceptance Criteria** in that tier and confirm each bullet passes. Use **Wire Format** examples as test fixtures.

---

## Rules

- Always run Step 0 naming audit before writing any code — naming changes are cheapest before implementation starts
- Always complete all REQ-F before starting REQ-C
- Load requirement files on demand — do not read all at once
- Use the generated schema types throughout — never use literal integer exit codes
- If the user's language is not in the codegen guide, produce equivalent types manually from the schema field definitions in `references/schemas/`
