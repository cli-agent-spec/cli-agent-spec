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
| `evaluations/<cli-name>/environment.md` | Read | `runtime`, `all` — actual binary, flags, timeout method |
| `evaluations/<cli-name>/report-dev.md` | Write | `all` — fix list for CLI authors |
| `evaluations/<cli-name>/report-agent-dev.md` | Write | `all` — integration guide for agent builders |
| `evaluations/<cli-name>/report-runtime.md` | Write | `all` — operational brief for AI agents |
| `evaluations/<cli-name>/report-issues.md` | Write | `all` — issues and gaps report |
| `evaluations/<cli-name>/report-index.md` | Write | `all` — index linking all four reports |
| `evaluations/<cli-name>/README.md` | Write | `all` — entry point: summary, key findings, file directory |
| `evaluations/<cli-name>/linkedin.md` | Write | `all` — LinkedIn post draft |
| `evaluations/<cli-name>/x.md` | Write | `all` — X.com thread draft |

Single-mode runs (`dev`, `agent-dev`, `runtime`, `issues`) emit output to the conversation only — they never write files. Only `all` writes files.

---

## Step 0 — Load findings

Load `evaluations/<cli-name>/findings.md`. If it does not exist, stop and tell the user:

```
No findings found for <cli>. Run /cli-agent-evaluate-batch or /cli-agent-audit first.
```

Apply the scope filter if provided — keep only the rows whose §N matches. Report how many rows are in scope.

For `all` mode, `runtime` single-mode, and `agent-dev` single-mode: also pre-load `evaluations/<cli-name>/environment.md` (used for version numbers, invocation invariants, and binary details).

For `issues` single-mode: also pre-load `evaluations/<cli-name>/issues.md` and `evaluations/<cli-name>/trace.md` (used for check evidence and trigger extraction).

For `all` mode additionally: pre-load `evaluations/<cli-name>/readiness.md` (optional — omit readiness section if missing), `evaluations/<cli-name>/issues.md`, and `evaluations/<cli-name>/trace.md`.

---

## Step 1 — Load supplementary data from challenge files

Challenge files live in `references/challenges/` relative to this skill's directory. Use the index at `references/challenges/index.md` to map §N → file path.

For each §N in scope, load only the sections needed by the chosen mode:

| Mode | Sections to read | Extra artifact |
|---|---|---|
| `dev` | `### Solutions` only | — |
| `agent-dev` | `### Agent Workaround` only | — |
| `runtime` | `### Agent Workaround` only (for score < 3 rows) | `evaluations/<cli>/environment.md` |
| `issues` | `### The Problem` + metadata line only (for score < 3 rows) | `evaluations/<cli>/issues.md` |

Do not read sections not listed above — they are not needed and add cost.

---

## Step 2 — Render the report

### Mode: `dev` — Fix List for CLI Authors

Audience: the person who wrote or maintains the CLI.
Goal: "here is what you must implement, in priority order."

```
# CLI Agent Spec — Fix Report for <cli>

**Generated:** <ISO date>
**CLI version:** <version from evaluations/<cli>/environment.md — "unknown" if profile not loaded>
**Scope:** <filter description>
**In findings:** <N> failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | N | N | N | N |
| High | N | N | N | N |
| Medium | N | N | N | N |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §N — <title>  [<Severity> · <score>/3]

**Gap:** <one sentence: what the CLI currently does or fails to do, drawn from the findings Notes field>

**Solutions:**
<content of ### Solutions from the challenge file — verbatim, trimmed>

**Requirements that address this:**
<For each REQ in references/requirements/index.md whose "Failure mode(s)" column references §N, list:>
- REQ-{TIER}-{NNN} ({Priority}) — <title> [Tier: F = framework handles / C = you declare / O = you opt in]

---
<repeat for each failing §N>

## Already Passing

§N, §N, §N  _(score 3/3 — no action needed)_

## Could Not Verify  _(if any ?/3 entries)_

§N, §N  _(check timed out — behavior unknown; treat as unverified risk)_
```

**How to find requirements for a §N:** Read `references/requirements/index.md`. In the "Failure mode(s)" column, find rows that link to §N. List their IDs and titles. Do not read individual requirement files — the index has enough information.

