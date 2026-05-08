# gh — Fix Report

**Generated:** 2026-05-07
**CLI version:** 2.88.1
**Scope:** Critical failure modes
**In findings:** 13 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) |
|---|---|---|---|
| Critical | 3 | 7 | 2 |
| High | 1 | 0 | 0 |
| Medium | — | — | — |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §1 — Exit Codes & Status Signaling  [Critical · 0/3]

**Gap:** HTTP 4xx responses (401, 404), GraphQL errors, and resource-not-found conditions all exit 0 — contradicting gh's own documented exit code convention that exit 4 is used for auth failures.

**Solutions:**
Map HTTP status codes to semantic exit codes before surfacing errors:
- HTTP 401/403 → exit 4 (auth required / permission denied)
- HTTP 404 → exit 5 (not found)
- HTTP 429 → exit 9 (rate limited)
- GraphQL errors → parse the `errors[].type` field and map to the appropriate exit code

Define and document a complete exit code table in `gh help exit-codes` with all codes gh can emit.

**Requirements that address this:**
- REQ-F-001 (P0) — Standard Exit Code Table [Tier: F = framework handles]
- REQ-F-002 (P0) — Exit Code 2 Reserved for Validation Failures [Tier: F = framework handles]

---

### §53 — Credential Expiry Mid-Session  [Critical · 0/3]

**Gap:** Invalid or expired `GH_TOKEN` produces a human-readable stderr message (`HTTP 401: Bad credentials`) and exits 0. Agents cannot detect auth failure programmatically, and the suggested recovery (`gh auth login`) is interactive-only.

**Solutions:**
- Exit 4 on any authentication failure, consistently
- Emit a structured JSON error to stdout (or stderr when `--json` is active) with `code: "AUTH_EXPIRED"` or `"AUTH_REQUIRED"`, `expired_at` if known, and `reauth_env_var: "GH_TOKEN"`
- Never suggest `gh auth login` in non-TTY context — suggest `GH_TOKEN=<value>` instead

**Requirements that address this:**
- REQ-F-001 (P0) — Standard Exit Code Table [Tier: F = framework handles]
- REQ-C-001 (P0) — Command Declares Exit Codes [Tier: C = you declare it]

---

### §12 — Idempotency & Safe Retries  [Critical · 1/3]

**Gap:** Mutating commands (`gh issue create`, `gh pr create`, `gh release create`) offer no idempotency key, no `effect` field in output, and no `--dry-run` flag. Retrying a failed create will produce duplicates.

**Solutions:**
- Add `--idempotency-key <string>` to all create commands; pass through to GitHub API's idempotency header where supported
- Include `"effect": "created" | "noop"` in JSON output so agents can detect duplicate suppression
- Add `--dry-run` to all mutating commands; output a `"would_create"` effect with the resource that would be created

**Requirements that address this:**
- REQ-C-007 (P1) — Mutating Commands Accept Idempotency Key [Tier: C = you declare it]
- REQ-C-003 (P0) — Mutating Commands Declare Effect Field [Tier: C = you declare it]
- REQ-C-004 (P0) — Destructive Commands Must Support Dry-Run [Tier: C = you declare it]

---

### §45 — Headless Authentication  [Critical · 1/3]

**Gap:** When stored credentials are invalid, the error is plain-text stderr and exits 0. The recovery suggestion (`gh auth login`) requires a browser. Agents have no structured signal and no non-interactive recovery path.

**Solutions:**
- In non-TTY context, emit a structured `AUTH_REQUIRED` JSON error with `auth_methods: [{"type": "env_var", "name": "GH_TOKEN"}]`
- Exit 4 consistently on all auth failures
- Document `GH_TOKEN` as the canonical non-interactive auth method in AGENTS.md

**Requirements that address this:**
- REQ-F-001 (P0) — Standard Exit Code Table [Tier: F = framework handles]
- REQ-C-005 (P0) — Interactive Commands Must Support --yes / --non-interactive [Tier: C = you declare it]

---

### §2 — Output Format & Parseability  [Critical · 2/3]

**Gap:** `--json` works but requires an explicit field list on every invocation and is not auto-activated in non-TTY. No response envelope (`ok`/`error`/`meta`) — success and failure responses have different shapes.

