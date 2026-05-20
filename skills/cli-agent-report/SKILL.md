---
name: cli-agent-report
description: Generate a perspective-specific report from existing CLI evaluation findings. Five modes — dev (fix list for CLI authors), agent-dev (integration guide for agent builders), runtime (operational brief for AI agents), issues (concrete bugs and gaps an agent will hit), all (runs all four, saves to files, generates an index and a LinkedIn post). Requires evaluations/<cli>/findings.md from cli-agent-evaluate or cli-agent-evaluate-batch.
license: MIT
compatibility: Reads local artifacts only — no CLI access required. The `all` mode writes report files to the current directory.
---

# CLI Agent Report — Perspective Lens

Transform evaluation findings into a targeted report for one of four audiences, or generate all at once.

## Inputs

- **CLI** — the CLI tool name (used to locate files under `evaluations/<cli>/`)
- **Mode** _(required)_:
  - `dev` — fix list for the CLI author
  - `agent-dev` — integration guide for the developer building an agent that uses this CLI
  - `runtime` — compact operational brief for an AI agent about to invoke this CLI
  - `issues` — concrete bugs and failure-mode gaps an agent will encounter when using this CLI
  - `all` — runs all four modes, saves each to a file, generates an index and a LinkedIn post
- **Scope** _(optional)_ — same filter syntax as `cli-agent-evaluate-batch`:
  - Severity: `critical`, `high`, `medium`, `all`
  - Part: `part 1` … `part 7`
  - Explicit list: `§1 §2 §10`
  - Omitting scope includes all failure modes present in findings

---

## Local Memory Artifacts

All files live under `evaluations/<cli-name>/`:

| File | Read / Write | Used by |
|---|---|---|
| `evaluations/<cli-name>/findings.md` | Read | All modes — primary data source |
| `evaluations/<cli-name>/issues.md` | Read | `issues`, `all` — observed bugs from evaluation |
| `evaluations/<cli-name>/trace.md` | Read | `issues`, `all` — raw check commands, exit codes, stdout/stderr per §N |
| `evaluations/<cli-name>/readiness.md` | Read | `all` — proactive readiness scores (optional) |
| `evaluations/<cli-name>/environment.md` | Read | `runtime`, `agent-dev`, `all` — actual binary, flags, timeout method |
| `evaluations/<cli-name>/report-dev.md` | Write | `all` — fix list for CLI authors |
| `evaluations/<cli-name>/report-agent-dev.md` | Write | `all` — integration guide for agent builders |
| `evaluations/<cli-name>/report-runtime.md` | Write | `all` — operational brief for AI agents |
| `evaluations/<cli-name>/report-issues.md` | Write | `all` — issues and gaps report |
| `evaluations/<cli-name>/report-index.md` | Write | `all` — index linking all four reports |
| `evaluations/<cli-name>/README.md` | Write | `all` — entry point: summary, key findings, file directory |
| `evaluations/<cli-name>/linkedin.md` | Write | `all` — LinkedIn post draft |
| `evaluations/<cli-name>/x.md` | Write | `all` — X.com thread draft |
| `docs/evaluations/<cli-name>/.pages` | Write | `all` — MkDocs awesome-pages sidebar config (title + nav order) |

Single-mode runs (`dev`, `agent-dev`, `runtime`, `issues`) emit output to the conversation only — they never write files. Only `all` writes files.

---

## Step 0 — Load findings

Load `evaluations/<cli-name>/findings.md`. If it does not exist, stop and tell the user:

```
No findings found for <cli>. Run /cli-agent-evaluate-batch or /cli-agent-audit first.
```

**Files to pre-load per mode** are declared in `config/mode-artifacts.json` (relative to this skill directory). Read the `"read"` list for the chosen mode and load each file that exists. Files listed as optional (readiness.md) may be absent — note when missing but do not stop.

Run `scripts/aggregate_findings.py evaluations/<cli>/findings.md [--scope <scope>]` to obtain structured findings data. All subsequent steps consume this JSON output — no re-reading of findings.md required.

If findings cover < 20% of all 71 failure modes, warn the user: "Findings are partial — run cli-agent-evaluate-batch for a complete picture."

---

## Step 1 — Load supplementary data from challenge files

Challenge files live in `references/challenges/` relative to this skill's directory. Use the index at `references/challenges/index.md` to map §N → file path.

