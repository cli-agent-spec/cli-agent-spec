# cube — Issues Report

**Generated:** 2026-08-06
**CLI version:** 1.7.16
**Scope:** Critical severity
**Findings in scope:** 22 failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### §42 candidate — `--token` exposes credentials in process listings

**Discovered during:** §42 evaluation — 2026-08-06
**Symptom:** The documented `--token` flag places the credential verbatim in the process command line; the fake value `cli-visible-secret` was visible through `ps` while a request was active. Prefer `CUBE_API_KEY` for agent and CI use.
**Impact:** Credentials can leak into process inventories, diagnostics, or agent logs.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --token cli-visible-secret --debug whoami < /dev/null`

---

### §43 candidate — unbounded single-result output

**Discovered during:** §43 evaluation — 2026-08-06
**Symptom:** `cube --json api GET /large` printed a 70 KiB field in full (71,748 stdout bytes) with no `meta.truncated`, total-size metadata, `--max-output`, or field-selection guard. A single API response can therefore overflow an agent context.
**Impact:** One API result can exhaust the agent context before it can post-process the response.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api GET /large < /dev/null`

---

### §45 candidate — `--json` authentication failures are prose-only

**Discovered during:** §45 evaluation — 2026-08-06
**Symptom:** With an isolated empty config and closed stdin, `cube --json whoami` failed promptly but wrote a human sentence to stderr and exited 1. It did not emit an `AUTH_REQUIRED` object or enumerate available headless authentication methods.
**Impact:** Agents must parse English prose to select authentication recovery.
**Trigger:** `env -u CUBE_API_URL -u CUBE_API_KEY CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 XDG_CONFIG_HOME=/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/xdg-empty /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --json whoami < /dev/null`

---

### §50 candidate — closed stdin is reported as malformed JSON

**Discovered during:** §50 evaluation — 2026-08-06
**Symptom:** `cube api POST /mutate -d -` with stdin closed exits promptly, but reports an EOF parser failure instead of declaring that stdin input is required or suggesting `-d @file.json`/inline JSON.
**Impact:** Agents cannot distinguish absent stdin from malformed JSON using a stable code.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api POST /mutate -d - < /dev/null`

---

### §53 candidate — expired credentials have no machine-readable identity

**Discovered during:** §53 evaluation — 2026-08-06
**Symptom:** A mocked 401 yields useful prose (`session expired` and `cube login`) but still exits 1 and emits no `CREDENTIALS_EXPIRED`, `expired_at`, or `reauth_command` field. Agents must parse English text to distinguish expiry from other auth failures.
**Impact:** Retry policy cannot reliably distinguish refreshable expiry from permanent denial.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token expired-audit-token --json api GET /expired < /dev/null`

---

### §60 candidate — HTTP responses are fully buffered before output

**Discovered during:** §60 evaluation — 2026-08-06
**Symptom:** A streaming mock response flushed one JSON fragment immediately and another three seconds later. Cube emitted nothing at the first observation point, then printed the entire document after completion. Long responses therefore provide no incremental progress or heartbeat.
**Impact:** Long operations can appear dead and provide no liveness evidence before completion.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api GET /stream < /dev/null`

---

### §61 candidate — stdin payloads have no declared or enforced size limit

**Discovered during:** §61 evaluation — 2026-08-06
**Symptom:** Cube accepted a 70,014-byte JSON object from stdin and simultaneously returned 71,727 bytes. The run completed, but there was no size ceiling or overflow signal. Agents should switch to the supported `-d @file.json` form before large payloads reach the pipe.
**Impact:** Large bidirectional pipes have no enforced safety boundary or overflow signal.
**Trigger:** `perl -e 'print "{\"payload\":\"", "x" x 70000, "\"}"' | env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api POST /large -d -`

---

### §64 candidate — login launches a browser and blocks in headless CI

**Discovered during:** §64 evaluation — 2026-08-06
**Symptom:** With `CI=true`, closed stdin, isolated config, and `--json`, `cube login` still invoked the platform browser command and entered its authorization polling loop. The URL was emitted as ANSI-decorated prose, not a machine-readable headless fallback. A harmless local browser shim was used so no real GUI opened.
**Impact:** Headless jobs can open a GUI path and remain blocked awaiting human approval.
**Trigger:** `env PATH=/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/headless-bin CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 XDG_CONFIG_HOME=/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/xdg-empty /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --json login --url http://127.0.0.1:18765 < /dev/null`