**Solutions:**
- Auto-activate `--json` (all fields) when stdout is not a TTY, consistent with CI=true detection
- Wrap all JSON output in a standard envelope: `{"ok": true, "data": [...], "error": null, "meta": {"duration_ms": N}}`
- On error, emit `{"ok": false, "data": null, "error": {"code": "...", "message": "..."}}` to stdout (not only stderr)

**Requirements that address this:**
- REQ-F-003 (P0) — JSON Output Mode Auto-Activation [Tier: F = framework handles]
- REQ-F-004 (P0) — Consistent JSON Response Envelope [Tier: F = framework handles]

---

### §10 — Interactivity & TTY Requirements  [Critical · 2/3]

**Gap:** No `--non-interactive` flag. Headless operation requires setting `GH_PROMPT_DISABLED=1` and `GH_PAGER=cat` — env vars not prominently documented for agent use, with no fallback if they are missed.

**Solutions:**
- Add `--non-interactive` flag: exits 4 with a structured error if any prompt would be shown
- Add `--no-pager` flag as a first-class flag (currently only suppressible via env var)
- Document both in AGENTS.md under Non-Interactive Flags

**Requirements that address this:**
- REQ-C-005 (P0) — Interactive Commands Must Support --yes / --non-interactive [Tier: C = you declare it]
- REQ-F-009 (P0) — Non-Interactive Mode Auto-Detection [Tier: F = framework handles]
- REQ-F-010 (P0) — Pager Suppression [Tier: F = framework handles]

---

### §11 — Timeouts & Hanging Processes  [Critical · 2/3]

**Gap:** No `--timeout` flag; no documented timeout env var; long API operations can hang indefinitely; no structured timeout exit code.

**Solutions:**
- Add `--timeout <duration>` flag (e.g. `--timeout 30s`) to all commands
- On timeout: exit 7, emit `{"ok": false, "error": {"code": "TIMEOUT", "duration_ms": N}}`
- Document the default per-command timeout in `--help`

**Requirements that address this:**
- REQ-F-011 (P0) — Default Timeout Per Command [Tier: F = framework handles]
- REQ-F-012 (P0) — Timeout Exit Code and JSON Error [Tier: F = framework handles]

---

### §43 — Tool Output Result Size Unboundedness  [Critical · 2/3]

**Gap:** Default limit is 30 (good), but JSON output contains no pagination metadata — agents cannot tell whether results were truncated or whether a next page exists.

**Solutions:**
- Include pagination metadata in all list command JSON responses: `"meta": {"total_count": N, "has_next_page": true, "next_cursor": "..."}`
- Add `--max-output <bytes>` flag; set `meta.truncated: true` when triggered

**Requirements that address this:**
- REQ-F-018 (P0) — Pagination Metadata on List Commands [Tier: F = framework handles]
- REQ-F-019 (P0) — Default Output Limit [Tier: F = framework handles]

---

### §62 — $EDITOR and $VISUAL Trap  [Critical · 2/3]

**Gap:** Commands like `gh issue create` without `--body` invoke `$EDITOR`. Bypass requires supplying all content flags — correct but not documented for agent use; no `EDITOR_REQUIRED` error emitted in non-TTY when flags are missing.

**Solutions:**
- In non-TTY mode, if editor would be invoked: exit 4 with `{"code": "EDITOR_REQUIRED", "alternatives": ["gh issue create --body <text>", "gh issue create --body-file <path>"]}`
- Set `GH_EDITOR=/bin/true` automatically in non-TTY mode so a missed flag fails fast rather than blocking
- Document in AGENTS.md: "always pass `--body` or `--body-file`; never rely on editor"

**Requirements that address this:**
- REQ-F-009 (P0) — Non-Interactive Mode Auto-Detection [Tier: F = framework handles]
- REQ-C-005 (P0) — Interactive Commands Must Support --yes / --non-interactive [Tier: C = you declare it]

---

## Already Passing

§8 ANSI & Color Code Leakage, §50 Stdin Consumption Deadlock, §60 OS Output Buffer Deadlock, §64 Headless Display and GUI Launch Blocking  _(score 3/3 — no action needed)_
