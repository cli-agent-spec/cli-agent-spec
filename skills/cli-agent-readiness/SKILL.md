---
name: cli-agent-readiness
description: Score how proactively agent-ready a CLI is across five dimensions — documentation quality, self-description, pre-built integrations, setup reproducibility, and workflow coverage. Complements cli-agent-evaluate-batch (which scores what breaks) with a positive readiness score (what the CLI provides). Requires CLI access and evaluations/<cli>/environment.md from cli-agent-onboard.
license: MIT
compatibility: Requires access to the CLI being evaluated.
---

# CLI Agent Readiness — Proactive Readiness Score

Evaluate what a CLI provides to help agents succeed, not just what it avoids breaking.

## Inputs

- **CLI** — the CLI tool to evaluate: a command name, binary path, or enough context to run it
- **Depth** _(optional, defaults to `full`)_:
  - `quick` — documentation and self-description only (dimensions 1–2); fastest; total scored out of 6
  - `full` — all five dimensions; total scored out of 15

---

## Local Memory Artifacts

| File | Read / Write | Content |
|---|---|---|
| `evaluations/<cli-name>/environment.md` | Read | Binary, runtime, version — from `cli-agent-onboard` |
| `evaluations/<cli-name>/readiness.md` | Write | Readiness scores per dimension, date, notes |

---

## Step 0 — Load environment profile

Load `evaluations/<cli-name>/environment.md`. If it does not exist, run `cli-agent-onboard` first, then return here.

The version field from the profile is used in every output header and the readiness artifact.

---

## Step 1 — Evaluate five dimensions

Score each dimension 0–3. For `full` depth: evaluate all five before emitting any output. For `quick` depth: evaluate only dimensions 1 and 2 (skip dimensions 3–5 entirely — do not run their checks) before emitting output.

---

### Dimension 1 — Documentation Quality

**What it measures:** whether an agent can learn how to use this CLI correctly from its docs, without trial and error.

Check in order:

1. Look for `AGENTS.md` in CWD. If found, read it.
2. Look for `CODING_AGENTS.md` in CWD. If found, read it.
3. Read `README.md` (CWD) for agent-relevant sections — invocation examples, env vars, non-interactive flags.
4. Run `<binary> --help` and compare against doc content: spot-check 3 flags or env vars that appear in docs — confirm each is present in `--help` output. "Correctly described" means the flag exists and covers the same use case, not word-for-word match. Record functional discrepancies only (flag absent, or does the opposite of what docs say). Wording differences alone do not reduce the score.

**Score table:**

| Score | Criteria |
|---|---|
| 0 | No `AGENTS.md`; README has no agent-relevant content (no invocation examples, no env vars, no flags) |
| 1 | README has CLI usage examples but no agent-specific guidance; no `AGENTS.md` |
| 2 | `AGENTS.md` exists with partial content — canonical invocation OR non-interactive flags OR env vars, but not all three |
| 3 | `AGENTS.md` complete: canonical invocation + non-interactive flags + env vars + input conventions; spot-check passes (docs match `--help`) |

**Notes to record:** which fields are missing from `AGENTS.md`; any discrepancy between docs and `--help`.

---

### Dimension 2 — Self-Description

**What it measures:** whether an agent can load a machine-readable description of the CLI's commands, flags, and exit codes without reading prose docs.

Check in order:

1. Run `<binary> --schema` or `<binary> manifest` or `<binary> --manifest` (try all; stop at first success).
2. If a response is returned: attempt to parse as JSON. If valid JSON, check against the `ManifestResponse` schema in `references/schemas/manifest-response.json` — verify `commands`, `flags`, and `exit_codes` fields are present.
3. If no schema command works: run `<binary> --help` and assess whether the output is structured enough for an agent to parse flag names and types without ambiguity.

**Score table:**