---

### Mode: `agent-dev` — Integration Guide for Agent Builders

Audience: a developer writing an agent, wrapper, or orchestration layer that calls this CLI.
Goal: "here is every workaround you must code, plus a reusable invocation template."

```
# CLI Agent Integration Guide — <cli>

**Generated:** <ISO date>
**CLI version:** <version from evaluations/<cli>/environment.md — "unknown" if profile not loaded>
**Scope:** <filter description>

## Invocation Invariants

These constraints must hold on every call to <cli>, regardless of language or framework:

```
binary:  <resolved binary from environment profile>
stdin:   closed (DEVNULL / equivalent)
timeout: <value from environment profile>s
env:     <ENV_VAR=value>  # §N — <why>
         <ENV_VAR=value>  # §N — <why>
flags:   <--flag>         # §N — <why>
         <--flag>         # §N — <why>
```

<If environment profile is not found, use descriptive placeholders and state: "Load evaluations/<cli>/environment.md for actual values.">

---

## Per-Failure-Mode Workarounds  _(score < 3, sorted: severity desc, score asc)_

### §N — <title>  [<Severity> · <score>/3]

**Gap:** <one sentence from findings Notes>

**Workaround:**
<content of ### Agent Workaround from the challenge file — verbatim, trimmed>

---
<repeat for each failing §N>

## No Action Needed

§N, §N, §N  _(score 3/3)_

## Could Not Verify  _(if any ?/3 entries)_

§N, §N  _(check timed out — treat as unverified risk; consider adding retry logic or manual observation)_
```

**Invocation invariants assembly rules:**
- `env` entries: collect every env var set in any `### Agent Workaround` section across all failing §N rows
- `flags` entries: collect every flag recommended in any `### Agent Workaround` section across all failing §N rows
- Deduplicate — if two workarounds recommend the same flag or var, list it once with all §N references in the comment on the same line: `# §10,§20 — <why>`. Do not repeat the flag on multiple lines
- Use actual values from `evaluations/<cli>/environment.md` if loaded; use descriptive placeholders if not

---

### Mode: `runtime` — Operational Brief for AI Agents

Audience: an AI agent about to invoke this CLI — possibly reading this brief as part of its context.
Goal: compact, decision-table format. No prose. Directly actionable.

Load `evaluations/<cli>/environment.md` for the actual binary and flags. If it is not found, state "environment profile not found — values below are placeholders."

```
# Runtime Brief — <cli>
Generated: <ISO date> | CLI version: <version> | Findings: <N> failure modes | Scope: <filter>

## Invoke As

<exact resolved invocation, e.g. `gh` or `uv run bean`>

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| <flag> | <why — one clause> | §N |
| <ENV_VAR=value> | <why> | §N |

## Never Do

| Action | Risk | §N |
|---|---|---|
| <action, e.g. "call without --no-pager"> | <consequence — one clause> | §N |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| <string or regex> | <what it signals> | <what to do — strip / retry / abort / log> |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes | Critical | 3/3 |
| §10 | Interactivity | Critical | 1/3 |
…

**Worst gaps (score 0):** §N, §N  
**Partial (score 1–2):** §N, §N  
**Indeterminate (?/3 — timed out):** §N, §N  
**Passing:** §N, §N
```

**Runtime brief assembly rules:**

- **Always Include** — collect every flag and env var from `### Agent Workaround` sections of failing §N rows. Keep only entries that must be applied on every invocation (not just in specific scenarios). One row per distinct flag/var.
- **Never Do** — extract `**Limitation:**` lines and any explicit "do not" / "never" / "avoid" statements from workaround sections. Rephrase as a concrete forbidden action.
- **Watch in Output** — extract pattern-matching guidance (regex, string literals, stderr patterns) from workaround sections. One row per distinct pattern.
- Score summary: include all §N in scope, sorted Critical → High → Medium, within group §N ascending.
- Omit prose headers, bullet explanations, and implementation context — this brief must stay under 80 lines total where possible.

---

### Mode: `issues` — Concrete Problems an Agent Will Hit

