# link-cli — Issues Report

**Generated:** 2026-06-08
**CLI version:** 0.7.1
**Scope:** Critical
**Findings in scope:** 22 failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### §1 candidate — semantic failures all exit 1

**Discovered during:** §1 evaluation — 2026-06-08
**Symptom:** Validation errors, auth-required errors, unknown flags, network failures, and expired token failures all returned process exit code 1 with no `exit_code` field.
**Impact:** Agents cannot route errors by process status and must parse fragile message text.
**Trigger:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli spend-request retrieve --format json`

### §2 candidate — JSON mode is not consistently enveloped by default

**Discovered during:** §2 evaluation — 2026-06-08
**Symptom:** `--format json` returns a bare array for successful commands and a bare object for errors; the `ok`/`data` envelope appears only with `--full-output`.
**Impact:** Integrations must special-case success and failure shapes.
**Trigger:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli auth status --format json`

### §11 candidate — API calls do not expose a command-level timeout

**Discovered during:** §11 evaluation — 2026-06-08
**Symptom:** Unreachable API endpoint returned `UNKNOWN` instead of a timeout code and there is no general API timeout flag.
**Impact:** Agents need external process timeouts and cannot distinguish transport timeouts from other failures.
**Trigger:** `LINK_ACCESS_TOKEN=<future-exp-token> LINK_API_BASE_URL=http://127.0.0.1:1 link-cli user-info retrieve --format json`

### §13 candidate — polling timeout returns success with pending states

**Discovered during:** §13 evaluation — 2026-06-08
**Symptom:** `auth login --interval 1 --timeout 2 --format json --full-output` exited 0 and returned pending auth states inside `ok: true`.
**Impact:** Agents may treat an incomplete auth flow as completed unless they inspect nested status fields.
**Trigger:** `LINK_AUTH_FILE=tmp/link-login-timeout.json link-cli auth login --client-name AgentAudit --interval 1 --timeout 2 --format json --full-output`

### §45 candidate — auth-required shape is incomplete

**Discovered during:** §45 evaluation — 2026-06-08
**Symptom:** Auth-gated commands return `NOT_AUTHENTICATED` with CTA text but no `AUTH_REQUIRED` code or `auth_methods` array.
**Impact:** Agents cannot discover supported auth mechanisms from the error alone.
**Trigger:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli payment-methods list --format json`

### §60 candidate — polling output is buffered until command exit

**Discovered during:** §60 evaluation — 2026-06-08
**Symptom:** A spawn probe received the first stdout chunk after about five seconds, just before `auth login --interval 1 --timeout 3 --format json` exited.
**Impact:** Agents cannot stream progress or detect liveness from stdout during long-running polling.
**Trigger:** `node -e "<spawn link-cli auth login --interval 1 --timeout 3 and log stdout chunk timestamps>"`

---

## Failure-Mode Gaps  _(score 0-2, sorted: score asc, severity desc)_

### §1 — Exit Codes & Status Signaling  [Critical · score 0/3]
**What fails:** All tested failures exit 1 and omit `exit_code`.
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

### §11 — Timeouts & Hanging Processes  [Critical · score 0/3]
**What fails:** No general API timeout flag or structured timeout error.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

### §12 — Idempotency & Safe Retries  [Critical · score 0/3]
**What fails:** No idempotency key, effect field, or dry-run coverage for mutating commands.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

### §13 — Partial Failure & Atomicity  [Critical · score 0/3]
**What fails:** No structured partial/resume state for multi-step flows.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

### §23 — Side Effects & Destructive Operations  [Critical · score 0/3]
**What fails:** No `--dry-run`, `danger_level`, or effect contract.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

### §25 — Prompt Injection via Output  [Critical · score 0/3]
**What fails:** External content is not structurally separated from CLI metadata.
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

### §60 — OS Output Buffer Deadlock  [Critical · score 0/3]
**What fails:** Polling output is emitted at process exit, not as incremental JSON heartbeats.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

### §74 — Credential Scope Declaration Absence  [Critical · score 0/3]
**What fails:** No machine-readable required scopes or permission preflight.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial

### Other partial gaps

§2, §10, §24, §34, §37, §42, §43, §45, §53, §64, and §71 scored 1-2/3. See [findings.md](findings.md) and [trace.md](trace.md) for exact evidence.

---

## Passing  _(score 3/3 — safe to use without special handling)_

§50 Stdin Consumption Deadlock; §61 Bidirectional Pipe Payload Deadlock; §62 $EDITOR and $VISUAL Trap

---

## Risk Summary

| Category | Count | §N list |
|---|---:|---|
| Observed bugs | 6 | §1, §2, §11, §13, §45, §60 |
| Score 0 — complete failure | 8 | §1, §11, §12, §13, §23, §25, §60, §74 |
| Score 1 — major gap | 5 | §2, §34, §43, §45, §53 |
| Score 2 — minor gap | 6 | §10, §24, §37, §42, §64, §71 |
| Score 3 — passing | 3 | §50, §61, §62 |
| Indeterminate (?/3 — timed out) | 0 | none |

**Highest-risk combination:** exit-code collapse, incomplete JSON envelope defaults, no timeout semantics, and no idempotency contract make retries and recovery risky for agents.
