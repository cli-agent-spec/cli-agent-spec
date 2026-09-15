# temporal — Issues Report

**Generated:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Scope:** critical
**Findings in scope:** 22 failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### §2 candidate — `--output json` does not apply to validation failures

**Discovered during:** §2 evaluation — 2026-07-07
**Symptom:** `temporal --output json workflow start` without required flags prints usage text to stdout and prose errors to stderr.
**Impact:** Agents expecting JSON must switch parsers on failure and can accidentally ingest usage text as data.
**Trigger:** `/opt/homebrew/bin/temporal --output json workflow start`

### §11 candidate — Timeout-like network failures collapse to exit 1 and prose

**Discovered during:** §11 evaluation — 2026-07-07
**Symptom:** An unroutable server with 2s command/client timeouts exits 1 with `Error: program interrupted`.
**Impact:** Agents cannot distinguish timeout, cancellation, and other failures from the exit code or JSON body.
**Trigger:** `/opt/homebrew/bin/temporal --output json --address 203.0.113.1:7233 --client-connect-timeout 2s --command-timeout 2s workflow list`

### §23 candidate — Destructive commands lack dry-run/effect contracts

**Discovered during:** §23 evaluation — 2026-07-07
**Symptom:** `workflow delete --dry-run` is rejected as an unknown flag, and query deletes require `--yes` but return only a batch job ID.
**Impact:** An agent cannot get a machine-readable would-delete scope or distinguish created/noop/effect outcomes.
**Trigger:** `/opt/homebrew/bin/temporal workflow delete --dry-run --workflow-id missing-audit-id`

### §74 candidate — No machine-readable credential scope declaration

**Discovered during:** §74 evaluation — 2026-07-07
**Symptom:** `--schema`, `manifest`, and `check-permissions` probes all fail as unknown.
**Impact:** Agents cannot select minimally scoped credentials before invocation.
**Trigger:** `/opt/homebrew/bin/temporal check-permissions --for workflow list`


---

## Failure-Mode Gaps  _(score 0–2, sorted: score asc, severity desc; ?/3 entries listed last)_

These are not confirmed bugs but verified gaps. `?/3` entries are included at the end with behavior unknown.

### §1 — Exit Codes & Status Signaling  [Critical · score 0/3]

**What fails:** Missing args, not-found, and network/timeout failures all exited 1; no declared semantic code table or JSON error exit_code field was observed.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes

### §13 — Partial Failure & Atomicity  [Critical · score 0/3]

**What fails:** A deliberate bad batch/query path returned a single prose error with no `partial`, `completed_steps`, `failed_step`, rollback, or resume token.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes

### §25 — Prompt Injection via Output  [Critical · score 0/3]

**What fails:** User-controlled/local config data is returned as raw JSON values with no trust boundary, envelope, or `trusted: false` metadata.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes

### §74 — Credential Scope Declaration Absence  [Critical · score 0/3]

**What fails:** `--schema`, `manifest`, and `check-permissions --for ...` are absent; command entries expose no `required_scopes` field.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Yes

### §2 — Output Format & Parseability  [Critical · score 1/3]

**What fails:** `--output json` exists and success paths return JSON, but validation and connection failures print prose/usage text instead of an ok/data/error envelope.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Yes

### §11 — Timeouts & Hanging Processes  [Critical · score 1/3]

**What fails:** `--command-timeout` and `--client-connect-timeout` work, but timeout/network failures exit 1 with `Error: program interrupted` rather than structured TIMEOUT JSON.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §12 — Idempotency & Safe Retries  [Critical · score 1/3]

**What fails:** Workspace-local `env set` was repeatable, and workflow start has ID conflict/reuse policies, but no `--idempotency-key` or response `effect` contract exists.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes

### §23 — Side Effects & Destructive Operations  [Critical · score 1/3]

**What fails:** Query-based destructive commands have `--yes` prompt bypass and JSON mode refuses prompts, but destructive commands expose no `--dry-run`, `danger_level`, or effect field.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Yes

### §24 — Authentication & Secret Handling  [Critical · score 1/3]

**What fails:** Temporal accepts API keys through `--api-key`, which exposes secrets in process arguments; a debug probe did not echo the test key in captured output.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Yes

### §34 — Shell Injection via Agent-Constructed Commands  [Critical · score 1/3]

**What fails:** Some enum-style flags reject invalid values, but a `%2F`-encoded environment name was accepted and errors are unstructured; no agent-hardening declaration exists.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes

### §42 — Debug / Trace Mode Secret Leakage  [Critical · score 1/3]

**What fails:** Debug logging did not echo the test API key, but secrets can still be supplied on argv and no schema marks sensitive fields.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Low · Time: Low
**Workaround exists:** Yes

### §43 — Tool Output Result Size Unboundedness  [Critical · score 1/3]

**What fails:** List commands expose `--limit`/`--page-size`, but outputs lack `meta.truncated`, total byte counts, or a global `--max-output` guard.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Critical · Time: High
**Workaround exists:** Yes

### §50 — Stdin Consumption Deadlock  [Critical · score 1/3]

**What fails:** Commands with missing required input failed quickly with usage/prose and did not block, but no structured `STDIN_REQUIRED` code or hint was emitted.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §60 — OS Output Buffer Deadlock  [Critical · score 1/3]

**What fails:** `server start-dev` emitted startup lines, but no JSON heartbeat or progress protocol for long-running commands was observed.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §61 — Bidirectional Pipe Payload Deadlock  [Critical · score 1/3]

**What fails:** Workflow input commands provide `--input-file`, but stdin size limits and `STDIN_TOO_LARGE` overflow errors were not observed.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §71 — Non-Interactive Installation Absence  [Critical · score 1/3]

**What fails:** The binary is installed and `--version` works, but this audit workspace has no AGENTS.md/README documenting a non-interactive, idempotent install command.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Critical
**Workaround exists:** Yes

### §10 — Interactivity & TTY Requirements  [Critical · score 2/3]

**What fails:** Local mutating config commands complete with stdin closed, and JSON destructive query commands require prompt bypass; no universal schema declares interactive paths.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · score 2/3]

**What fails:** Temporal uses API-key/config flags and no browser OAuth flow was observed; auth failures are not exposed as structured `AUTH_REQUIRED`/`auth_methods` envelopes.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §64 — Headless Display and GUI Launch Blocking  [Critical · score 2/3]

**What fails:** `server start-dev` documents `--headless` and prints service/UI URLs instead of opening a browser; no schema declares GUI/headless behavior.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes

### §53 — Credential Expiry Mid-Session  [Critical · score ?/3]

**What fails:** Could not safely create or mock an expired Temporal credential in this environment; behavior remains unverified.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial


---

## Passing  _(score 3/3 — safe to use without special handling)_

- §37 — REPL / Interactive Mode Accidental Triggering
- §62 — $EDITOR and $VISUAL Trap

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | 4 | §2, §11, §23, §74 |
| Score 0 — complete failure | 4 | §1, §13, §25, §74 |
| Score 1 — major gap | 12 | §2, §11, §12, §23, §24, §34, §42, §43, §50, §60, §61, §71 |
| Score 2 — minor gap | 3 | §10, §45, §64 |
| Score 3 — passing | 2 | §37, §62 |
| Indeterminate (?/3) | 1 | §53 |

**Highest-risk combination:** Temporal has useful JSON success output and safe prompt behavior in places, but failures collapse to prose/exit 1 while destructive, auth, and scope contracts remain under-specified for autonomous agents.
