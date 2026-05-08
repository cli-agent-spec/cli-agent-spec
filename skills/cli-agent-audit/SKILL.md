---
name: cli-agent-audit
description: Autonomous end-to-end CLI audit pipeline. Downloads and installs the CLI non-interactively, onboards it, scores proactive readiness, evaluates all Critical failure modes, and generates the full report bundle (dev, agent-dev, runtime, issues, index, LinkedIn post). Single command, zero human steps required in the happy path.
license: MIT
compatibility: Requires internet access for installation. Produces all local artifacts consumed by cli-agent-report mode=all.
---

# CLI Agent Audit — Autonomous Pipeline

Run the complete evaluation pipeline for a CLI tool in one command.

## Inputs

- **CLI** — one of:
  - Package spec: `pip:my-cli==2.1.0`, `npm:my-cli@2.1.0`, `brew:my-cli`, `cargo:my-cli`, `go:github.com/org/my-cli`
  - Binary name already on PATH: `gh`, `kubectl`, `aws`
  - Binary path: `/usr/local/bin/my-cli`
- **Scope** _(optional)_ — failure modes to evaluate:
  - `critical` — Critical severity only (default; fastest)
  - `critical+high` — Critical and High severity
  - `all` — all 71 failure modes (slow; use for full audits)
- **Flags** _(optional)_:
  - `--skip-install` — skip Phase 1; assume CLI is already installed
  - `--skip-readiness` — skip Phase 3; omit readiness score from reports
  - `--refresh` — ignore existing artifacts and re-run all phases from scratch

---

## Artifacts Produced

All files are written to `evaluations/<cli>/`:

| File | Phase | Content |
|---|---|---|
| `evaluations/<cli>/environment.md` | 2 — Onboard | Binary, runtime, version, flags |
| `evaluations/<cli>/readiness.md` | 3 — Readiness | Proactive readiness scores (5 dimensions) |
| `evaluations/<cli>/findings.md` | 4 — Evaluate | Score per §N |
| `evaluations/<cli>/issues.md` | 4 — Evaluate | Observed bugs |
| `evaluations/<cli>/trace.md` | 4 — Evaluate | Raw check commands, exit codes, stdout/stderr |
| `evaluations/<cli>/report-dev.md` | 5 — Report | Fix list for CLI authors |
| `evaluations/<cli>/report-agent-dev.md` | 5 — Report | Integration guide for agent builders |
| `evaluations/<cli>/report-runtime.md` | 5 — Report | Operational brief for AI agents |
| `evaluations/<cli>/report-issues.md` | 5 — Report | Concrete bugs and gaps |
| `evaluations/<cli>/report-index.md` | 5 — Report | Index linking all reports + score summary |
| `evaluations/<cli>/README.md` | 5 — Report | Entry point — summary, key findings, file directory |
| `evaluations/<cli>/linkedin.md` | 5 — Report | LinkedIn post draft (gitignored — local use only) |
| `evaluations/<cli>/x.md` | 5 — Report | X.com thread draft (gitignored — local use only) |

---

## Phase 0 — Pre-flight

Before starting, determine what can be skipped by checking which artifacts already exist:

```
Pre-flight check — evaluations/<cli>/:
  environment.md  → [exists | missing]
  readiness.md    → [exists | missing]
  findings.md     → [exists, N rows | missing]
  trace.md        → [exists | missing]
```

Apply skip logic in this order:
- If `--refresh` is set: treat all phases as "run" initially, then apply other flags
- If `--skip-install` is set: skip Phase 1, but first verify `<binary> --version` exits 0 right now; if it fails, halt immediately with "Binary not found. Install manually or re-run without `--skip-install`."
- If `--skip-readiness` is set: skip Phase 3 regardless of `--refresh` (explicit opt-out overrides refresh)
- If `evaluations/<cli>/environment.md` exists and `--refresh` is not set: skip Phase 2 (reuse profile)
- If `evaluations/<cli>/readiness.md` exists and `--refresh` is not set and `--skip-readiness` is not set: skip Phase 3
- For Phase 4: pass `--refresh` through to `cli-agent-evaluate-batch` if set; otherwise skip §N rows already fully evaluated (complete row in findings.md AND complete block in trace.md)

