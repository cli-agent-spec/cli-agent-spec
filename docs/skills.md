# Skills — Technical Reference

Ten installable agent skills for evaluating CLIs, implementing the spec, and diagnosing failures at the tool-execution layer. Compatible with any [Agent Skills](https://agentskills.io)-enabled agent: Claude Code, Cursor, Gemini CLI, Copilot, and others.

---

## Skill Inventory

| Skill | Category | Purpose |
|-------|----------|---------|
| [`cli-agent-onboard`](../skills/cli-agent-onboard/SKILL.md) | Evaluation pipeline | Profile a CLI tool — detects runtime, binary, non-interactive flags, timeout method |
| [`cli-agent-evaluate`](../skills/cli-agent-evaluate/SKILL.md) | Evaluation pipeline | Score a CLI against one failure mode (0–3), return applicable agent workaround |
| [`cli-agent-evaluate-batch`](../skills/cli-agent-evaluate-batch/SKILL.md) | Evaluation pipeline | Evaluate a CLI across multiple failure modes in one resumable run |
| [`cli-agent-readiness`](../skills/cli-agent-readiness/SKILL.md) | Evaluation pipeline | Score proactive agent-readiness across 5 dimensions (0–15) |
| [`cli-agent-report`](../skills/cli-agent-report/SKILL.md) | Evaluation pipeline | Transform findings into perspective-specific reports for 4 audiences |
| [`cli-agent-audit`](../skills/cli-agent-audit/SKILL.md) | Evaluation pipeline | Autonomous end-to-end pipeline: install → onboard → readiness → evaluate → report |
| [`cli-agent-implement`](../skills/cli-agent-implement/SKILL.md) | Implementation | Guide implementing the spec in a CLI framework, tier by tier |
| [`cli-agent-diagnose`](../skills/cli-agent-diagnose/SKILL.md) | Diagnosis | Classify a failed agent CLI call against the §N taxonomy; return workaround + memory string |
| [`fixlayer-report`](../skills/fixlayer-report/SKILL.md) | Diagnosis | Render a self-contained HTML audit report from a tool-execution trace file |
| [`validate-links`](../skills/validate-links/SKILL.md) | Spec maintenance | Validate cross-links and schema↔requirement symmetry in the spec |

---

## Skill Relations

### Call graph

Skills invoke other skills automatically or on demand. The arrows show delegation, not data flow (data flow is covered in [Artifact Flow](#artifact-flow) below).

```
cli-agent-audit
  ├─→ cli-agent-onboard          (Phase 2 — always)
  ├─→ cli-agent-readiness        (Phase 3 — skippable with --skip-readiness)
  ├─→ cli-agent-evaluate-batch   (Phase 4)
  └─→ cli-agent-report           (Phase 5, mode=all)

cli-agent-evaluate
  └─→ cli-agent-onboard          (Step 0 — auto-invoked if environment.md missing)

cli-agent-evaluate-batch
  └─→ cli-agent-onboard          (Step 0 — auto-invoked if environment.md missing)

cli-agent-readiness
  └─→ cli-agent-onboard          (Step 0 — auto-invoked if environment.md missing)

fixlayer-report
  └─→ cli-agent-diagnose         (scripts/diagnose.py --explain)
```

`cli-agent-implement`, `cli-agent-diagnose`, and `validate-links` have no skill-level dependencies.

---

### Artifact flow

All evaluation artifacts live under `evaluations/<cli-name>/`. Skills read and write specific files; no skill reads another skill's files at runtime (they share the directory, not live state).

```
cli-agent-onboard
  writes → evaluations/<cli>/environment.md

cli-agent-evaluate  /  cli-agent-evaluate-batch
  reads  → evaluations/<cli>/environment.md
  writes → evaluations/<cli>/findings.md
  writes → evaluations/<cli>/issues.md
  writes → evaluations/<cli>/trace.md

cli-agent-readiness
  reads  → evaluations/<cli>/environment.md
  writes → evaluations/<cli>/readiness.md

cli-agent-report (mode=all)
  reads  → evaluations/<cli>/findings.md
  reads  → evaluations/<cli>/issues.md
  reads  → evaluations/<cli>/trace.md
  reads  → evaluations/<cli>/readiness.md       (optional)
  reads  → evaluations/<cli>/environment.md
  writes → evaluations/<cli>/report-dev.md
  writes → evaluations/<cli>/report-agent-dev.md
  writes → evaluations/<cli>/report-runtime.md
  writes → evaluations/<cli>/report-issues.md
  writes → evaluations/<cli>/report-index.md
  writes → evaluations/<cli>/README.md
  writes → evaluations/<cli>/linkedin.md        (gitignored)
  writes → evaluations/<cli>/x.md               (gitignored)
  writes → docs/evaluations/<cli>/.pages
```

Single-mode `cli-agent-report` runs (`dev`, `agent-dev`, `runtime`, `issues`) emit output to the conversation only — they never write files.

---

### Artifact reference table

| File | Produced by | Consumed by |
|------|-------------|-------------|
| `environment.md` | `cli-agent-onboard` | `cli-agent-evaluate`, `cli-agent-evaluate-batch`, `cli-agent-readiness`, `cli-agent-report` |
| `findings.md` | `cli-agent-evaluate`, `cli-agent-evaluate-batch` | `cli-agent-report` |
| `issues.md` | `cli-agent-evaluate`, `cli-agent-evaluate-batch` | `cli-agent-report` (modes: `issues`, `all`) |
| `trace.md` | `cli-agent-evaluate`, `cli-agent-evaluate-batch` | `cli-agent-report` (modes: `issues`, `all`) |
| `readiness.md` | `cli-agent-readiness` | `cli-agent-report` (modes: `all`) |
| `report-dev.md` | `cli-agent-report` | humans — CLI authors |
| `report-agent-dev.md` | `cli-agent-report` | humans — agent builders |
| `report-runtime.md` | `cli-agent-report` | AI agents at runtime |
| `report-issues.md` | `cli-agent-report` | agent users — concrete bug list |
| `report-index.md` | `cli-agent-report` | humans — navigation |
| `README.md` | `cli-agent-report` | humans — entry point |
| `linkedin.md` | `cli-agent-report` | humans — social post draft |
| `x.md` | `cli-agent-report` | humans — social post draft |

---

## Skill Descriptions

### `cli-agent-onboard`

**Role:** foundation. Every evaluation skill reads `environment.md` before running any check. Run once per CLI per machine; re-run with `--force` to refresh.

**Steps:** reads agent docs (`AGENTS.md`, `CODING_AGENTS.md`, `README.md`) → detects runtime and toolchain from manifest files → locates and verifies the binary → detects OS timeout method → discovers non-interactive and output-format flags → saves `evaluations/<cli>/environment.md`.

**Invoked automatically by:** `cli-agent-evaluate`, `cli-agent-evaluate-batch`, `cli-agent-readiness` (Step 0) and `cli-agent-audit` (Phase 2).

---

### `cli-agent-evaluate`

**Role:** targeted single-failure-mode evaluation. Use when investigating one specific §N, or when building a custom evaluation sequence.

**Steps:** loads environment profile → locates failure mode file → reads `### Evaluation` section → runs `**Check:**` command → assigns score 0–3 (or `?/3` on timeout) → reads `### Agent Workaround` if score < 3 → emits structured result block → saves to `findings.md` and `trace.md`.

**Score semantics:** 3 = fully passing, 0 = failing, `?/3` = check timed out (indeterminate — not a fail).

**Resumable:** skips §N rows already present in `findings.md` unless `--refresh` is passed.

---

### `cli-agent-evaluate-batch`

**Role:** efficient multi-failure-mode evaluation in a single run. Accepts a severity filter (`critical`, `high`, `medium`, `all`), a part number (`part 1`–`part 7`), or an explicit §N list.

**Difference from `cli-agent-evaluate`:** builds a queue from the failure mode index, processes all entries in order, saves findings after each §N (resumable), emits a final scorecard table sorted by severity then §N.

**Resumable:** skips §N rows that have a complete row in `findings.md` AND a complete block in `trace.md`. Re-evaluate with `--refresh`.

---

### `cli-agent-readiness`

**Role:** positive readiness score — measures what the CLI provides, not just what it avoids breaking. Complements `cli-agent-evaluate-batch`.

**Five dimensions (3 points each, 15 total):**

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | Documentation Quality | Can an agent learn correct invocation from docs alone |
| 2 | Self-Description | Does `--schema`/`manifest` return a machine-readable `ManifestResponse` |
| 3 | Pre-built Integrations | MCP server, OpenAPI spec, Claude skill, workflow recipes — with co-versioning check |
| 4 | Setup Reproducibility | Non-interactive idempotent install; dependency manifest; health-check command |
| 5 | Workflow Coverage | Copy-pasteable examples covering CRUD operations, verified by execution |

**Depth:** `quick` evaluates dimensions 1–2 only (score out of 6); `full` evaluates all five.

**Grade scale:** A 13–15 · B 10–12 · C 7–9 · D 4–6 · F 0–3.

---

### `cli-agent-report`

**Role:** translate raw findings into actionable output for a specific audience. Never re-runs CLI checks — reads only pre-existing artifacts.

**Five modes:**

| Mode | Audience | Output |
|------|----------|--------|
| `dev` | CLI authors | Fix list: failing §N → `### Solutions` section from challenge file |
| `agent-dev` | Agent builders | Integration guide: binary invocation, env vars, per-§N workarounds, invocation invariants |
| `runtime` | AI agents | Compact brief: always-include flags, never-do actions, output patterns to watch |
| `issues` | Agent users | Concrete bugs from `issues.md` + gap list from failing §N |
| `all` | All above | Runs all four modes, writes 8 files, generates index + README + LinkedIn/X drafts |

**`all` mode validation:** runs `scripts/validate_report_bundle.py` before declaring the bundle complete.

---

### `cli-agent-audit`

**Role:** autonomous end-to-end pipeline. Single command, zero human steps in the happy path.

**Six phases:**

| Phase | Action | Halt on failure |
|-------|--------|----------------|
| 0 | Pre-flight — check existing artifacts, determine what to skip | n/a |
| 1 | Install — non-interactive package install, binary verification | yes |
| 2 | Onboard — delegate to `cli-agent-onboard` | yes |
| 3 | Readiness — delegate to `cli-agent-readiness` | no (warn and continue) |
| 4 | Evaluate — delegate to `cli-agent-evaluate-batch` | no (note skipped §N) |
| 5 | Report — delegate to `cli-agent-report mode=all` | no (fix reported errors) |

**Scope:** `critical` (default), `critical+high`, or `all`.

**Flags:** `--skip-install`, `--skip-readiness`, `--refresh`.

**Artifacts produced:** 13 files under `evaluations/<cli>/` — see [cli-agent-audit SKILL.md](../skills/cli-agent-audit/SKILL.md) for the full table.

---

### `cli-agent-implement`

**Role:** guides a CLI framework author through implementing the spec, tier by tier.

**Steps:** naming audit (corpus alignment, verb gaps, flag gaps) → identify target language and framework → generate language-specific types from JSON schemas → implement REQ-F (Framework-Automatic) → REQ-C (Command Contract) → REQ-O (Opt-In) → verify acceptance criteria.

**Key invariant to add post-codegen:** `retryable: true` implies `side_effects: "none"` in `ExitCodeEntry` — code generators do not enforce this; add a validation snippet manually.

**Standalone:** does not read evaluation artifacts or invoke other skills.

---

### `cli-agent-diagnose`

**Role:** post-hoc failure classifier. Given a failed CLI call (command, stdout, stderr, exit code), identifies the matching §N failure mode and returns an actionable workaround, a memory string, and a skill patch.

**Input forms:** failed call visible in the current conversation, a JSON object, or a path to a message history file (OpenAI format, LangSmith, or Langfuse).

**Scripts:**
- `scripts/diagnose.py` — classifier; output is always JSON regardless of exit code
- `scripts/runner.py` — drop-in `subprocess.run` wrapper that applies §N fixes transparently
- `scripts/preflight_hook.py` — Claude Code `PreToolUse` hook that intercepts Bash calls before they run

**Exit codes of `diagnose.py`:** `0` match found · `2` trace too sparse · `3` no match.

**Scope:** tool execution layer only. Reasoning failures, wrong answers, and incorrect domain logic are out of scope — `diagnose.py` returns `no_match` for those.

---

### `fixlayer-report`

**Role:** visual counterpart to `cli-agent-diagnose`. Renders a self-contained HTML audit report in the FixLayer design system from a tool-execution trace file.

**Input formats:** Claude Code PostToolUse hook log (JSONL), OpenAI message history (JSON array), or single-event JSON.

**Script:** `scripts/generate_report.py <trace-file>` — calls `diagnose.py --explain`, collects session stats (tool counts, durations, retries), renders HTML, prints output path.

**Report sections:** verdict strip (pass/fail + §N codes) → match cards (evidence, triggering tool calls, workaround, limitation) → memory strings and skill patches → action items.

**Depends on:** `cli-agent-diagnose` scripts installed alongside it.

---

### `validate-links`

**Role:** spec consistency validator. Detects broken file references and symmetry violations before they accumulate.

**Five checks:**

| # | Check | What it validates |
|---|-------|-----------------|
| 1 | Broken file links | Every relative link in every `.md` file resolves to an existing file |
| 2 | Schema↔requirement symmetry | `Used by` in schema `.md` ↔ `## Schema` link in requirement; bidirectional |
| 3 | Index completeness | Every file linked from `requirements/index.md` and `schemas/index.md` exists; every file in those directories is listed |
| 4 | Content completeness | Challenge and requirement files have all required sections (informational — not a hard error) |
| 5 | Counter consistency | Numbers declared in `README.md`, `AGENTS.md`, `challenges/index.md`, `requirements/index.md` match actual file counts on disk |

**Standalone:** reads spec files only; does not invoke other skills or write any artifacts.

**When to run:** after adding or editing any failure mode, requirement, schema, or guide file.

---

## Quick-Reference: Which Skill to Use

| Goal | Skill |
|------|-------|
| Full autonomous audit of a CLI | `cli-agent-audit` |
| Evaluate one specific §N | `cli-agent-evaluate` |
| Evaluate a set of failure modes | `cli-agent-evaluate-batch` |
| Profile a CLI before evaluation | `cli-agent-onboard` |
| Score what a CLI provides to agents | `cli-agent-readiness` |
| Generate a fix list for the CLI author | `cli-agent-report mode=dev` |
| Generate an integration guide for an agent builder | `cli-agent-report mode=agent-dev` |
| Generate a runtime brief for an AI agent | `cli-agent-report mode=runtime` |
| Generate all reports + index + social drafts | `cli-agent-report mode=all` |
| Understand why a CLI call failed | `cli-agent-diagnose` |
| Visual HTML report from a trace file | `fixlayer-report` |
| Implement the spec in a CLI framework | `cli-agent-implement` |
| Check spec cross-links after editing | `validate-links` |
