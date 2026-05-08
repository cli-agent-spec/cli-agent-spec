---
name: cli-agent-evaluate-batch
description: Evaluate a CLI tool against multiple CLI Agent Spec failure modes in one run. Accepts a severity filter, part number, or an explicit list of §N identifiers. Skips already-evaluated failure modes (resumable). Emits a scorecard table when done.
license: MIT
compatibility: Requires access to the CLI being evaluated.
---

# CLI Agent Evaluate — Batch

Evaluate a CLI tool against a set of failure modes from the CLI Agent Spec in a single run.

## Inputs

- **CLI** — the CLI tool to evaluate: a command name (e.g. `gh`), a binary path, or enough context to run checks
- **Scope** _(pick one)_:
  - A severity filter: `critical`, `high`, `medium`, or `all`
  - A part number: `part 1` … `part 7`
  - An explicit list of failure mode identifiers: `§1 §2 §10` or `§1,§2,§10`
  - Omitting scope defaults to **`all`**
- **`--refresh`** _(optional)_ — re-evaluate all §N in scope, overwriting existing findings and trace rows; bypasses the resumability skip check

---

## Local Memory Artifacts

Same artifacts as `cli-agent-evaluate`, stored under `evaluations/<cli-name>/`. Run the same CLI through either skill interchangeably.

| File | Content |
|---|---|
| `evaluations/<cli-name>/environment.md` | OS, runtime, binary, version, non-interactive flags, config env vars |
| `evaluations/<cli-name>/findings.md` | One row per evaluated failure mode (§N, title, severity, score, date, notes) |
| `evaluations/<cli-name>/issues.md` | Bugs and cross-challenge observations tagged by §N |
| `evaluations/<cli-name>/trace.md` | Raw check commands, exit codes, stdout/stderr per §N |

---

## Step 0 — Load environment profile

Load `evaluations/<cli-name>/environment.md`.

- **If it exists:** use it and proceed to Step 1.
- **If it does not exist:** run the `cli-agent-onboard` skill for this CLI first, then return to Step 1.

---

## Step 1 — Build the evaluation queue

Failure mode metadata lives in `references/challenges/index.md` relative to this skill's directory.

1. Parse the index table — collect all 71 rows: `§N`, title, severity, part.
2. Apply the scope filter:
   - **Severity filter** (`critical` / `high` / `medium` / `all`): keep rows whose severity matches.
   - **Part filter** (`part N`): keep rows in that numbered part.
   - **Explicit list** (`§1 §2 §10`): keep only the listed §N values. Error on unknown §N.
3. Load `evaluations/<cli-name>/findings.md` if it exists. Load `evaluations/<cli-name>/trace.md` if it exists. Remove from the queue any §N that has a row in **both** findings.md AND a complete block in trace.md — those are fully evaluated. A trace block is complete when it contains both a `**Check command:**` line and a `**Score:**` line. If findings.md has a row for §N but trace.md is missing or has no complete block for that §N (interrupted mid-write), keep §N in the queue and re-evaluate it.
4. To force re-evaluation of already-evaluated §N rows, pass `--refresh`. This bypasses Step 3 and re-evaluates all §N in the queue, overwriting their rows in findings.md and blocks in trace.md.
5. Report the queue to the user before starting:

```
Evaluating <cli> against <N> failure mode(s). <M> already evaluated (findings + trace complete) — skipping.
Queue: §N <title>, §N <title>, …
```

If the queue is empty (all §N fully evaluated and `--refresh` not set), report "All selected failure modes already evaluated. Pass --refresh to re-run." and stop.

---

## Step 2 — Evaluate each failure mode

For each §N in the queue, in index order, run Steps 2a–2f below. These correspond to Steps 1–7 of `cli-agent-evaluate` but merge Steps 1 and 2 into 2a, use a compact per-§N output format (Step 2e), and save findings incrementally after each §N (Step 2f) rather than at the end:

### Step 2a — Read the failure mode file

Failure mode files live in `references/challenges/` relative to this skill's directory. Locate the file for §N using the path from the index.

Extract only:
1. The metadata line — `**Severity:** ... | **Frequency:** ...` immediately after the title
2. The `### Evaluation` section — score table + `**Check:**` line
3. The `### Agent Workaround` section — **only if score < 3** after running the check

### Step 2b — Run the check

The `**Check:**` line inside `### Evaluation` is self-contained. Run it against the CLI using the invocation pattern from the environment profile.