---

### §10 candidate — OAuth login ignores non-TTY execution

**Discovered during:** §10 evaluation — 2026-08-06
**Symptom:** `cube login --url ...` with closed stdin and `CI=true` remained active beyond five seconds in its device-flow polling loop and required cancellation. There is no non-TTY guard or structured `INTERACTIVE_REQUIRED` failure; agents must avoid `login` and inject `CUBE_API_KEY` instead.
**Impact:** A non-TTY agent can stall until an external supervisor cancels the login.
**Trigger:** `env PATH=/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/headless-bin CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 XDG_CONFIG_HOME=/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/xdg-empty /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube login --url http://127.0.0.1:18765 < /dev/null`

---

### §11 candidate — network operations have no user-configurable timeout

**Discovered during:** §11 evaluation — 2026-08-06
**Symptom:** The global parser rejects `--timeout`. Against a localhost endpoint that withheld its response, Cube produced no output and remained active after three seconds until cancelled. There is no structured timeout, duration, heartbeat, or resume data.
**Impact:** Network or lock stalls consume the entire orchestration budget unless the caller kills them.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --timeout 2 --api-url http://127.0.0.1:18765 --token audit-token --json api GET /slow < /dev/null`

---

### §12 candidate — mutating commands have no idempotency key

**Discovered during:** §12 evaluation — 2026-08-06
**Symptom:** The `api` mutation path rejects `--idempotency-key`, and the global command surface exposes no equivalent. Agents cannot safely identify retries or distinguish a repeated creation from a noop without separately querying state.
**Impact:** Retries can duplicate mutations because the CLI cannot identify a logical operation.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api POST /mutate -d '{}' --idempotency-key audit-1 < /dev/null` (run twice)

---

### §13 candidate — deploy partial failures are not structured

**Discovered during:** §13 evaluation — 2026-08-06
**Symptom:** A deliberately failed upload step showed useful prose progress and the failing endpoint, but `--json` emitted no JSON at all. The output does not say whether the upload transaction remains open, which steps completed, whether rollback is possible, or where a safe retry should resume.
**Impact:** Agents cannot know which deploy steps committed or where a safe resume begins.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json deploy 1 --directory /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/tmp/deploy-project -m 'audit partial failure' < /dev/null`

---

### §23 candidate — destructive calls have no preview or confirmation contract

**Discovered during:** §23 evaluation — 2026-08-06
**Symptom:** The raw API escape hatch rejects `--dry-run`, while an otherwise identical DELETE executes immediately without confirmation. The observed deletion was confined to the localhost mock; the production-facing command surface offers no machine-readable danger level or affected-scope preview.
**Impact:** A mistaken destructive request can execute before an agent can preview affected scope.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api DELETE /delete --dry-run < /dev/null`

---

### §25 candidate — external content is returned without trust boundaries

**Discovered during:** §25 evaluation — 2026-08-06
**Symptom:** The raw API command emitted instruction-like user content as a normal `message` field alongside identifiers, with no envelope or `trusted: false` marker. Agents cannot distinguish CLI-owned metadata from untrusted external text without endpoint-specific knowledge.
**Impact:** Instruction-like external content can be mistaken for trusted tool guidance.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json api GET /external < /dev/null`

---

### §74 candidate — minimum credential scopes are undiscoverable

**Discovered during:** §74 evaluation — 2026-08-06
**Symptom:** Cube has no schema/manifest or `check-permissions` command, and its CLI documentation explains credential mechanisms without declaring the minimum permissions required by each command group. Agents cannot pre-flight least privilege or detect an over-privileged token.
**Impact:** Agents cannot prove least privilege or detect over-privileged credentials.
**Trigger:** `/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --schema < /dev/null`

