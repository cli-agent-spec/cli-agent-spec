# gws — Issues Report

**Generated:** 2026-05-14
**CLI version:** 0.17.0
**Scope:** Critical (22 failure modes)
**Findings in scope:** 22 failure modes

---

## Observed Bugs _(from evaluation notes)_

### §1 candidate — Auth failures exit 0 on list commands

**Discovered during:** §1 evaluation — 2026-05-14
**Symptom:** `gws drive files list` returns a JSON auth error body but exits with code 0. `gws drive files get` correctly exits 2 on the same auth error. The inconsistency is per-command.
**Impact:** Agent has no failure signal from exit code on list operations. An agent that branches on exit code will treat a failing list call as success and proceed with an empty or missing result.
**Trigger:** `gws drive files list --params '{"pageSize":1}'` with expired credentials

---

### §53 — Credential expiry indistinguishable from permission denial

**Discovered during:** §53 evaluation — 2026-05-14
**Symptom:** Both expired token (`invalid_rapt`) and permanent permission denial return `{"error":{"code":401,"reason":"authError"}}`. The only distinction is buried in the `message` field as a long OAuth error string.
**Impact:** Agent cannot safely decide whether to retry (expiry = transient) or abort (denial = permanent). Blind retry on permanent denial loops indefinitely. Blind abort on expiry abandons a recoverable task.
**Trigger:** `gws drive files list` with an expired OAuth token (invalid_rapt state)

---

### §45 candidate — Missing AUTH_REQUIRED structured error

**Discovered during:** §45 evaluation — 2026-05-14
**Symptom:** Running without credentials returns `reason: "authError"` with no `auth_methods` array. The agent cannot programmatically determine how to authenticate — it must read the error message prose.
**Impact:** Agent cannot self-recover from a missing-credentials state. No machine-readable guidance on which env var to set.
**Trigger:** `GOOGLE_WORKSPACE_CLI_TOKEN="" GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="" gws drive files list < /dev/null`

---

### §43 candidate — No response body size limit

**Discovered during:** §43 evaluation — 2026-05-14
**Symptom:** `--page-limit` caps pagination page count but not the size of individual response bodies. A single large document, email, or spreadsheet is returned in full.
**Impact:** A single `gws docs documents get` on a large document can return hundreds of kilobytes — overflowing the agent's context window with a single call.
**Trigger:** `gws docs documents get --params '{"documentId":"<large-doc-id>"}'`

---

### §11 candidate — No timeout mechanism

**Discovered during:** §11 evaluation — 2026-05-14
**Symptom:** `--timeout` flag does not exist (returns validation error). Network hangs (unreachable API, DNS timeout) block indefinitely.
**Impact:** A single hung gws call blocks the agent's entire pipeline until the OS TCP timeout (up to 2 minutes) fires — with no structured error, no JSON output, and exit code from the OS kill signal.
**Trigger:** `gws drive files list --timeout 1` → `{"error":{"code":400,"message":"error: unexpected argument '--timeout' found..."}}`

---

### §42 candidate — ANSI codes in debug stderr

**Discovered during:** §42 evaluation — 2026-05-14
**Symptom:** `GOOGLE_WORKSPACE_CLI_LOG=gws=debug` emits ANSI escape sequences (`\x1b[2m`, `\x1b[34m`, etc.) to stderr. Agents capturing stderr for error parsing receive polluted output.
**Impact:** Agents that parse stderr to extract error messages will receive ANSI-polluted strings. Pattern matching on error codes breaks. ANSI stripping adds complexity.
**Trigger:** `GOOGLE_WORKSPACE_CLI_LOG=gws=debug gws drive files list < /dev/null`

---

### §64 — No headless auth alternative for `gws auth login`

**Discovered during:** §64 evaluation — 2026-05-14
**Symptom:** `gws auth login` explicitly opens a browser ("Authenticate via OAuth2 (opens browser)"). No `--print-url`, `--no-browser`, or device-code flow alternative.
**Impact:** Agent cannot perform initial authentication without human intervention. There is no in-band path for headless token acquisition. Agents must be pre-seeded with `GOOGLE_WORKSPACE_CLI_TOKEN` set externally before first use.
**Trigger:** `gws auth --help` → `login    Authenticate via OAuth2 (opens browser)`

---

## Failure-Mode Gaps _(score 0–2, sorted: score asc, severity desc)_

### §11 — Timeouts & Hanging Processes [Critical · 0/3]

**What fails:** Network hangs block indefinitely — the agent receives no output and no timeout error; the pipeline stalls until OS TCP timeout (~2 minutes).
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (external timeout via `perl alarm` or `subprocess.run(timeout=N)` — does not produce structured JSON error)

---

### §13 — Partial Failure & Atomicity [Critical · 0/3]

**What fails:** Workflow commands (`gws workflow +standup-report`, etc.) fail with a generic error and no indication of which steps completed — agents retry the entire workflow and duplicate side effects.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (decompose workflow into individual calls; track state manually in agent)

---

### §25 — Prompt Injection via Output [Critical · 0/3]

**What fails:** Email bodies, document content, and file names are returned as raw untagged strings in the JSON response — LLMs consuming this output may execute injected instructions from external data.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (manually extract fields; never route raw external content to LLM — but no structural guarantee)

---

### §53 — Credential Expiry Mid-Session [Critical · 0/3]

**What fails:** When credentials expire mid-session, every subsequent call returns `reason:"authError"` — identical to permanent denial — and the agent cannot distinguish retryable expiry from permanent failure.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (inspect message string for `invalid_rapt`/`invalid_grant` patterns; treat as potentially retriable — but cannot auto-refresh without human browser interaction)

---

### §1 — Exit Codes & Status Signaling [Critical · 1/3]

