---
name: cli-agent-evaluate
description: Evaluate a CLI tool against a single CLI Agent Spec failure mode. Runs the failure mode's check, scores 0–3, and provides an applicable agent workaround if the score is below 3. Use this for targeted single-failure-mode evaluation. For multi-failure-mode evaluation use cli-agent-evaluate-batch.
license: MIT
compatibility: Requires access to the CLI being evaluated.
---

# CLI Agent Evaluate — Single Failure Mode

Evaluate a CLI tool against one failure mode from the CLI Agent Spec.

## Inputs

- **Failure mode** — a failure mode identifier: `§N` number, a keyword (e.g. "ansi", "interactivity"), or a file path
- **CLI** — the CLI tool to evaluate: a command name (e.g. `gh`), a binary path, or enough context to run checks
- **`--refresh`** _(optional)_ — re-evaluate this §N even if a row already exists in `evaluations/<cli>/findings.md`; overwrites the existing findings row and trace block for this §N only

---

## Local Memory Artifacts

This skill manages four files per CLI being evaluated, all stored under `evaluations/<cli-name>/`:

| File | Content |
|---|---|
| `evaluations/<cli-name>/environment.md` | OS, runtime, binary, version, non-interactive flags, config env vars |
| `evaluations/<cli-name>/findings.md` | One row per evaluated failure mode (§N, title, severity, score, date, notes) |
| `evaluations/<cli-name>/issues.md` | Bugs and cross-challenge observations tagged by §N, discovered during evaluation |
| `evaluations/<cli-name>/trace.md` | Raw check commands, exit codes, stdout/stderr per §N |

---

## Step 0 — Load environment profile

Load `evaluations/<cli-name>/environment.md`.

- **If it exists:** use it and continue.
- **If it does not exist:** run the `cli-agent-onboard` skill for this CLI first, then return to Step 0. If onboard fails (binary not found, runtime not detected, no PATH entry), halt with the onboard error — do not proceed with an incomplete profile.

After loading the profile, check `evaluations/<cli-name>/findings.md`:

- **If it contains a row for this §N and `--refresh` is not set:** stop — report "§N already evaluated. Pass --refresh to re-run." Do not proceed to Step 1.
- **Otherwise:** proceed to Step 1.

---

## Step 1 — Locate the failure mode file

Failure mode files live in `references/challenges/` relative to this skill's directory.

Find the file by matching `§N` or a keyword against the index:

```
references/challenges/index.md
```

---

## Step 2 — Read only the needed sections from the failure mode file

Do not read the full file. Extract only:

1. The **metadata line** — the `**Severity:** ... | **Frequency:** ...` line immediately after the title
2. The `### Evaluation` section — score table + `**Check:**` line
3. The `### Agent Workaround` section — only if the score ends up below 3

---

## Step 3 — Run the check

The `**Check:**` line inside `### Evaluation` is self-contained. Run it against the CLI using the invocation pattern from the environment profile.

- Use the resolved binary and timeout method from the profile
- Pass `stdin=DEVNULL` (or equivalent) for any command that might prompt
- If the check requires human observation (e.g. "inspect output for X"), describe what was observed and ask the user to confirm
- If the check times out: record score as `?/3` (indeterminate), write `[timeout after N seconds]` in the trace stderr field, use exit code `124` in the trace. Do not assign 0 — timeout means the check could not complete, not that the CLI failed it

---

## Step 4 — Assign a score

If Step 3 timed out, the score is `?/3` (indeterminate) — skip this step and proceed to Step 5. Otherwise, match the observed behavior against the score table (0–3). If the CLI falls between two levels, assign the lower score.

---

## Step 5 — Read workaround if score < 3

If score is `?/3`: skip this step.

If score is 0, 1, or 2: read the `### Agent Workaround` section from the failure mode file.
Select the techniques that apply given the gap. Substitute real values from the environment profile (actual flag names, actual binary path, actual timeout method). Omit a technique only if the environment profile's Non-Interactive Flags or Output Format Flags sections list the exact flag or env var it recommends, and the onboard check confirmed it suppresses the relevant behaviour. Do not omit based on flag name similarity alone.

---

## Step 6 — Emit the result

Output a structured result block for immediate visibility. This block is for the conversation only — it is not what gets saved to `evaluations/<cli-name>/findings.md`. The findings artifact uses the compact table format in Step 7.

```
## Evaluation Result

**Failure mode:** §N — <title>
**Severity:** <Critical | High | Medium>
**CLI:** <tool name>
**Score:** <0–3> / 3  _(or `? / 3` if check timed out)_
**Check:** <one-line summary of what was observed — or "timed out after N seconds" for ?/3>

### Applicable Workaround
<workaround with real values from environment profile — omit section if score is 3 or ?/3>

### Notes
<bugs, unexpected behaviours, or findings relevant to other failure modes — tag each with §N if known>
```

---

## Step 7 — Save findings and trace

**Findings** — load `evaluations/<cli-name>/findings.md` if it exists. If `--refresh` is set and a row for this §N already exists, replace that row; otherwise append one row.

For the Notes column: summarize what was observed. If score is `?/3` (timeout), write `timeout after <N>s — check could not complete`.

```markdown
# Findings — <cli-name>

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §10 | Interactivity & TTY Requirements | Critical | 2/3 | 2026-03-15 | confirm() exits with error in non-TTY without --yes; pager suppressed ✓ |
```

If any bugs or unexpected behaviours were observed, load `evaluations/<cli-name>/issues.md`, append an entry, and save it back:

```markdown
# Issues — <cli-name>

### §18 candidate — transaction add unhandled TypeError
`bean transaction add` without `--json` raises a raw stack trace instead of a clean error.
Discovered during §10 evaluation on 2026-03-15.
```

**Trace** — load `evaluations/<cli-name>/trace.md` if it exists. If `--refresh` is set and a block for this §N already exists, replace that block; otherwise append one block. The trace makes the score auditable and reproducible.

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
Usage: bean [OPTIONS] COMMAND [ARGS]...
...
```

**stderr** (first 20 lines):
```
confirm() requires a TTY
```
```

Trace capture rules:
- Record the exact command string as executed (with all flags and env vars set by the check)
- Cap stdout and stderr at 20 lines each; add `[truncated — N lines total]` if longer
- If the check was confirmed by the user rather than run automatically, write `**Check method:** user-confirmed` and record what was described
- Do not redact output — the trace is the raw evidence for the score

---

## Rules

- Always run Step 0 first — never skip environment discovery
- Re-use the existing profile if present; do not re-run discovery unnecessarily
- The workaround must use actual values from the environment profile, not generic placeholders
- Do not infer the score from the failure mode title alone — always run the check
- If the check cannot be run automatically (no CLI access), state that explicitly and ask the user to provide the observation
- Use only the four files under `evaluations/<cli>/` for persistence — do not write to any other paths
- If `evaluations/<cli>/findings.md` already contains a row for this §N and `--refresh` is not set: skip Steps 1–7 entirely and report "§N already evaluated — pass --refresh to re-run"