---

### §1 candidate — runtime failures collapse to exit 1

**Discovered during:** §1 evaluation — 2026-08-06
**Symptom:** Argument validation exits 2, but a not-found response and a connection failure both exit 1. The errors contain useful prose yet provide no documented semantic code or JSON `exit_code`, so retry and recovery policies must parse text.
**Impact:** Agents cannot map not-found, network, and other runtime failures to safe recovery from exit status.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube api < /dev/null`

---

### §2 candidate — `--json` does not define one success/error envelope

**Discovered during:** §2 evaluation — 2026-08-06
**Symptom:** `cube --json regions` returned valid raw API JSON with no `ok`/`data`, while `cube --json api GET /missing` returned no JSON at all—only prose on stderr. Agent integrations need separate parsers for success and failure and cannot rely on one machine contract.
**Impact:** Integrations need separate success and failure parsers and cannot validate one response schema.
**Trigger:** `env CI=true CUBE_NO_UPDATE_CHECK=1 CUBE_NO_TELEMETRY=1 /Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube --api-url http://127.0.0.1:18765 --token audit-token --json regions < /dev/null`

---

---

## Failure-Mode Gaps  _(score 0–2, sorted: score asc, severity desc; ?/3 entries listed last)_

These are not confirmed bugs but verified gaps — the CLI does not meet the bar for reliable agent use.

### §10 — Interactivity & TTY Requirements  [Critical · score 0/3]

**What fails:** With closed stdin and `CI=true`, `cube login --url ...` launched the browser path and was still polling with no new output after the five-second check window; it required manual cancellation
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §11 — Timeouts & Hanging Processes  [Critical · score 0/3]

**What fails:** `--timeout 2` is unsupported; a request whose server withheld its response was still active with no output after three seconds and required manual cancellation, with no structured timeout or partial progress
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §12 — Idempotency & Safe Retries  [Critical · score 0/3]

**What fails:** The same mutating request was attempted twice with one idempotency key; both invocations rejected `--idempotency-key` at parse time, so Cube provides no CLI-level retry identity, noop effect, or universal dry-run
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §23 — Side Effects & Destructive Operations  [Critical · score 0/3]

**What fails:** `--dry-run` was rejected, while the same DELETE against the local mock executed without confirmation and returned a deletion result; no danger declaration, preview, or explicit destructive confirmation exists
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: High
**Workaround exists:** Partial

---

### §25 — Prompt Injection via Output  [Critical · score 0/3]

**What fails:** User-controlled API text containing an instruction-like payload was returned as an ordinary raw JSON `message` field, with no response envelope, trust annotation, content type, or separation from CLI metadata
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §43 — Tool Output Result Size Unboundedness  [Critical · score 0/3]

**What fails:** A 70 KiB API field was emitted in full as 71,748 bytes; there is no output bound, truncation metadata, or pre-flight size facility
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Critical · Time: High
**Workaround exists:** Partial

---

### §60 — OS Output Buffer Deadlock  [Critical · score 0/3]

**What fails:** The server flushed the first JSON fragment immediately, yet the CLI emitted no stdout after one second and released the entire response only after the server completed; no heartbeat or incremental JSON lines were present
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §64 — Headless Display and GUI Launch Blocking  [Critical · score 0/3]

**What fails:** `cube login` invoked the platform browser command despite `CI=true`, closed stdin, isolated config, and `--json`; it then remained in the OAuth polling loop until manually cancelled, and the URL was ANSI-styled prose rather than JSON
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §74 — Credential Scope Declaration Absence  [Critical · score 0/3]

**What fails:** Neither `--schema` nor `check-permissions` exists, and official CLI docs do not map command groups to minimum API-key/OAuth scopes; agents cannot compare required, active, or excessive privileges
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial

---

