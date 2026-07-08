# temporal — Fix Report

**Generated:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Scope:** critical
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | 2 | 15 | 4 | 1 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §1 — Exit Codes & Status Signaling  [Critical · 0/3]

**Gap:** Missing args, not-found, and network/timeout failures all exited 1; no declared semantic code table or JSON error exit_code field was observed.

**Solutions:**
Publish a stable exit-code table and include the numeric exit code in every JSON error body.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §1.

### §13 — Partial Failure & Atomicity  [Critical · 0/3]

**Gap:** A deliberate bad batch/query path returned a single prose error with no `partial`, `completed_steps`, `failed_step`, rollback, or resume token.

**Solutions:**
For multi-step and batch commands, emit per-step results, partial status, failed step, and resume or rollback handles.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §13.

### §25 — Prompt Injection via Output  [Critical · 0/3]

**Gap:** User-controlled/local config data is returned as raw JSON values with no trust boundary, envelope, or `trusted: false` metadata.

**Solutions:**
Wrap external data separately from CLI metadata and mark it with trust/source fields.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §25.

### §74 — Credential Scope Declaration Absence  [Critical · 0/3]

**Gap:** `--schema`, `manifest`, and `check-permissions --for ...` are absent; command entries expose no `required_scopes` field.

**Solutions:**
Add required_scopes to command manifests and a check-permissions preflight.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §74.

### §2 — Output Format & Parseability  [Critical · 1/3]

**Gap:** `--output json` exists and success paths return JSON, but validation and connection failures print prose/usage text instead of an ok/data/error envelope.

**Solutions:**
Make `--output json` invariant for both success and failure paths with ok, data, error, warnings, and meta.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §2.

### §11 — Timeouts & Hanging Processes  [Critical · 1/3]

**Gap:** `--command-timeout` and `--client-connect-timeout` work, but timeout/network failures exit 1 with `Error: program interrupted` rather than structured TIMEOUT JSON.

**Solutions:**
Emit structured TIMEOUT errors with a distinct exit code and duration metadata.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §11.

### §12 — Idempotency & Safe Retries  [Critical · 1/3]

**Gap:** Workspace-local `env set` was repeatable, and workflow start has ID conflict/reuse policies, but no `--idempotency-key` or response `effect` contract exists.

**Solutions:**
Add idempotency keys or explicit effect fields for mutating commands so retries can be made safely.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §12.

### §23 — Side Effects & Destructive Operations  [Critical · 1/3]

**Gap:** Query-based destructive commands have `--yes` prompt bypass and JSON mode refuses prompts, but destructive commands expose no `--dry-run`, `danger_level`, or effect field.

**Solutions:**
Add dry-run and structured effect/danger metadata to every destructive command.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §23.

### §24 — Authentication & Secret Handling  [Critical · 1/3]

**Gap:** Temporal accepts API keys through `--api-key`, which exposes secrets in process arguments; a debug probe did not echo the test key in captured output.

**Solutions:**
Prefer env/file secret inputs and deprecate secret-bearing argv flags, or auto-redact and warn when they are used.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §24.

### §34 — Shell Injection via Agent-Constructed Commands  [Critical · 1/3]

**Gap:** Some enum-style flags reject invalid values, but a `%2F`-encoded environment name was accepted and errors are unstructured; no agent-hardening declaration exists.

**Solutions:**
Reject traversal/metacharacter patterns consistently and return structured validation suggestions.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §34.

### §42 — Debug / Trace Mode Secret Leakage  [Critical · 1/3]

**Gap:** Debug logging did not echo the test API key, but secrets can still be supplied on argv and no schema marks sensitive fields.

**Solutions:**
Add sensitive-field metadata and safe trace mode; prefer env/file secret injection over argv flags.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §42.

### §43 — Tool Output Result Size Unboundedness  [Critical · 1/3]

**Gap:** List commands expose `--limit`/`--page-size`, but outputs lack `meta.truncated`, total byte counts, or a global `--max-output` guard.

**Solutions:**
Add output caps and truncation metadata to large or single-result responses.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §43.

### §50 — Stdin Consumption Deadlock  [Critical · 1/3]

**Gap:** Commands with missing required input failed quickly with usage/prose and did not block, but no structured `STDIN_REQUIRED` code or hint was emitted.

**Solutions:**
Emit structured `STDIN_REQUIRED` errors for stdin-dependent arguments and declare stdin fallbacks in schema.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §50.

### §60 — OS Output Buffer Deadlock  [Critical · 1/3]

**Gap:** `server start-dev` emitted startup lines, but no JSON heartbeat or progress protocol for long-running commands was observed.

**Solutions:**
Emit line-delimited JSON heartbeats with elapsed time and current step for long-running commands.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §60.

### §61 — Bidirectional Pipe Payload Deadlock  [Critical · 1/3]

**Gap:** Workflow input commands provide `--input-file`, but stdin size limits and `STDIN_TOO_LARGE` overflow errors were not observed.

**Solutions:**
Declare stdin size limits and return `STDIN_TOO_LARGE` with an input-file hint when exceeded.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §61.

### §71 — Non-Interactive Installation Absence  [Critical · 1/3]

**Gap:** The binary is installed and `--version` works, but this audit workspace has no AGENTS.md/README documenting a non-interactive, idempotent install command.

**Solutions:**
Document a pinned non-interactive install and verify command in AGENTS.md.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §71.

### §10 — Interactivity & TTY Requirements  [Critical · 2/3]

**Gap:** Local mutating config commands complete with stdin closed, and JSON destructive query commands require prompt bypass; no universal schema declares interactive paths.

**Solutions:**
Declare every interactive command in a manifest and auto-disable prompts when stdin/stdout are non-TTY.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §10.

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · 2/3]

**Gap:** Temporal uses API-key/config flags and no browser OAuth flow was observed; auth failures are not exposed as structured `AUTH_REQUIRED`/`auth_methods` envelopes.

**Solutions:**
Declare auth requirements and methods in a manifest and return structured auth errors.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §45.

### §64 — Headless Display and GUI Launch Blocking  [Critical · 2/3]

**Gap:** `server start-dev` documents `--headless` and prints service/UI URLs instead of opening a browser; no schema declares GUI/headless behavior.

**Solutions:**
Declare GUI operations/headless behavior in a manifest and return URL/path fields in JSON.

**Requirements that address this:**
- Requirements index was not available under the report skill; map this fix to the corresponding CLI Agent Spec requirement for §64.


## Already Passing

§37, §62  _(score 3/3 — no action needed)_

## Could Not Verify

§53  _(behavior unknown; treat as unverified risk)_
