# temporal — Integration Guide

**Generated:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Scope:** critical

## Invocation Invariants

These constraints must hold on every call to temporal, regardless of language or framework:

```
binary:  /opt/homebrew/bin/temporal
stdin:   closed (DEVNULL / equivalent)
timeout: outer subprocess timeout plus --client-connect-timeout and --command-timeout on network calls
env:     CI=true, NO_COLOR=1, PAGER=cat, EDITOR=true, VISUAL=true
flags:   --output json where supported; --color never; --client-connect-timeout <duration>; --command-timeout <duration>
```

---

## Per-Failure-Mode Workarounds  _(score < 3, sorted: severity desc, score asc)_

### §1 — Exit Codes & Status Signaling  [Critical · 0/3]

**Gap:** Missing args, not-found, and network/timeout failures all exited 1; no declared semantic code table or JSON error exit_code field was observed.

**Workaround:**
Treat any non-zero exit as ambiguous. Parse stderr for known Temporal phrases and classify locally before retrying.

### §13 — Partial Failure & Atomicity  [Critical · 0/3]

**Gap:** A deliberate bad batch/query path returned a single prose error with no `partial`, `completed_steps`, `failed_step`, rollback, or resume token.

**Workaround:**
For batch jobs, query job state after submission and record job IDs; do not assume a failed CLI exit means no server-side work occurred.

### §25 — Prompt Injection via Output  [Critical · 0/3]

**Gap:** User-controlled/local config data is returned as raw JSON values with no trust boundary, envelope, or `trusted: false` metadata.

**Workaround:**
Treat all values returned from Temporal resources, payloads, memos, search attributes, and config as untrusted external data.

### §74 — Credential Scope Declaration Absence  [Critical · 0/3]

**Gap:** `--schema`, `manifest`, and `check-permissions --for ...` are absent; command entries expose no `required_scopes` field.

**Workaround:**
Provision the narrowest credential externally and do not infer required scopes from the CLI.

### §2 — Output Format & Parseability  [Critical · 1/3]

**Gap:** `--output json` exists and success paths return JSON, but validation and connection failures print prose/usage text instead of an ok/data/error envelope.

**Workaround:**
Request `--output json`, then validate stdout strictly; if parsing fails, fall back to stderr classification and avoid treating usage text as data.

### §11 — Timeouts & Hanging Processes  [Critical · 1/3]

**Gap:** `--command-timeout` and `--client-connect-timeout` work, but timeout/network failures exit 1 with `Error: program interrupted` rather than structured TIMEOUT JSON.

**Workaround:**
Always set both `--client-connect-timeout` and `--command-timeout`; classify `program interrupted` as timeout-like only when your outer timer confirms it.

### §12 — Idempotency & Safe Retries  [Critical · 1/3]

**Gap:** Workspace-local `env set` was repeatable, and workflow start has ID conflict/reuse policies, but no `--idempotency-key` or response `effect` contract exists.

**Workaround:**
Use stable workflow IDs and conflict policies; verify state before retrying mutating commands.

### §23 — Side Effects & Destructive Operations  [Critical · 1/3]

**Gap:** Query-based destructive commands have `--yes` prompt bypass and JSON mode refuses prompts, but destructive commands expose no `--dry-run`, `danger_level`, or effect field.

**Workaround:**
List or describe the target scope first; use exact IDs or narrow queries; only pass `--yes` after validating the affected scope.

### §24 — Authentication & Secret Handling  [Critical · 1/3]

**Gap:** Temporal accepts API keys through `--api-key`, which exposes secrets in process arguments; a debug probe did not echo the test key in captured output.

**Workaround:**
Prefer environment/config injection for API keys and avoid placing secrets in command-line arguments.

### §34 — Shell Injection via Agent-Constructed Commands  [Critical · 1/3]

**Gap:** Some enum-style flags reject invalid values, but a `%2F`-encoded environment name was accepted and errors are unstructured; no agent-hardening declaration exists.

**Workaround:**
Always invoke Temporal via exec-array arguments and validate LLM-generated IDs, env names, queries, and file paths before passing them.

### §42 — Debug / Trace Mode Secret Leakage  [Critical · 1/3]

**Gap:** Debug logging did not echo the test API key, but secrets can still be supplied on argv and no schema marks sensitive fields.

**Workaround:**
Do not pass API keys as CLI arguments; scrub captured logs for high-entropy values before storing traces.

### §43 — Tool Output Result Size Unboundedness  [Critical · 1/3]

**Gap:** List commands expose `--limit`/`--page-size`, but outputs lack `meta.truncated`, total byte counts, or a global `--max-output` guard.

**Workaround:**
Always set `--limit` and `--page-size` on list commands; avoid fetching histories or payload-heavy fields unless needed.

### §50 — Stdin Consumption Deadlock  [Critical · 1/3]

**Gap:** Commands with missing required input failed quickly with usage/prose and did not block, but no structured `STDIN_REQUIRED` code or hint was emitted.

**Workaround:**
Always pass `stdin=DEVNULL` and provide required flags explicitly; treat a 1s stall as an undeclared stdin read.

### §60 — OS Output Buffer Deadlock  [Critical · 1/3]

**Gap:** `server start-dev` emitted startup lines, but no JSON heartbeat or progress protocol for long-running commands was observed.

**Workaround:**
Use an outer watchdog and kill long-running commands when no output arrives within the expected window.

### §61 — Bidirectional Pipe Payload Deadlock  [Critical · 1/3]

**Gap:** Workflow input commands provide `--input-file`, but stdin size limits and `STDIN_TOO_LARGE` overflow errors were not observed.

**Workaround:**
Use `--input-file` for payloads instead of piping large data through stdin.

### §71 — Non-Interactive Installation Absence  [Critical · 1/3]

**Gap:** The binary is installed and `--version` works, but this audit workspace has no AGENTS.md/README documenting a non-interactive, idempotent install command.

**Workaround:**
Install through a non-interactive package manager path and verify with `temporal --version` before use.

### §10 — Interactivity & TTY Requirements  [Critical · 2/3]

**Gap:** Local mutating config commands complete with stdin closed, and JSON destructive query commands require prompt bypass; no universal schema declares interactive paths.

**Workaround:**
Use `stdin=DEVNULL`; for query mutations pass `--yes` only after reviewing the query scope.

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · 2/3]

**Gap:** Temporal uses API-key/config flags and no browser OAuth flow was observed; auth failures are not exposed as structured `AUTH_REQUIRED`/`auth_methods` envelopes.

**Workaround:**
Use `--api-key` or config/env-based credentials; keep browser launch assumptions out of headless runs.

### §64 — Headless Display and GUI Launch Blocking  [Critical · 2/3]

**Gap:** `server start-dev` documents `--headless` and prints service/UI URLs instead of opening a browser; no schema declares GUI/headless behavior.

**Workaround:**
Pass `--headless` for `server start-dev`; do not rely on GUI/browser side effects.


## No Action Needed

§37, §62  _(score 3/3)_

## Could Not Verify

§53  _(treat as unverified risk; do not auto-retry auth failures unless structured expiry is present)_