If `--refresh` is set AND Phase 2 will run: pass `--force` (or equivalent) to the onboard skill so it overwrites `evaluations/<cli>/environment.md` without prompting.

Note: `evaluations/<cli>/` is created by the onboard skill in Phase 2 — no pre-creation needed here. Print the plan before executing:

```
Audit plan for <cli>:
  Phase 1 Install    → [run | skip: binary found at <path>]
  Phase 2 Onboard    → [run [--force if --refresh] | skip: profile loaded]
  Phase 3 Readiness  → [run | skip: --skip-readiness | skip: artifact exists]
  Phase 4 Evaluate   → [run N failure modes [--refresh] | skip M already evaluated (findings + trace complete)]
  Phase 5 Report     → run (all mode)
```

---

## Phase 1 — Install

**Goal:** ensure the CLI binary is available and exits 0 on `--version`.

**Note:** If `--skip-install` was set in Phase 0, this phase is skipped entirely. However, Phase 0 must have already verified the binary works (via `<binary> --version`) before marking Phase 1 as skipped. If that verification fails with `--skip-install`, Phase 0 halts with: "Binary not found. Install manually or re-run without `--skip-install`."

### Step 1a — Check if already installed

Run `<binary-name> --version` (with stdin closed). If it exits 0: binary is present — print version and skip to Phase 2.

If the input is a binary path, verify it directly. If it is a bare name (e.g. `gh`), try `which gh` first.

### Step 1b — Install non-interactively

Resolve the install command from the package spec:

| Prefix | Install command template |
|---|---|
| `pip:` | `pip install <package> --quiet --no-input` |
| `npm:` | `npm install -g <package> --no-fund --no-audit` |
| `brew:` | `brew install <package> --quiet` |
| `cargo:` | `cargo install <package> --quiet` |
| `go:` | `go install <package>@latest` |

Set these environment variables before running any install command:

```
CI=true
PIP_NO_INPUT=1
DEBIAN_FRONTEND=noninteractive
NPM_CONFIG_YES=true
```

Run the install command with `stdin=DEVNULL`. Cap execution at 120 seconds.

If the install command exits non-zero or times out: **halt the pipeline** and emit:

```
Phase 1 FAILED — Install error
Command: <exact command>
Exit code: <N>
Stderr: <first 20 lines>

Cannot proceed without a working binary. Possible fixes:
- Check the package name and version
- Try --skip-install if the binary is installed under a different name
- Install manually and rerun with --skip-install
```

### Step 1c — Verify

Run `<binary> --version` with `stdin=DEVNULL`. Confirm exit 0 and capture the version string. If this fails: halt with the same format as Step 1b.

Print: `✓ Phase 1 complete — <cli> <version> installed at <path>`

---

## Phase 2 — Onboard

**Goal:** build `evaluations/<cli>/environment.md`.

Delegate entirely to the `cli-agent-onboard` skill. Pass the resolved binary — from Phase 1 if it ran, or the binary verified in Phase 0 if `--skip-install` was set — and `--force` if `--refresh` was set (so the profile is overwritten without a prompt). The onboard skill creates `evaluations/<cli>/` if it does not exist — no separate directory creation step is needed here.

If onboard fails for any reason: **halt the pipeline** and emit:

```
Phase 2 FAILED — Onboard error
<reason from onboard skill>

Cannot proceed without an environment profile.
```

Print: `✓ Phase 2 complete — environment profile saved`

---

## Phase 3 — Readiness

**Goal:** score the CLI's proactive agent-readiness across 5 dimensions.

Delegate to `cli-agent-readiness` with `depth=full`.

If readiness fails or produces partial results: **warn and continue** — readiness is not required for the report pipeline. Note the failure in the Phase 6 summary.