| Score | Criteria |
|---|---|
| 0 | No schema command; `--help` output is unstructured prose or mixed with progress output |
| 1 | `--help` is structured (flag names, types, defaults readable) but no machine-readable schema |
| 2 | Schema command exists and returns JSON but output is incomplete (missing `exit_codes`, or fewer than 80% of commands described) or does not validate against `ManifestResponse` |
| 3 | Schema command returns valid `ManifestResponse` JSON: all commands described, all flags typed, exit codes mapped; `etag` present |

**Notes to record:** which schema fields are missing or invalid; which schema command was tried. For validation: use `references/schemas/manifest-response.json` (symlinked from the top-level schemas directory) as the ManifestResponse schema definition. An empty `commands` object (zero commands) counts as score 2 (incomplete), not score 3.

---

### Dimension 3 — Pre-built Integrations

**What it measures:** whether the CLI ships integration artifacts an agent can use directly without writing wrapper code, and whether those artifacts are co-versioned with the CLI binary so they cannot drift out of sync.

#### 3a — Presence and functionality

Check in order — look in CWD and subdirectories up to 2 levels deep:

| Artifact | Files / indicators to look for |
|---|---|
| MCP server | `mcp.json`, `mcp-server/`, `claude_mcp_config.json`, `"mcp"` key in `package.json`, MCP package in `pyproject.toml` |
| OpenAPI spec | `openapi.yaml`, `openapi.json`, `swagger.yaml`, `api.yaml` |
| Claude skill / agent config | `.claude/`, `SKILL.md`, `skills/` directory |
| LangChain / LlamaIndex tool | `tools/`, `langchain_tool.py`, `llamaindex_tool.py` |
| Workflow recipes | `recipes/`, `playbooks/`, `examples/agents/`, `workflows/` |

For any MCP server found: run it with `--help` or inspect its schema to confirm it is functional (not just a stub).

#### 3b — Co-versioning check

Co-versioning means the integration artifact is guaranteed to describe the same CLI version that is installed. Check each found artifact:

**Step 1 — Same package?** Check whether the artifact is declared in the same package manifest as the CLI binary (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`). If yes: co-versioned by construction — record as **co-versioned (same package)**.

**Step 2 — Version field match?** If the artifact is a separate package or file, look for an explicit version field inside it (e.g. `version:` in `openapi.yaml`, `framework_version` in a manifest-response, `version` in `mcp.json`). Compare against the CLI binary version from `evaluations/<cli>/environment.md`. If they match exactly: record as **co-versioned (version match)**.

**Step 3 — Lockstep release evidence?** If neither of the above: check for evidence of lockstep releases — same git tag references, a `CHANGELOG` entry that updates both in the same commit, or a CI workflow that releases both together. If found: record as **co-versioned (release evidence)**. If none found: record as **version drift risk**.

**Step 4 — Drift detection?** For any artifact **not confirmed co-versioned** in steps 1–3 (i.e. recorded as "version drift risk"): scan it for command names or flag names that do not appear in `<binary> --help` output. Each mismatch is a confirmed drift instance — record each one. For artifacts confirmed co-versioned in steps 1–3: skip drift scanning — the versioning mechanism prevents drift by construction, and scanning would produce false positives from newly added commands not yet in the artifact's release cycle.

#### Score table

| Score | Criteria |
|---|---|
| 0 | No integration artifacts of any kind |
| 1 | One artifact exists but is incomplete (< 50% of commands covered) or has confirmed drift (mismatched command/flag names) |
| 2 | One complete, working artifact — functional and covers ≥ 80% of commands — but co-versioning is unconfirmed (version drift risk) |
| 3 | One or more complete, working artifacts with confirmed co-versioning (same package, version match, or release evidence) and zero confirmed drift instances |

**Notes to record:** which artifacts were found; co-versioning verdict for each (same package / version match / release evidence / version drift risk); confirmed drift instances (command or flag name mismatches); which artifact was verified functional.

---

### Dimension 4 — Setup Reproducibility

**What it measures:** whether an agent can install and verify the CLI in a fresh environment without human intervention.

Check in order:

1. Look for documented install instructions in `AGENTS.md`, `CODING_AGENTS.md`, `README.md`.
2. Identify whether the documented install command is non-interactive (no prompts, no browser flows).
3. Check whether dependencies are explicitly declared in a manifest (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`).
4. Confirm `<binary> --version` exits 0 and returns a parseable version string (already verified by onboard).
5. Run the install command a second time (if safe and non-destructive) and confirm it completes without error — testing idempotency.