- Use the resolved binary and timeout method from the profile
- Pass `stdin=DEVNULL` (or equivalent) for any command that might prompt
- If the check requires human observation (e.g. "inspect output for X"), describe what was observed and ask the user to confirm before continuing
- If the check times out: record score as `?/3` (indeterminate), write `[timeout after N seconds]` in the trace stderr field, use exit code `124` in the trace. Do not assign 0 — timeout means the check could not complete, not that the CLI failed it

### Step 2c — Assign a score

Match observed behavior against the score table (0–3). If the CLI falls between two levels, assign the lower score. If Step 2b timed out, the score is `?/3` — skip the score table, skip Step 2d, and proceed to Step 2e.

### Step 2d — Read workaround if score < 3

If score is 0, 1, or 2: read the `### Agent Workaround` section. Select applicable techniques. Substitute real values from the environment profile. Omit techniques the CLI already handles.

### Step 2e — Emit the per-failure-mode result

_This is a compact format for batch output. It differs from the single-evaluate Step 6 block (which includes `### Applicable Workaround` and `### Notes` sub-sections). Both contain the same information but the structure is streamlined here for iteration._

```
## §N — <title>
**Severity:** <Critical | High | Medium> | **Score:** <0–3 or ?> / 3
**Check:** <one-line summary of what was observed — or "timed out after N seconds" for ?/3>

<Applicable workaround — omit block if score is 3 or ?/3>

<Notes: bugs, unexpected behaviours, cross-challenge observations — tag each with §N if known>
```

### Step 2f — Save findings and trace incrementally

After each §N, save immediately to findings.md and trace.md; also write to issues.md if bugs were observed. Do not batch — this makes the run resumable on interruption.

**Findings** — if `--refresh` is set and a row for this §N already exists in `evaluations/<cli-name>/findings.md`, replace that row; otherwise append one row. For the Notes column: summarize what was observed; if score is `?/3` (timeout), write `timeout after <N>s — check could not complete`.

```markdown
# Findings — <cli-name>

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §10 | Interactivity & TTY Requirements | Critical | 2/3 | 2026-03-15 | ... |
```

**Trace** — if `--refresh` is set and a block for this §N already exists in `evaluations/<cli-name>/trace.md`, replace that block; otherwise append one block:

```markdown
# Trace — <cli-name>

## §10 — Interactivity & TTY Requirements
**Date:** 2026-03-15
**CLI version:** 1.4.2  ← from `evaluations/<cli-name>/environment.md` Binary section
**Check command:** `bean --help < /dev/null`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
...
```

**stderr** (first 20 lines):
```
...
```
```

Cap stdout and stderr at 20 lines each; add `[truncated — N lines total]` if longer. If the check was user-confirmed rather than executed, write `**Check method:** user-confirmed` and record what was observed.

**Issues** — if bugs or unexpected behaviours were observed, append an entry to `evaluations/<cli-name>/issues.md` as well. For the issues.md format, see Step 7 of `cli-agent-evaluate`.

---

## Step 3 — Emit the final scorecard

After all failure modes in the queue are evaluated, output:

```
## Batch Evaluation Scorecard — <cli-name>

**Scope:** <filter description>
**Evaluated:** <N> failure modes  |  **Already evaluated (skipped):** <M>  |  **Total in findings:** <N+M>
**Date:** <ISO date>

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 3/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §5 | Timeout & Hang Detection | Critical | ?/3 |
…

### Summary
- **Perfect (3/3):** <count> — §N, §N, …
- **Partial (1–2/3):** <count> — §N, §N, …
- **Failing (0/3):** <count> — §N, §N, …
- **Indeterminate (?/3):** <count> — §N, §N, …  _(timed out; excluded from average)_
- **Average score:** <X.X> / 3  _(computed over scored entries only; ?/3 excluded)_
```

Sort the scorecard table: Critical first, then High, then Medium; within each group sort by §N ascending. This sort is for the scorecard output only — do not re-sort `evaluations/<cli>/findings.md`, which retains insertion order for auditability.

---

## Rules

- Always run Step 0 first — never skip environment discovery
- Reuse the existing profile if present; do not re-run discovery
- Save findings after **each** failure mode — never batch writes
- Skip §N rows that are fully evaluated (complete row in findings.md AND complete block in trace.md) — do not re-evaluate unless `--refresh` is passed
- If a check cannot be run automatically (no CLI access), state that, record score as `?/3`, and continue with the next failure mode
- The workaround must use actual values from the environment profile, not generic placeholders
- Do not infer scores from failure mode titles — always run the check
- Use only the four files under `evaluations/<cli-name>/` for persistence
