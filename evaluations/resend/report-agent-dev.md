# resend — Integration Guide

**Generated:** 2026-07-06
**CLI version:** resend-cli v2.8.1
**Scope:** Critical

## Invocation Invariants

These constraints must hold on every call to resend, regardless of language or framework:

```
binary:  /Users/roman/.hermes/node/bin/resend
stdin:   closed (DEVNULL / equivalent)
timeout: external subprocess timeout; use <30s for short checks and explicit budgets for long-running listeners
env:     RESEND_API_KEY  # §24, §45 — authenticate without leaking secrets in argv
flags:   -q              # §2, §60 — request JSON-oriented quiet output
         --yes           # §10, §23 — only after independent scope review for delete/rm/revoke commands
```

---

## Per-Failure-Mode Workarounds

### §1 — Exit Codes & Status Signaling [Critical · 0/3]

**Gap:** Error docs state all errors exit `1`; observed validation, auth, unknown-command, and API errors all exit `1` with no `exit_code` in JSON.

**Workaround:** Parse the JSON `error.code` from stdout/stderr and maintain your own retry policy. Treat unknown `code` values as non-retryable until inspected.

### §25 — Prompt Injection via Output [Critical · 0/3]

**Gap:** Dry-run returns user-supplied HTML as raw JSON under `request.html`; no `trusted:false`, content-type marker, or external-data wrapper.

**Workaround:** Wrap `request.html`, inbound email bodies, template HTML, contact fields, and any fetched external content in an explicit untrusted-data boundary before passing to an LLM.

### §43 — Tool Output Result Size Unboundedness [Critical · 0/3]

**Gap:** `emails send --html-file work/large.html --dry-run -q` returned 70,166 bytes with no `meta.truncated`, `meta.total_bytes`, or output cap.

**Workaround:** Capture stdout with a byte limit, summarize or discard large body fields before storing in context, and prefer caller-side field selection when possible.

### §64 — Headless Display and GUI Launch Blocking [Critical · 0/3]

**Gap:** `open`/`docs` help says they open the default browser; code invokes the OS opener even with `--quiet`/`--json`, with no JSON URL fallback.

**Workaround:** Do not call `resend open`, `resend docs`, or resource-specific `open` commands from agents. Emit the known dashboard URL yourself when a human needs it.

### §74 — Credential Scope Declaration Absence [Critical · 0/3]

**Gap:** `resend commands` contains no `required_scopes`; no `check-permissions` preflight; docs do not declare minimal scopes per command.

**Workaround:** Provision the narrowest Resend credential outside the CLI based on the workflow. Do not reuse broad personal/admin keys for agent sessions.

### Major Partial Gaps [Critical · 1-2/3]

| §N | Gap | Workaround |
|---|---|---|
| §2 | JSON shapes vary across success/error/dry-run/doctor output. | Validate each command response against command-specific schemas. |
| §11 | No user-configurable timeout or dedicated timeout code. | Apply subprocess timeouts and parse partial stderr/stdout on failure. |
| §12 | Idempotency is limited to email send/batch; no universal `effect`. | Generate idempotency keys where supported and query state before retrying mutations. |
| §13 | Batch has permissive validation, but no resume/rollback contract. | Retry only known failed items; otherwise inspect current state before rerun. |
| §23 | Delete commands require `--yes` but lack dry-run/danger metadata. | Independently list/get target scope before any delete/revoke. |
| §24 | Secret flags are accepted and `whoami` can overstate fake flag auth. | Prefer `RESEND_API_KEY`; use `doctor -q` to validate credentials. |
| §34 | Traversal-like file paths are accepted. | Validate paths before passing file flags. |
| §45 | Missing auth returns `auth_error`, not `AUTH_REQUIRED` with methods. | Preflight `RESEND_API_KEY` and `doctor -q`. |
| §50 | Stdin errors are generic JSON parse errors. | Avoid `--file -` unless you control input; pass files for larger payloads. |
| §60 | Long-running commands lack heartbeat output. | Run listeners under a watchdog and treat silence as unknown liveness. |
| §61 | Large stdin is accepted without size guard. | Use files for large payloads; avoid bidirectional piping. |

## No Action Needed

§10, §37, §62, §71 _(score 3/3)_

## Could Not Verify

§53 Credential Expiry Mid-Session _(no expired credential could be created safely during this audit)_