Audience: an AI agent (or its builder) planning a task that involves this CLI.
Goal: "here is every problem you will actually encounter — observed bugs first, then scored gaps."

This mode surfaces two layers:

1. **Observed bugs** — entries from `evaluations/<cli>/issues.md`, written during evaluation when unexpected behaviour was found
2. **Scored gaps** — failure modes where score < 3, meaning the CLI does not fully handle the situation

Use the pre-loaded `issues.md` and `trace.md` from Step 0. If `issues.md` was not found or contains no entries (only the header line), note "No issues recorded during evaluation" and continue with scored gaps only. `trace.md` provides check commands, exit codes, and exact dates for each gap.

```
# Issues Report — <cli>

**Generated:** <ISO date>
**CLI version:** <version from evaluations/<cli>/environment.md — "unknown" if profile not loaded>
**Scope:** <filter description>
**Findings in scope:** <N> failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### <§N tag> — <bug headline from issues artifact>

**Discovered during:** §N evaluation — <date from issues entry>
**Symptom:** <description from issues artifact — verbatim if concise, summarized if long>
**Impact:** <one clause — what breaks for an agent: hang / wrong exit code / parse failure / data loss / etc.>
**Trigger:** <the exact command or condition that causes it, if recorded>

---
<repeat for each entry in evaluations/<cli>/issues.md that falls within scope>

---

## Failure-Mode Gaps  _(score 0–2, sorted: score asc, severity desc; ?/3 entries listed last)_

These are not confirmed bugs but verified gaps — the CLI does not meet the bar for reliable agent use. `?/3` entries (check timed out) are included at the end with `**What fails:** check timed out — behavior unknown`.

### §N — <title>  [<Severity> · score <X>/3]

**What fails:** <one sentence drawn from findings Notes — what the agent experiences, not what the spec says>
**Frequency:** <from challenge metadata line — Common / Situational / Very Common>
**Token/time cost when it triggers:** Token Spend: <X> · Time: <X>  _(from metadata)_
**Workaround exists:** Yes / Partial / No  _(Yes if ### Agent Workaround has actionable steps; Partial if it has a Limitation that reduces coverage; No if none)_

---
<repeat for each §N with score < 3 in scope>

---

## Passing  _(score 3/3 — safe to use without special handling)_

§N <title>, §N <title>, …

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | N | §N, §N |
| Score 0 — complete failure | N | §N, §N |
| Score 1 — major gap | N | §N, §N |
| Score 2 — minor gap | N | §N, §N |
| Score 3 — passing | N | §N, §N |
| Indeterminate (?/3 — timed out) | N | §N, §N |

**Highest-risk combination:** <call out the most dangerous score-0 Critical row, or the most impactful observed bug — one sentence>
```

**Issues mode trace.md field mapping:**

Data from `evaluations/<cli>/trace.md` populates the observed bug sections as follows:
- `**Trigger:**` ← `**Check command:**` line from the matching §N trace block
- `**Discovered during:**` date ← `**Date:**` line from the matching §N trace block
- `**Impact:**` ← inferred from `**Exit code:**` and stdout/stderr in the trace block (e.g. exit 0 on error = "agent has no failure signal")

If the §N tag in issues.md does not match any block in trace.md, use the date from the issues.md entry and omit `**Trigger:**`.

**Issues mode assembly rules:**

- Sort observed bugs before scored gaps — bugs are confirmed, gaps are potential
- Within scored gaps: sort score ascending (0 first), then severity descending (Critical before High) — worst-and-most-severe first
- `**What fails:**` must describe the agent's experience, not the spec language. Use the findings Notes field as the primary source; fall back to `### The Problem` from the challenge file only if Notes is empty
- `**Workaround exists:**` — read the `### Agent Workaround` section title only (do not read content) to determine if one is present; check for a `**Limitation:**` line to determine Partial
- Scope filter applies to both `evaluations/<cli>/issues.md` entries (match by §N tag) and findings rows
- If `evaluations/<cli>/issues.md` entries have no §N tag, include them in Observed Bugs without scope filtering and note they are untagged

---

### Mode: `all` — Full Report Bundle