**What fails:** Agent branches on exit code and treats list commands with auth errors as success (exit 0), proceeding with an empty result as if the call succeeded.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Yes (always parse stdout JSON; check for `"error"` key regardless of exit code)

---

### §2 — Output Format & Parseability [Critical · 1/3]

**What fails:** No top-level `ok`/`data`/`meta` envelope — agent must handle two different structures (raw API JSON on success; `{error:{...}}` on failure) with no common discriminator field.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Yes (normalize in wrapper: `ok = "error" not in data`)

---

### §12 — Idempotency & Safe Retries [Critical · 1/3]

**What fails:** Retrying a failed email send or calendar event creation causes duplicates — no idempotency key and no `effect: "noop"` signal to detect second writes.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (read-before-write pattern; track operation IDs in agent state — subject to TOCTOU race)

---

### §23 — Side Effects & Destructive Operations [Critical · 1/3]

**What fails:** `--dry-run` validates params locally but does not return the affected scope — agent cannot confirm what would be deleted before executing.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial (fetch resource metadata before destructive call; confirm identity manually)

---

### §34 — Shell Injection via Agent-Constructed Commands [Critical · 1/3]

**What fails:** LLM-generated values passed to `--params` with metacharacters (`../../`, `%2F`, `?`) reach the Google API without CLI-level validation — may cause unexpected API behavior or data access.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Yes (validate params with regex before passing; use exec-array form — never shell=True)

---

### §42 — Debug / Trace Mode Secret Leakage [Critical · 1/3]

**What fails:** Enabling `GOOGLE_WORKSPACE_CLI_LOG=gws=debug` produces ANSI-polluted stderr; no guaranteed redaction of token values in debug output.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Low · Time: Low
**Workaround exists:** Yes (never enable debug logging in production agent code; strip ANSI from stderr if captured)

---

### §43 — Tool Output Result Size Unboundedness [Critical · 1/3]

**What fails:** A single `gws docs documents get` or `gws gmail users messages get` on a large document returns the entire content — overflowing the agent's context window.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Critical · Time: High
**Workaround exists:** Partial (use `fields` param to limit response; manually truncate body fields — no gws-native size limit)

---

### §45 — Headless Authentication / OAuth Browser Flow Blocking [Critical · 1/3]

**What fails:** Missing credentials exit with code 0 and no `AUTH_REQUIRED` code — agent has no machine-readable signal to distinguish "never authenticated" from other errors, and no `auth_methods` to guide recovery.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (pre-check with `gws auth status`; inject `GOOGLE_WORKSPACE_CLI_TOKEN` before any call)

---

### §60 — OS Output Buffer Deadlock [Critical · 1/3]

**What fails:** No heartbeat on long-running workflow calls — agent cannot tell if a multi-second workflow call is running, stuck, or crashed until it exits.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (external timeout with progress logging thread — no step-level visibility)

---

### §64 — Headless Display and GUI Launch Blocking [Critical · 1/3]

**What fails:** `gws auth login` opens a browser; no `--print-url` alternative means agent cannot perform initial authentication headlessly.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (pre-seed `GOOGLE_WORKSPACE_CLI_TOKEN` from external token service; no in-band headless auth path)

---

### §71 — Non-Interactive Installation Absence [Critical · 1/3]

**What fails:** No AGENTS.md documents the install command; agents bootstrapping a fresh environment may use the wrong formula (`gws` vs `googleworkspace-cli`) or skip the verify step.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Critical
**Workaround exists:** Yes (`brew install googleworkspace-cli && gws --version`)

---

### §74 — Credential Scope Declaration Absence [Critical · 1/3]

**What fails:** `gws schema` returns all possible OAuth scopes (up to 8 per method) but not the minimal required set — agent cannot create a minimally-scoped credential for a specific workflow.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial (use `gws auth login -s <service> --readonly` to limit scopes at login time; no per-command `required_scopes` available)

---

### §10 — Interactivity & TTY Requirements [Critical · 2/3]

**What fails:** No `--non-interactive` flag — future commands that add interactive prompts would hang on stdin=DEVNULL without a guaranteed non-interactive mode.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes (always pass `stdin=subprocess.DEVNULL`; never call `gws auth login` from agent code)

---

### §24 — Authentication & Secret Handling [Critical · 2/3]

**What fails:** No `--secret-from-file` for container environments where env vars are harder to manage than mounted secrets files.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Yes (read secrets file at runtime and inject as env var: `env={"GOOGLE_WORKSPACE_CLI_TOKEN": open(path).read().strip()}`)

---

### §61 — Bidirectional Pipe Payload Deadlock [Critical · 2/3]

**What fails:** Large `--json` request bodies (batch spreadsheet updates, large JSON payloads) may exceed OS argument limits — no `--json-file` alternative.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (keep `--json` payloads under 64KB; batch large operations manually)

---

## Passing _(score 3/3 — safe to use without special handling)_

§37 REPL / Interactive Mode Accidental Triggering, §50 Stdin Consumption Deadlock, §62 $EDITOR and $VISUAL Trap

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | 7 | §1, §53, §45, §43, §11, §42, §64 |
| Score 0 — complete failure | 4 | §11, §13, §25, §53 |
| Score 1 — major gap | 12 | §1, §2, §12, §23, §34, §42, §43, §45, §60, §64, §71, §74 |
| Score 2 — minor gap | 3 | §10, §24, §61 |
| Score 3 — passing | 3 | §37, §50, §62 |
| Indeterminate (?/3 — timed out) | 0 | — |

**Highest-risk combination:** §53 (credential expiry indistinguishable from permanent denial) combined with §11 (no timeout) means a mid-session expiry causes every subsequent call to fail ambiguously, and any hung call has no time-bound — a cascading failure with no recovery signal.