Print: `✓ Phase 3 complete — readiness score: <X>/15 [<grade>]`
Or:    `⚠ Phase 3 partial — readiness incomplete, continuing`

---

## Phase 4 — Evaluate

**Goal:** evaluate the CLI against the selected scope of failure modes and populate `evaluations/<cli>/findings.md`, `issues.md`, and `trace.md`.

Delegate to `cli-agent-evaluate-batch` with the scope from the audit input (`critical` by default). If `--refresh` was set in the audit input, pass `--refresh` to the batch skill as well.

The batch skill handles:
- Resumability (skipping §N rows that are fully evaluated — complete in both findings and trace)
- Incremental saves after each §N
- User confirmation for checks that require human observation

**Human confirmation handling:** if a check requires human observation (the batch skill will ask), the audit pipeline pauses and surfaces the question to the user. After confirmation, it continues automatically. Do not skip these checks — they may be Critical severity.

After the batch run completes, print:

```
✓ Phase 4 complete — evaluated <N> failure modes
  Pass (3/3): <count>  Partial (1-2/3): <count>  Fail (0/3): <count>  Indeterminate (?/3): <count>
  Observed bugs recorded: <count>
```

If the batch skill reports that it could not run some checks (no CLI access, timeout): note each skipped §N and continue.

---

## Phase 5 — Report

**Goal:** generate the full report bundle.

Delegate to `cli-agent-report mode=all`. Pass the same CLI name. The report skill reads all artifacts produced in Phases 2–4.

The report skill produces all 8 files. Print `✓` as each file is saved (the report skill already does this).

---

## Phase 6 — Pipeline Summary

After all phases complete, print the final summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLI Agent Audit Complete — <cli> <version>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1  Install      ✓  <version>
Phase 2  Onboard      ✓
Phase 3  Readiness    ✓  <X>/15 [<grade>]   (or ⚠ partial / — skipped)
Phase 4  Evaluate     ✓  <N> failure modes · <pass>/<N> passing
Phase 5  Report       ✓  8 files written

Failure mode score:   <avg>/3  (<pass> pass · <partial> partial · <fail> fail · <indeterminate> indeterminate)
Readiness score:      <X>/15 [<grade>]  (or — skipped)
Worst gaps:           §N <title> (0/3), §N <title> (0/3)

Warnings:
  <list any Phase 3 partial/failure notes here — omit section if all phases completed cleanly>

Files:
  evaluations/<cli>/README.md             ← start here
  evaluations/<cli>/report-index.md
  evaluations/<cli>/report-issues.md
  evaluations/<cli>/report-runtime.md
  evaluations/<cli>/report-agent-dev.md
  evaluations/<cli>/report-dev.md
  evaluations/<cli>/linkedin.md           ← paste into LinkedIn; add report link as first comment
  evaluations/<cli>/x.md                  ← post thread to X; add link in closing post

Next steps:
  1. Open evaluations/<cli>/README.md for the full picture
  2. Share evaluations/<cli>/report-issues.md with agent users
  3. Publish the report and add the link as the first comment on the LinkedIn post
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Rules

- Halt on Phase 1 or Phase 2 failure — there is nothing useful to produce without a working binary and environment profile
- Never halt on Phase 3 or Phase 4 partial failure — produce whatever reports are possible
- Always run Phase 5 last, even if Phases 3 or 4 produced partial results — partial reports are better than none
- Print a one-line status update when each phase starts and when it completes — never go silent for more than the duration of a single check
- If `--refresh` is not set: the onboard skill will prompt before overwriting `evaluations/<cli>/environment.md` — do not suppress this prompt
- If `--refresh` is set: pass `--force` to the onboard skill so it overwrites without prompting; this is the only case where silent overwrite is allowed
- The scope of evaluation in Phase 4 does not affect the report bundle — all 5 report modes are always generated in Phase 5
- Do not re-implement logic from sub-skills — delegate fully and carry results forward
