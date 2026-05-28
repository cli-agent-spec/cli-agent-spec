# shopify — Issues Report

**Generated:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Scope:** Critical
**Findings in scope:** 22 failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

### §45 candidate — auth login blocks non-interactive agents

**Discovered during:** §45 evaluation — 2026-05-28
**Symptom:** `shopify auth login` printed a device-code URL and kept running until manually terminated.
**Impact:** An agent can hang indefinitely waiting for a human browser flow.
**Trigger:** `shopify auth login`

---

### §37 candidate — Liquid REPL path hangs under non-TTY

**Discovered during:** §37 evaluation — 2026-05-28
**Symptom:** `shopify theme console` emitted release notes and did not exit before a 3s alarm killed it.
**Impact:** Agents can lose a run to an interactive command path without a machine-readable recovery hint.
**Trigger:** `perl -e 'alarm 3; exec @ARGV' -- shopify theme console`

---

### §2 candidate — release notes and preference errors pollute command output

**Discovered during:** §2 evaluation — 2026-05-28
**Symptom:** Theme commands emitted release notes, analytics/storage errors, and stack traces before command-specific output.
**Impact:** Agents cannot safely parse stdout/stderr without defensive filtering.
**Trigger:** `shopify theme pull --store invalid.myshopify.com --password [REDACTED] --theme 123 --verbose`

---

### §24 candidate — secret material can be supplied as command-line flags

**Discovered during:** §24 evaluation — 2026-05-28
**Symptom:** Theme commands accept `--password=<value>`.
**Impact:** Credentials can enter shell history or process listings on shared agent hosts.
**Trigger:** `shopify theme pull --store invalid.myshopify.com --password [REDACTED] --theme 123 --verbose`

---

### §10 candidate — undeclared writes to user preferences

**Discovered during:** §10 evaluation — 2026-05-28
**Symptom:** Several commands attempted writes under `/Users/roman/Library/Preferences/...`, causing sandbox `EPERM` stack traces.
**Impact:** Restricted agent environments can fail before command-specific validation or structured errors are reached.
**Trigger:** theme command probes under the workspace sandbox

---

## Failure-Mode Gaps  _(score 0–2, sorted: score asc, severity desc; ?/3 entries listed last)_

### §10 — Interactivity & TTY Requirements  [Critical · score 0/3]

**What fails:** Auth and REPL paths block or wait in non-TTY; no universal `--non-interactive`/`--yes` flag or automatic structured failure.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §11 — Timeouts & Hanging Processes  [Critical · score 0/3]

**What fails:** No generic `--timeout`, JSON timeout error, defined timeout exit code, heartbeat interval, or resume token was found.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §12 — Idempotency & Safe Retries  [Critical · score 0/3]

**What fails:** Mutating commands do not expose `--idempotency-key`, universal `--dry-run`, or `effect` fields in structured responses.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial

---

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · score 0/3]

**What fails:** `shopify auth login` in non-TTY printed a device-code URL and kept running until terminated; no structured `AUTH_REQUIRED` response.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial

---

### §74 — Credential Scope Declaration Absence  [Critical · score 0/3]

**What fails:** No `--schema`/manifest required-scope declaration or `check-permissions` machine-readable preflight exists.
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Low · Time: Medium
**Workaround exists:** Partial

---

## Passing  _(score 3/3 — safe to use without special handling)_

§62 $EDITOR and $VISUAL Trap

---

## Risk Summary

| Category | Count | §N list |
|---|---:|---|
| Observed bugs | 5 | §45, §37, §2, §24, §10 |
| Score 0 — complete failure | 11 | §10, §11, §12, §13, §25, §37, §43, §45, §50, §60, §74 |
| Score 1 — major gap | 8 | §1, §2, §23, §24, §34, §42, §61, §64 |
| Score 2 — minor gap | 1 | §71 |
| Score 3 — passing | 1 | §62 |
| Indeterminate (?/3) | 1 | §53 |

**Highest-risk combination:** headless auth and interactive command paths can block agents while output pollution prevents simple parsers from recognizing the failure mode reliably.