**Score table:**

| Score | Criteria |
|---|---|
| 0 | No install instructions; or install requires interactive steps (browser OAuth, wizard prompts) |
| 1 | Install instructions exist and are non-interactive, but not idempotent or dependencies are implicit |
| 2 | Non-interactive idempotent install documented; dependencies declared in manifest; `--version` verifies |
| 3 | All of score-2 criteria, plus: install instructions are in `AGENTS.md` (not just README), and a health-check command is documented (e.g. `<binary> doctor` or `<binary> --version`) |

**Notes to record:** the exact install command; whether a second run succeeded; which dependency manifest was found.

---

### Dimension 5 — Workflow Coverage

**What it measures:** whether an agent can complete realistic end-to-end tasks using documented commands and examples, without improvising.

Check in order:

1. Collect all example commands from `AGENTS.md`, `README.md`, recipe/workflow files, and `--help` output.
2. Assess whether examples are: (a) copy-pasteable as-is, (b) cover create/read/update/delete operations where applicable, (c) include the non-interactive flags needed for agent use.
3. Look for multi-step workflow documentation (sequences of commands that accomplish a complete task).
4. Run one documented example verbatim (the simplest read-only one) and confirm it exits 0 and produces expected output.

**Score table:**

| Score | Criteria |
|---|---|
| 0 | No examples; agent must discover commands entirely by trial and error |
| 1 | Basic examples exist but require human-specific values (no placeholders explained), or omit non-interactive flags |
| 2 | Examples are copy-pasteable with clear placeholder substitution; cover at least read and create operations; include non-interactive flags |
| 3 | All of score-2, plus: at least one documented multi-step workflow an agent can follow verbatim; one example verified by execution |

**Notes to record:** which example was run and its output; which operations have no examples; any examples that fail when run.

---

## Step 2 — Emit the result

Use the appropriate template for the depth evaluated:

**Full depth (`full`):**

```
# CLI Agent Readiness Report — <cli>

**Generated:** <ISO date>
**CLI version:** <version from environment profile>
**Depth:** full

## Readiness Score: <total>/15  [<grade>]

| Dimension | Score | Key finding |
|---|---|---|
| 1. Documentation Quality | X/3 | <one clause — what's present or missing> |
| 2. Self-Description | X/3 | <one clause> |
| 3. Pre-built Integrations | X/3 | <one clause> |
| 4. Setup Reproducibility | X/3 | <one clause> |
| 5. Workflow Coverage | X/3 | <one clause> |

Grade scale: A 13–15 · B 10–12 · C 7–9 · D 4–6 · F 0–3
```

**Quick depth (`quick`) — dimensions 1–2 only:**

```
# CLI Agent Readiness Report — <cli>

**Generated:** <ISO date>
**CLI version:** <version from environment profile>
**Depth:** quick (dimensions 1–2 only)

## Readiness Score: <total>/6  [<grade>]

| Dimension | Score | Key finding |
|---|---|---|
| 1. Documentation Quality | X/3 | <one clause — what's present or missing> |
| 2. Self-Description | X/3 | <one clause> |

Grade scale (quick): A 6 · B 5 · C 4 · D 3 · F 0–2

_Run with `depth=full` to evaluate Pre-built Integrations, Setup Reproducibility, and Workflow Coverage._
```

**Both depths continue with (append after the score table):**

```
---

## Dimension Details

### 1. Documentation Quality — <X>/3

<findings: what was found, what was missing, any doc/--help discrepancies>

### 2. Self-Description — <X>/3

<findings: which schema command was tried, what it returned, what was missing>
```