**Sections to load per mode** are declared in `config/mode-sections.json`. For each §N in scope whose score < 3, load only the sections listed under `challenge_sections` for the chosen mode. Do not read any other section.

---

## Step 2 — Render the report

Each mode has a template in `templates/`. Fill every `{{VARIABLE}}` placeholder with the corresponding value. Expand `<!-- REPEAT -->` blocks once per matching row. Honour `<!-- IF -->` guards — omit the section entirely when the condition is false.

### Mode: `dev` — Fix List for CLI Authors

Template: `templates/report-dev.md`

| Placeholder | Source |
|---|---|
| `{{CLI}}` | CLI name from input |
| `{{DATE}}` | Today's ISO date |
| `{{VERSION}}` | Version field from `environment.md` — `"unknown"` if not loaded |
| `{{SCOPE}}` | Scope description string |
| `{{N_FINDINGS}}` | `aggregate_findings` → `summary.all.total` |
| `{{CRIT_*}}` / `{{HIGH_*}}` / `{{MED_*}}` | `aggregate_findings` → `summary.<Severity>.<bucket>` |
| `{{NOTES}}` | `findings` row `notes` field |
| `{{SOLUTIONS_CONTENT}}` | `### Solutions` section from challenge file — verbatim, trimmed |
| `{{PASSING_LIST}}` | `aggregate_findings` → `lists.passing` — comma-separated §N |
| `{{INDET_LIST}}` | `aggregate_findings` → `lists.indeterminate` — comma-separated §N |

Repeat block order: `aggregate_findings` → `sorted.severity_desc_score_asc`.

Requirements block: run `scripts/lookup_requirements.py references/requirements/index.md §N` for each failing §N and insert output verbatim. If the requirements index is not found, omit the block and note it inline.

---

### Mode: `agent-dev` — Integration Guide for Agent Builders

Template: `templates/report-agent-dev.md`

| Placeholder | Source |
|---|---|
| `{{BINARY}}` | `environment.md` resolved binary — placeholder text if not loaded |
| `{{TIMEOUT}}` | `environment.md` timeout value |
| `{{AGENT_WORKAROUND_CONTENT}}` | `### Agent Workaround` section from challenge file — verbatim, trimmed |
| Invariants block | `scripts/build_invariants.py` — see below |

Repeat block order: `aggregate_findings` → `sorted.severity_desc_score_asc`.

**Invocation invariants:** collect the `### Agent Workaround` text for every failing §N, serialize as JSON (`[{"section": N, "workaround_text": "..."}]`), pass to `scripts/build_invariants.py`, and insert the ENV / FLAGS output into the invariants fenced block. If the script finds nothing, write `(none identified)` in the block. Use actual values from `environment.md` when available.

---

### Mode: `runtime` — Operational Brief for AI Agents

Template: `templates/report-runtime.md`

| Placeholder | Source |
|---|---|
| `{{BINARY}}` | `environment.md` resolved binary |
| `{{SCORE_0_LIST}}` / `{{SCORE_1_2_LIST}}` / `{{INDET_LIST}}` / `{{PASSING_LIST}}` | `aggregate_findings` → `lists.*` — comma-separated §N |
| Table rows | Extracted from `### Agent Workaround` sections of failing §N (see assembly rules below) |

Score Summary row order: `aggregate_findings` → `sorted.runtime_severity_section`.

**Assembly rules:**

- **Always Include** — collect every flag and env var from workaround sections that must apply on every invocation (not scenario-specific). One row per distinct flag/var.
- **Never Do** — extract `**Limitation:**` lines and explicit "do not / never / avoid" statements. Rephrase as a concrete forbidden action.
- **Watch in Output** — extract pattern-matching guidance (regex, string literals, stderr patterns). One row per distinct pattern.
- Target ≤ 80 lines total. Omit section if no rows found.

---

### Mode: `issues` — Concrete Problems an Agent Will Hit

Template: `templates/report-issues.md`

| Placeholder | Source |
|---|---|
| `{{BUG_*}}` fields | `evaluations/<cli>/issues.md` entries |
| `{{BUG_DATE}}` / `{{BUG_TRIGGER}}` | Matched §N block in `trace.md` — `**Date:**` and `**Check command:**` fields |
| `{{BUG_IMPACT}}` | Inferred from `**Exit code:**` and stdout/stderr in the trace block |
| `{{NOTES}}` (gap rows) | `findings` row `notes` field — fall back to `### The Problem` only if notes empty |
| `{{FREQUENCY}}` / `{{TOKEN_SPEND}}` / `{{TIME_COST}}` | Challenge file metadata line for each §N |
| `{{WORKAROUND_EXISTS}}` | `Yes` if `### Agent Workaround` present and no `**Limitation:**`; `Partial` if has `**Limitation:**`; `No` if absent |