Audience: anyone publishing or sharing a complete evaluation.
Goal: run all four modes, save each to a file, generate an index, and produce a LinkedIn post draft.

#### Step A — Generate and save the four reports

Run the `dev`, `agent-dev`, `runtime`, and `issues` modes in full (respecting any scope filter). Use the artifacts pre-loaded in Step 0 — do not re-read files from disk for each sub-mode. Save each to a file:

| File | Contents |
|---|---|
| `evaluations/<cli>/report-dev.md` | Output of `dev` mode |
| `evaluations/<cli>/report-agent-dev.md` | Output of `agent-dev` mode |
| `evaluations/<cli>/report-runtime.md` | Output of `runtime` mode |
| `evaluations/<cli>/report-issues.md` | Output of `issues` mode |

Print a one-line status after each file is saved: `✓ <filename> saved`.

#### Step B — Generate the index file

Save as `evaluations/<cli>/report-index.md`:

```markdown
# CLI Agent Evaluation — <cli>

**Generated:** <ISO date>  
**CLI version:** <version from evaluations/<cli>/environment.md — "unknown" if profile not loaded>  
**Scope:** <filter description>  
**Failure modes evaluated:** <N> of 71 _(scope: <filter description, e.g. "Critical" or "all">)_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | N | N | N | N |
| High | N | N | N | N |
| Medium | N | N | N | N |
| **All** | **N** | **N** | **N** | **N** |

**Average score:** X.X / 3

## Readiness Score

<If evaluations/<cli>/readiness.md exists, include this section; otherwise omit it entirely and replace with: "_Readiness not evaluated. Run `/cli-agent-readiness` to populate this section._">

<If readiness.md shows `/6` (quick depth): render only Dimensions 1–2 rows with total `/6`. If it shows `/15` (full depth): render all five rows.>

| Dimension | Score |
|---|---|
| Documentation Quality | X/3 |
| Self-Description | X/3 |
| Pre-built Integrations | X/3 |
| Setup Reproducibility | X/3 |
| Workflow Coverage | X/3 |
| **Total** | **X/15 [grade]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

<3–5 bullet points drawn from the issues report — the highest-impact bugs and score-0 gaps, one clause each>

## Observed Bugs

<N> bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
```

#### Step C — Generate the README

Save as `evaluations/<cli>/README.md`. This is the entry point for anyone browsing the evaluation folder — it must be self-contained and readable with no prior context.

```markdown
# <cli> — CLI Agent Evaluation

> Evaluated against the [CLI Agent Spec](https://github.com/anthropics/cli-agent-ergonomics) — a specification defining 71 failure modes for CLI tools used under AI agent orchestration.

**CLI version:** <version>  
**Evaluated:** <ISO date>  
**Scope:** <filter description> (<N> of 71 failure modes)

## Scores

| Metric | Result |
|---|---|
| Failure mode score | <avg>/3 — <pass> passing · <partial> partial · <fail> failing |
| Readiness score | <X>/15 [<grade>] |
| Observed bugs | <N> confirmed during live evaluation |
| Worst gaps | <§N title (score)>, <§N title (score)> |

## Key Findings

- <Most critical issue — one sentence, what the agent experiences>
- <Second critical issue>
- <Third issue or readiness gap>

## Files

| File | What it is |
|---|---|
| [report-index.md](report-index.md) | Full scorecard — all failure modes, readiness breakdown, links to all reports |
| [report-issues.md](report-issues.md) | Concrete bugs and gaps agents will hit when using this CLI as-is |
| [report-runtime.md](report-runtime.md) | Compact operational brief — what to set, what to avoid, what to watch for |
| [report-agent-dev.md](report-agent-dev.md) | Integration guide — invocation invariants and per-gap workarounds for agent developers |
| [report-dev.md](report-dev.md) | Fix list for CLI authors — what to implement, mapped to spec requirements |
| [linkedin.md](linkedin.md) | LinkedIn post draft for sharing findings with the agent engineering community |
| [findings.md](findings.md) | Raw scorecard — one row per evaluated failure mode |
| [issues.md](issues.md) | Observed bugs recorded during live evaluation |
| [trace.md](trace.md) | Audit trail — exact check commands, exit codes, stdout/stderr per §N |
| [environment.md](environment.md) | CLI environment profile — binary path, version, flags, timeout method |
| [readiness.md](readiness.md) | Proactive readiness scores across 5 dimensions |

---

_Generated by cli-agent-audit · CLI Agent Spec_
```