**Full depth only — append dimensions 3–5 (omit entirely for quick depth):**

```
### 3. Pre-built Integrations — <X>/3

<findings: which artifacts were found, which were verified, which appear stale>

### 4. Setup Reproducibility — <X>/3

<findings: install command, idempotency result, dependency manifest>

### 5. Workflow Coverage — <X>/3

<findings: which example was run, its result, which operations lack examples>

---

## Recommended Improvements  _(full depth only — omit this entire section for quick depth)_

### <Dimension name> — currently <X>/3

**To reach <X+1>/3:** <concrete, actionable step — one sentence>
**To reach 3/3:** <concrete, actionable step — one sentence>

---

## Related failure modes

These failure modes from the CLI Agent Spec are related to readiness gaps found above:

| §N | Title | Severity | Readiness dimension |
|---|---|---|---|
| §44 | Agent Knowledge Packaging Absence | Medium | Documentation Quality |
| §52 | Recursive Command Tree Discovery Cost | Medium | Self-Description |
| §21 | Schema & Help Discoverability | Medium | Self-Description |
| §47 | MCP Wrapper Schema Staleness | High | Pre-built Integrations |
| §20 | Environment & Dependency Discovery | Medium | Setup Reproducibility |
```

_Include only §N rows that are relevant given the actual findings._

---

## Step 3 — Save the readiness artifact

Save as `evaluations/<cli-name>/readiness.md`:

```markdown
# Readiness — <cli-name>

**CLI version:** <version>
**Date:** <ISO date>
**Depth:** <full | quick>
**Total:** <X>/15  [<grade>]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | X/3 | <one-liner> |
| Self-Description | X/3 | <one-liner> |
| Pre-built Integrations | X/3 | <one-liner — omit row for quick depth> |
| Setup Reproducibility | X/3 | <one-liner — omit row for quick depth> |
| Workflow Coverage | X/3 | <one-liner — omit row for quick depth> |
```

For `quick` depth: replace `/15` with `/6` and use the quick grade scale (A 6 · B 5 · C 4 · D 3 · F 0–2) in the **Total:** line; omit the Pre-built Integrations, Setup Reproducibility, and Workflow Coverage rows entirely.

If `evaluations/<cli-name>/readiness.md` already exists, insert the new entry after the `# Readiness — <cli-name>` header line and before the previous entry — the artifact is a log, newest first. The header line appears only once at the top of the file. Separate entries with `---`. Example with two entries:

```markdown
# Readiness — <cli-name>

**CLI version:** 2.5.0
**Date:** 2026-05-08
**Depth:** full
**Total:** 10/15  [B]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 3/3 | AGENTS.md complete |
| Self-Description | 2/3 | Schema missing exit codes |
| Pre-built Integrations | 2/3 | OpenAPI present, version drift risk |
| Setup Reproducibility | 2/3 | Non-interactive install documented |
| Workflow Coverage | 1/3 | No multi-step workflow examples |

---

**CLI version:** 2.4.1
**Date:** 2026-04-15
**Depth:** full
**Total:** 8/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 2/3 | AGENTS.md missing env vars |
| Self-Description | 1/3 | No schema command |
| Pre-built Integrations | 2/3 | OpenAPI present |
| Setup Reproducibility | 2/3 | Install documented but not idempotent |
| Workflow Coverage | 1/3 | Basic examples only |
```

---

## Rules

- Always load the environment profile first — never skip Step 0
- Do not infer scores from filenames alone — read the content to verify quality
- If a check cannot be run (no CLI access, install not possible), record the dimension as `?/3` and explain why; do not assign 0
- Recommended improvements must be concrete — "add AGENTS.md" not "improve documentation"
- For `quick` depth: skip dimensions 3–5 entirely (no checks run); emit output and save artifact with only dimensions 1–2 scored; report total as `<X>/6`; omit dimensions 3–5 from the Dimension Details section and from the Recommended Improvements section
- Never overwrite `evaluations/<cli-name>/environment.md` — it is owned by the onboard skill