Gap row order: `aggregate_findings` → `sorted.score_asc_severity_desc` (indeterminate appended last).

If `issues.md` has no entries: write "No issues recorded during evaluation." in the Observed Bugs section body.
If a §N tag in `issues.md` has no matching block in `trace.md`: use date from the issues entry and omit `**Trigger:**`.

---

### Mode: `all` — Full Report Bundle

#### Step A — Generate and save the four reports

Run `dev`, `agent-dev`, `runtime`, and `issues` modes using the pre-loaded artifacts (no re-reading files from disk). Save outputs:

| File | Template |
|---|---|
| `evaluations/<cli>/report-dev.md` | `templates/report-dev.md` |
| `evaluations/<cli>/report-agent-dev.md` | `templates/report-agent-dev.md` |
| `evaluations/<cli>/report-runtime.md` | `templates/report-runtime.md` |
| `evaluations/<cli>/report-issues.md` | `templates/report-issues.md` |

Print `✓ <filename> saved` after each file.

Write `docs/evaluations/<cli>/.pages` from `templates/pages.yaml`, substituting `{{CLI}}` with the CLI name. Create `docs/evaluations/<cli>/` if it does not exist. Print `✓ docs/evaluations/<cli>/.pages saved`.

#### Step B — Generate the index file

Fill `templates/report-index.md` and save as `evaluations/<cli>/report-index.md`.

Readiness section: include if `evaluations/<cli>/readiness.md` exists. Render `/6` rows (Dimensions 1–2 only) for quick depth, all five rows for `/15` depth. Replace the section with the placeholder text if `readiness.md` is absent.

#### Step C — Generate the README

Fill `templates/README.md` and save as `evaluations/<cli>/README.md`.

- Key Findings bullets: pull from `issues.md` (confirmed bugs) first, then score-0 findings. 1–5 bullets; do not pad to 3.
- Omit readiness row from Scores table if `readiness.md` does not exist.
- Omit any file row from the Files table for a file that does not exist.

#### Step D — Generate the LinkedIn post

Fill `templates/linkedin.md` and save as `evaluations/<cli>/linkedin.md`. All format rules are embedded in the template as HTML comments — follow them exactly.

#### Step E — Generate the X.com thread

Fill `templates/x.md` and save as `evaluations/<cli>/x.md`. All format rules are embedded in the template as HTML comments — follow them exactly.

#### Step F — Print completion summary

```
## Bundle complete — <cli>

Files written:
  evaluations/<cli>/README.md            ← entry point
  evaluations/<cli>/report-index.md
  evaluations/<cli>/report-issues.md
  evaluations/<cli>/report-runtime.md
  evaluations/<cli>/report-agent-dev.md
  evaluations/<cli>/report-dev.md
  evaluations/<cli>/linkedin.md           ← gitignored, local use only
  evaluations/<cli>/x.md                  ← gitignored, local use only
  docs/evaluations/<cli>/.pages           ← MkDocs sidebar config

<N files overwritten: list filenames that already existed and were replaced — omit line if none>

Next steps:
1. Publish the report (share the index file or host it)
2. Open `evaluations/<cli>/linkedin.md`, paste the post into LinkedIn; add the report link as the first comment
```

---

## Rules

- Never re-run CLI checks — this skill consumes findings produced by `cli-agent-evaluate` or `cli-agent-evaluate-batch`
- If a §N row in findings has Notes that contradict the generic workaround from the challenge file, prefer the Notes (they are specific observations from the actual evaluation)
- Workaround content must use actual values from `evaluations/<cli>/environment.md` when available — no generic placeholders when real values exist
- Single-mode runs (`dev`, `agent-dev`, `runtime`, `issues`) never write files — output to conversation only
- `all` mode writes nine files (4 reports + index + README + linkedin + x + .pages); linkedin and x are gitignored and for local use only — do not reference them in the README Files table; if any file already exists, overwrite it and note the overwrite in the completion summary
- LinkedIn and X post content must be grounded in actual findings — do not invent scores, bugs, or counts