**README writing rules:**
- Key Findings bullets are drawn from `issues.md` (confirmed bugs first) then from score-0 findings — same source as the LinkedIn post, same agent-experience framing. Include 1–5 bullets depending on what was found; do not pad to exactly 3 if fewer exist. If more than 5 qualify, select the highest-severity ones
- All file links are relative — the README must work when the folder is shared or published
- If a file does not exist (e.g. readiness was skipped, so `readiness.md` was never written), omit its row from the Files table
- Omit the readiness row from Scores if `evaluations/<cli>/readiness.md` does not exist

#### Step D — Generate the LinkedIn post

Save as `evaluations/<cli>/linkedin.md`. The post addresses **both agent builders** (developers writing agent code that calls this CLI) and **agent users** (people whose agents invoke this CLI in workflows). Both audiences need to know what is silently breaking right now.

**Post structure (respect LinkedIn's ~3000 character limit; aim for 200–350 words):**

```markdown
# LinkedIn Post — <cli>

<!-- Copy everything between the lines below into LinkedIn -->
---
If your agent uses `<cli>` today, <one-clause hook describing the core risk — e.g. "it's flying blind" / "it's silently failing" / "it's creating duplicates">.

We ran a live evaluation against the real binary — <N> failure modes, every check attempted. Here's what's silently breaking your agent right now:

🔴 <Score-0 gap or confirmed bug — written as what the AGENT experiences, present tense, one sentence>
🔴 <Second score-0 or critical observed bug — agent's experience, present tense>
⚠️ <Score-1 or high-impact score-2 gap — agent's experience, present tense>

Whether you're building agents that call `<cli>` or running workflows that depend on it — these aren't edge cases. They're the default behavior.

<N> Critical failure modes scored 0/3. <M> scored 1–2/3. <If readiness.md exists: "Readiness score: <X>/15." — otherwise omit this sentence.>

Runtime brief, integration guide, issues report, and fix list for the <cli> team — all in the first comment.

<@OrgOrMaintainerLinkedInName — omit line entirely if unknown; see tagging rules below>

#AIAgents #<most-specific-domain-tag>  ← 2–4 total; prefer keywords in body over more tags
---

<!-- First comment to post separately: -->
Full evaluation report: [PASTE LINK HERE]
```

**LinkedIn post writing rules:**
- **Hook from the agent's POV, present tense** — "your agent is experiencing this right now", not "we found that"
- **No "we evaluated X" opener** — start with the reader's problem, not the evaluation process
- **Bullets describe what the agent experiences**, not what the spec says or what the CLI does — write "your agent has no signal that anything went wrong" not "exit code is not semantic"
- **Use 🔴 for score-0 failures, ⚠️ for score-1 or high-impact score-2** — visual severity signal
- **No "what works well" section** — it softens urgency; omit entirely
- **Both-audiences line is mandatory** — "whether you're building agents… or running workflows" explicitly covers builders and users
- **Numbers near the end**, not the opening — credibility anchor after the hook lands
- **CTA names all report types** — "runtime brief, integration guide, issues report, and fix list for the <cli> team"
- **Maintainer tag (optional):** place one `@mention` on its own line after the CTA, before the hashtags. Tag the org/company LinkedIn page rather than an individual unless a specific maintainer is known. One tag maximum — tagging multiple people reads as spam. The LinkedIn handle is not automatically discoverable — do not infer or guess it from the CLI name, package org, or GitHub handle. If the handle is not explicitly known, omit the line entirely. The tag is an invitation to engage, not an accusation — the post tone is constructive. **LinkedIn-specific only: never add mentions to any other report file.**
- **Hashtags:** 2–4 total; more than 4 reduces engagement. Pick the 1–2 most specific to the CLI's domain (e.g. `#GitHub`, `#Kubernetes`) plus `#AIAgents` or `#CLI` — not both unless the post is short. Keywords in the post body carry more algorithmic weight than tags; do not compensate for weak copy with extra hashtags
- **Comment line is separate** — make clear it is posted as a reply after publishing, not part of the post body
- Do not invent scores or issues — draw only from findings and issues artifacts

#### Step E — Generate the X.com thread

Save as `evaluations/<cli>/x.md`. X posts are 280 characters each. Write a thread of 4–6 posts: a hook post, one post per critical issue, and a closing post with the link.

**Thread structure:**

```markdown
# X Thread — <cli>

<!-- Post each numbered block separately, in order -->

---
**1/**
If your agent uses `<cli>` — <one-clause hook, max 200 chars to leave room for 🧵>.

<one sentence of context — what kind of evaluation, what was tested>

🧵
---

**2/**
🔴 <Score-0 issue — agent's experience, present tense>

<One clarifying sentence if needed. Total post ≤ 280 chars.>
---

**3/**
🔴 <Second score-0 or confirmed bug — agent's experience, present tense. ≤ 280 chars.>
---

**4/**
⚠️ <High-impact score-1 or score-2 gap — agent's experience. ≤ 280 chars.>
---

**5/ (closing)**
<N> Critical gaps. <pass> passing, <fail> at zero.

Full report → [PASTE LINK HERE]

<@XHandle — omit if unknown>

#AIAgents
---
```

**X thread writing rules:**
- **280 characters per post** — count carefully; include spaces, punctuation, and the link (~23 chars when shortened by t.co)
- **Hook post ends with 🧵** — signals a thread; no link in post 1 (algorithm suppresses link-in-first-post)
- **One issue per post** — do not combine two failures in one post; brevity over completeness
- **Short sentences, hard line breaks** — X renders line breaks; use them to create rhythm, not prose paragraphs
- **🔴 for score-0, ⚠️ for score-1/2** — same severity signal as LinkedIn
- **Link in the closing post only** — not in post 1; closing post may also have the @mention and 1–2 hashtags
- **1–2 hashtags maximum** — one niche (`#AIAgents`), one domain-specific if highly relevant; X algorithm now prioritises keywords over tags
- **@mention (optional):** tag the CLI's X/Twitter handle in the closing post — one handle only, same constructive framing as LinkedIn. Omit if the handle is unknown. **X-specific only: never add mentions to any other report file.**
- **No "we evaluated" framing** — start from the user's problem; the thread should feel like a warning, not a press release
- Do not invent scores or issues — draw only from findings and issues artifacts

#### Step F — Print completion summary

After all files are saved:

```
## Bundle complete — <cli>

Files written:
  evaluations/<cli>/README.md            ← entry point
  evaluations/<cli>/report-index.md
  evaluations/<cli>/report-issues.md
  evaluations/<cli>/report-runtime.md
  evaluations/<cli>/report-agent-dev.md
  evaluations/<cli>/report-dev.md
  evaluations/<cli>/linkedin.md
  evaluations/<cli>/x.md

<N files overwritten: list filenames that already existed and were replaced — omit line if none>

Next steps:
1. Publish the report (share the index file or host it)
2. Open `evaluations/<cli>/linkedin.md`, paste the post into LinkedIn
3. After posting, add the report link as the first comment
```

---

## Rules

- Never re-run CLI checks — this skill consumes findings produced by `cli-agent-evaluate` or `cli-agent-evaluate-batch`
- If a §N row in findings has Notes that contradict the generic workaround from the challenge file, prefer the Notes (they are specific observations from the actual evaluation)
- Workaround content must use actual values from `evaluations/<cli>/environment.md` when available — no generic placeholders when real values exist
- If findings cover < 20% of all 71 failure modes, warn the user: "Findings are partial — run cli-agent-evaluate-batch for a complete picture"
- Single-mode runs (`dev`, `agent-dev`, `runtime`, `issues`) never write files — output to conversation only
- `all` mode writes eight files (4 reports + index + README + linkedin + x); if any file already exists, overwrite it and note the overwrite in the completion summary
- LinkedIn post content must be grounded in actual findings — do not invent scores, bugs, or counts