### §1 — Exit Codes & Status Signaling  [Critical · score 1/3]

**What fails:** Missing arguments used clap exit 2, but both a 404 resource and a connection failure exited 1; codes are not documented and no JSON error body embeds the code
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §2 — Output Format & Parseability  [Critical · score 1/3]

**What fails:** Global `--json` produced valid raw success JSON, but without `ok`/`data`; a 404 under the same flag emitted prose only on stderr, so the output contract changes between success and failure
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Partial

---

### §13 — Partial Failure & Atomicity  [Critical · score 1/3]

**What fails:** A deploy transaction failed deliberately at file upload after hashing and transaction start; stderr named the file and failing endpoint, but `--json` still returned no `partial`, completed-step list, rollback state, or resume token
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §24 — Authentication & Secret Handling  [Critical · score 1/3]

**What fails:** A fake credential supplied through `CUBE_API_KEY` was not echoed, but Cube also accepts secrets through `--token`/`login --api-key` and maps authentication failure to generic exit 1 rather than a defined auth code
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Medium · Time: Medium
**Workaround exists:** Partial

---

### §34 — Shell Injection via Agent-Constructed Commands  [Critical · score 1/3]

**What fails:** `acme%2Fwidgets` was accepted and sent to the API; `../../etc/test` reached filesystem handling and produced only a prose path error, with no structured validation or correction suggestion
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §42 — Debug / Trace Mode Secret Leakage  [Critical · score 1/3]

**What fails:** `--debug` is unsupported and the parser did not echo the fake token, but the documented `--token` option exposed the credential verbatim in the process table; no safe trace mode or sensitive schema exists
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: Low · Time: Low
**Workaround exists:** Partial

---

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · score 1/3]

**What fails:** An authenticated command with no credentials exited immediately, but even `--json` produced only a prose stderr error with exit 1 and no `AUTH_REQUIRED` code or `auth_methods` array
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §50 — Stdin Consumption Deadlock  [Critical · score 1/3]

**What fails:** `-d -` with closed stdin failed immediately rather than hanging, but returned a generic prose JSON-parse error with exit 1 instead of a structured `STDIN_REQUIRED` error and hint
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §53 — Credential Expiry Mid-Session  [Critical · score 1/3]

**What fails:** A mocked 401 was described as “session expired” with a re-login hint, but only in prose; there was no structured expiry code, timestamp, or reauthentication field, and exit 1 was generic
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §61 — Bidirectional Pipe Payload Deadlock  [Critical · score 1/3]

**What fails:** A 70,014-byte stdin JSON object was accepted and a 71,727-byte response was emitted successfully, but no stdin size limit or `STDIN_TOO_LARGE` signal exists; `-d @file.json` is the documented file alternative
**Frequency:** Situational
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §71 — Non-Interactive Installation Absence  [Critical · score 2/3]

**What fails:** The official README documents a non-interactive installer; two isolated runs both exited 0 and `cube --version` returned `Cube CLI 1.7.16`, but no `AGENTS.md` documents the agent install and verification contract
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Critical
**Workaround exists:** Partial

---

---

## Passing  _(score 3/3 — safe to use without special handling)_

§37 — REPL / Interactive Mode Accidental Triggering; §62 — $EDITOR and $VISUAL Trap

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | 17 | §1, §2, §10, §11, §12, §13, §23, §25, §42, §43, §45, §50, §53, §60, §61, §64, §74 |
| Score 0 — complete failure | 9 | §10, §11, §12, §23, §25, §43, §60, §64, §74 |
| Score 1 — major gap | 10 | §1, §2, §13, §24, §34, §42, §45, §50, §53, §61 |
| Score 2 — minor gap | 1 | §71 |
| Score 3 — passing | 2 | §37, §62 |
| Indeterminate (?/3 — timed out) | 0 | — |

**Highest-risk combination:** Headless authentication and network calls can block without a built-in timeout, while generic prose errors, absent idempotency, and no destructive dry-run make automated recovery unsafe.
