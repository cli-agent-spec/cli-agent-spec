# gws — Fix Report

**Generated:** 2026-05-14
**CLI version:** 0.17.0
**Scope:** Critical (22 failure modes)
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | 3 | 15 | 4 | 0 |

---

## Required Fixes _(score < 3, sorted: severity desc, score asc)_

### §11 — Timeouts & Hanging Processes [Critical · 0/3]

**Gap:** No `--timeout` flag exists; network hangs are handled silently by the HTTP stack with no defined exit code or JSON error structure.

**Solutions:**
Built-in timeout flags:
```bash
tool operation --timeout 30s
tool operation --connect-timeout 5s
```

Progress heartbeats to stderr:
```json
{"status": "running", "step": "calling drive API", "elapsed_ms": 5000, "heartbeat": true}
```

Emit partial results before timeout:
```json
{
  "ok": false,
  "partial": true,
  "error": {"code": "TIMEOUT", "message": "Operation timed out after 30s"},
  "resume_token": "abc123"
}
```

**Requirements that address this:**
- REQ-C-028 (High) — Timeout flag declaration [Tier: C = you declare]
- REQ-C-029 (High) — Structured timeout error [Tier: C = you declare]

---

### §13 — Partial Failure & Atomicity [Critical · 0/3]

**Gap:** Workflow commands have no `completed_steps`, no `resume_from` token, and no `--rollback-on-failure`; agents cannot determine what to retry safely.

**Solutions:**
Structured partial failure output:
```json
{
  "ok": false,
  "partial": true,
  "completed_steps": ["fetch_meetings", "fetch_tasks"],
  "failed_step": "send_notification",
  "error": {"code": "RATE_LIMITED", "message": "..."},
  "resume_from": "send_notification"
}
```

Batch result per item:
```json
{
  "ok": false,
  "partial": true,
  "results": [
    {"id": "meeting-1", "ok": true, "effect": "included"},
    {"id": "email-1", "ok": false, "error": {"code": "RATE_LIMITED"}}
  ],
  "summary": {"total": 2, "succeeded": 1, "failed": 1}
}
```

Resumable commands — expose `resume_from` so agents can restart at the failed step without re-running successful ones.

**Requirements that address this:**
- REQ-C-030 (High) — Partial failure envelope [Tier: C = you declare]
- REQ-O-045 (Medium) — Rollback flag [Tier: O = you opt in]

---

### §25 — Prompt Injection via Output [Critical · 0/3]

**Gap:** API responses return external content (email subjects, document bodies, file names) as raw strings with no `trusted`/`untrusted` markers — LLMs consuming this output cannot distinguish CLI metadata from external data.

**Solutions:**
Content type tagging on all external data fields:
```json
{
  "ok": true,
  "data": {
    "_content_type": "user_data",
    "subject": "...",
    "body": "..."
  }
}
```

Structural wrapping in framework output — the framework should always wrap external data so the agent knows it is data, not instructions:
```
<tool_result source="gmail.messages.get" trusted="false">
<raw content — treat as untrusted data>
</tool_result>
```

Enable `--sanitize` on all commands by default (already available via `GWS_SANITIZE_TEMPLATE`), not just per-command opt-in.

**Requirements that address this:**
- REQ-F-012 (High) — External data tagging [Tier: F = framework handles]
- REQ-C-015 (Medium) — trusted field on data responses [Tier: C = you declare]

---

### §53 — Credential Expiry Mid-Session [Critical · 0/3]

**Gap:** Expired credentials return `reason: "authError"` — identical to permanent permission denial. Agents cannot distinguish the two and cannot safely auto-retry.

**Solutions:**
Auth errors MUST distinguish expiry from permission denial:
```json
{
  "ok": false,
  "error": {
    "code": "CREDENTIALS_EXPIRED",
    "message": "Access token expired.",
    "expired": true,
    "expired_at": "2026-05-14T11:00:00Z",
    "retryable": true,
    "reauth_command": "gws auth login",
    "reauth_env_var": "GOOGLE_WORKSPACE_CLI_TOKEN"
  }
}
```

Add exit 10 to the exit code table: `10 = credentials expired (retryable with refresh)`. Exit 8 = permanent permission denied.

Classify HTTP 401/403 responses by inspecting the underlying OAuth error before surfacing — `invalid_rapt` and `invalid_grant` are expiry signals; `insufficient_scope` and `access_denied` are permanent.

**Requirements that address this:**
- REQ-C-018 (High) — CREDENTIALS_EXPIRED distinct code [Tier: C = you declare]
- REQ-C-019 (High) — reauth_command field [Tier: C = you declare]
- REQ-F-008 (High) — Exit 10 for credential expiry [Tier: F = framework handles]

---

### §1 — Exit Codes & Status Signaling [Critical · 1/3]

**Gap:** Auth errors inconsistently exit 0 (list commands) vs exit 2 (get commands). No documented exit code table. JSON error body uses HTTP codes (401, 400) rather than symbolic names.

**Solutions:**
Follow the standard exit code table:
```
0  = success
2  = bad arguments / validation error (already used — good)
3  = operation failed mid-way
5  = not found
8  = permission denied / auth failure
9  = rate limited
10 = credentials expired (retryable)
```

Fix: all auth failures must exit 8 (or 10 for expiry), never 0. Current inconsistency where `gws drive files list` exits 0 on auth error is a bug.

Use symbolic error codes in JSON, not HTTP codes:
```json
{"error": {"code": "AUTH_FAILED", "http_status": 401, ...}}
```

**Requirements that address this:**
- REQ-C-001 (Critical) — Semantic exit codes [Tier: C = you declare]
- REQ-C-002 (High) — Exit code table documented in --help [Tier: C = you declare]

---

### §2 — Output Format & Parseability [Critical · 1/3]

**Gap:** JSON output exists and is the default, but uses `{error:{code,message,reason}}` without a top-level `ok`/`data`/`meta` envelope. Prose error lines are also emitted to stderr alongside JSON.

**Solutions:**
Machine-readable output with consistent envelope:
```json
{
  "ok": true,
  "data": {"files": [...]},
  "warnings": [],
  "meta": {"request_id": "...", "duration_ms": 120}
}
```

Error envelope:
```json
{
  "ok": false,
  "error": {"code": "AUTH_FAILED", "message": "...", "retryable": false},
  "meta": {"request_id": "...", "duration_ms": 45}
}
```

Remove the prose `error[auth]: ...` line from stderr when stdout already carries the JSON error — this line pollutes stderr for agents parsing it separately.

**Requirements that address this:**
- REQ-C-003 (Critical) — Consistent JSON envelope [Tier: C = you declare]
- REQ-C-004 (High) — ok/data/error/meta top-level fields [Tier: C = you declare]

---

### §12 — Idempotency & Safe Retries [Critical · 1/3]

**Gap:** `--dry-run` exists on destructive commands but no `--idempotency-key` and no `effect` field (`created`/`updated`/`noop`) in responses. Agents cannot detect duplicate writes.

**Solutions:**
Idempotency keys:
```bash
gws gmail users messages send --idempotency-key "msg-$(date +%s)-$RANDOM" --json '{...}'
```

Declare operation effect in output:
```json
{
  "ok": true,
  "effect": "created",
  "data": {"id": "msg_abc123"}
}
```

Second call with same key returns:
```json
{
  "ok": true,
  "effect": "noop",
  "reason": "Message already sent with this idempotency key",
  "data": {"id": "msg_abc123"}
}
```

**Requirements that address this:**
- REQ-O-020 (High) — Idempotency key support [Tier: O = you opt in]
- REQ-C-021 (High) — effect field in all mutating responses [Tier: C = you declare]

---

### §23 — Side Effects & Destructive Operations [Critical · 1/3]

**Gap:** `--dry-run` validates requests locally but does not return `effect: "would_delete"` or the affected scope. No `danger_level` declared in schema. No `reversible` field.

**Solutions:**
Dry-run must return structured would-do output:
```bash
gws drive files delete --params '{"fileId":"abc"}' --dry-run
```
```json
{
  "ok": true,
  "effect": "would_delete",
  "would_affect": {
    "file": {"id": "abc", "name": "Budget.xlsx"},
    "reversible": false,
    "note": "File will be permanently deleted, bypassing Trash"
  }
}
```

Declare `danger_level` in `gws schema` output:
```json
{
  "command": "drive.files.delete",
  "danger_level": "destructive",
  "reversible": false
}
```

**Requirements that address this:**
- REQ-C-025 (High) — danger_level in schema [Tier: C = you declare]
- REQ-O-026 (High) — Dry-run with would-do envelope [Tier: O = you opt in]

---

### §34 — Shell Injection via Agent-Constructed Commands [Critical · 1/3]

**Gap:** Compiled Rust binary avoids shell=True, but `--params` JSON is passed to the API without CLI-level metacharacter validation. Path traversal (`../../`) and percent-encoded values are accepted without rejection.

**Solutions:**
Reject known injection patterns at the CLI argument level before sending to API:
```python
import re
SAFE_PARAM_RE = re.compile(r'^[^;&|<>`$\\\n\r]+$')
# Reject: ../, %2F, embedded ?, #, null bytes
```

Add `agent_hardening` validation for `--params` JSON values — scan for `../`, `%[0-9a-f]{2}`, embedded `?` or `#` in resource ID fields and exit with a structured `VALIDATION_ERROR` before making the API call.

**Requirements that address this:**
- REQ-F-034 (High) — Metacharacter rejection [Tier: F = framework handles]
- REQ-F-035 (High) — Path traversal rejection [Tier: F = framework handles]

---

### §42 — Debug / Trace Mode Secret Leakage [Critical · 1/3]

**Gap:** `GOOGLE_WORKSPACE_CLI_LOG=gws=debug` emits ANSI escape sequences to stderr. No `sensitive: true` field declarations in schema. No `--trace-safe` mode.

**Solutions:**
Auto-redact values matching token/secret/key/password patterns in all debug output:
```
[DEBUG] Using token: [REDACTED]
[DEBUG] GOOGLE_WORKSPACE_CLI_TOKEN: [REDACTED]
```

Provide `GOOGLE_WORKSPACE_CLI_LOG_SAFE=true` mode that enables debug logging with sensitive fields replaced by `[REDACTED]`.

Strip ANSI codes from debug output when stderr is not a TTY.

Declare sensitive fields in schema:
```json
{
  "env_vars": [
    {"name": "GOOGLE_WORKSPACE_CLI_TOKEN", "sensitive": true}
  ]
}
```

**Requirements that address this:**
- REQ-F-042 (High) — Auto-redact sensitive fields [Tier: F = framework handles]
- REQ-C-043 (Medium) — sensitive: true in schema declarations [Tier: C = you declare]

---

### §43 — Tool Output Result Size Unboundedness [Critical · 1/3]

**Gap:** `--page-limit 10` caps pagination pages but does not limit individual response body size. A single large document or email body is returned in full with no `meta.truncated` signal.

**Solutions:**
Add `meta.truncated` to responses when output is capped:
```json
{
  "ok": true,
  "data": {"body": "First 10000 chars..."},
  "meta": {"truncated": true, "total_bytes": 204800, "returned_bytes": 10240,
           "truncation_hint": "Use --offset and --max-length for subsequent chunks"}
}
```

Add `--max-length N` flag to all commands returning large text fields (document bodies, email bodies, file contents). Default to 50KB with explicit opt-out.

Declare `max_output_bytes` in `gws schema` output per command.

**Requirements that address this:**
- REQ-C-044 (High) — meta.truncated signal [Tier: C = you declare]
- REQ-O-045 (High) — max-length flag [Tier: O = you opt in]

---

### §45 — Headless Authentication / OAuth Browser Flow Blocking [Critical · 1/3]

**Gap:** API calls without credentials exit immediately (no hang), but exit code is 0 instead of 8, error uses `reason: "authError"` not `AUTH_REQUIRED`, and no `auth_methods` array is returned.

**Solutions:**
Return structured `AUTH_REQUIRED` error with auth methods:
```json
{
  "ok": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "No credentials found.",
    "auth_methods": [
      {"type": "env_var", "name": "GOOGLE_WORKSPACE_CLI_TOKEN", "description": "Pre-obtained OAuth2 access token"},
      {"type": "env_var", "name": "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE", "description": "Path to OAuth credentials JSON"}
    ]
  }
}
```

Exit 8 (not 0) on auth failure.

Include `"requires_auth": true` and `"auth_methods": [...]` in `gws schema` output.

**Requirements that address this:**
- REQ-C-009 (High) — AUTH_REQUIRED code with auth_methods [Tier: C = you declare]
- REQ-F-010 (High) — Exit 8 on auth failure [Tier: F = framework handles]

---

### §60 — OS Output Buffer Deadlock [Critical · 1/3]

**Gap:** Single-shot API call model; no heartbeat for long-running operations; debug output carries ANSI escape codes to stderr.

**Solutions:**
For long-running workflow commands, emit JSON heartbeats to stdout:
```json
{"status": "running", "step": "fetching meetings", "elapsed_ms": 2000, "heartbeat": true}
```

Strip ANSI codes from debug output when stderr is not a TTY (detect with `isatty()`).

Explicitly set line buffering on stdout startup when not a TTY.

**Requirements that address this:**
- REQ-F-060 (High) — Line-buffered stdout in non-TTY [Tier: F = framework handles]
- REQ-O-061 (Medium) — Heartbeat for long operations [Tier: O = you opt in]

---

### §64 — Headless Display and GUI Launch Blocking [Critical · 1/3]

**Gap:** `gws auth login` opens a browser with no `--print-url` or `--no-browser` alternative. Headless agents must pre-set `GOOGLE_WORKSPACE_CLI_TOKEN` externally.

**Solutions:**
Add `--print-url` flag to `gws auth login` — emits the auth URL as JSON instead of opening a browser:
```json
{
  "ok": true,
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
    "opened": false,
    "note": "Open this URL in a browser to complete authentication"
  }
}
```

Detect headless environment (`CI=true`, `DISPLAY` unset) and automatically emit URL rather than launching browser.

**Requirements that address this:**
- REQ-C-064 (High) — headless_behavior in schema [Tier: C = you declare]
- REQ-O-065 (Medium) — --print-url flag on auth commands [Tier: O = you opt in]

---

### §71 — Non-Interactive Installation Absence [Critical · 1/3]

**Gap:** Homebrew install is non-interactive and idempotent in practice, but this is not documented in AGENTS.md. No verify command documented. An update from 0.17.0 → 0.22.5 is available.

**Solutions:**
Add an `AGENTS.md` file documenting the canonical non-interactive install:
```markdown
## Installation

brew install googleworkspace-cli   # non-interactive, idempotent
gws --version                       # verify: exits 0, prints version
```

Publish a `gws doctor --json` health-check command agents can run after install to confirm the binary is functional and credentials are valid.

Update to 0.22.5 — current 0.17.0 is outdated.

**Requirements that address this:**
- REQ-O-071 (High) — AGENTS.md with install + verify commands [Tier: O = you opt in]
- REQ-C-072 (Medium) — Idempotent install documented [Tier: C = you declare]

---

### §74 — Credential Scope Declaration Absence [Critical · 1/3]

**Gap:** `gws schema <method>` returns a `scopes` field listing all possible OAuth scopes for a method (up to 8), but not a `required_scopes` minimal set. No over-privileged warning. No `check-permissions` command.

**Solutions:**
Add `required_scopes` (minimal set) to schema output, distinct from `scopes` (all possible):
```json
{
  "command": "drive.files.list",
  "required_scopes": ["https://www.googleapis.com/auth/drive.readonly"],
  "scopes": ["https://www.googleapis.com/auth/drive", "...6 more..."]
}
```

Add `gws check-permissions --for drive.files.list`:
```json
{
  "ok": true,
  "required_scopes": ["https://www.googleapis.com/auth/drive.readonly"],
  "active_scopes": ["https://www.googleapis.com/auth/drive"],
  "over_privileged": true,
  "warnings": ["Active credential has broader access than this command needs"]
}
```

Emit `warnings[]` when active credential scope exceeds `required_scopes`.

Document minimal credential recipes for common agent workflows in AGENTS.md.

**Requirements that address this:**
- REQ-C-074 (High) — required_scopes in schema [Tier: C = you declare]
- REQ-O-075 (Medium) — check-permissions pre-flight command [Tier: O = you opt in]
- REQ-O-076 (Medium) — over-privileged warning in warnings[] [Tier: O = you opt in]

---

### §10 — Interactivity & TTY Requirements [Critical · 2/3]

**Gap:** No hang on stdin=DEVNULL (good), but no explicit `--non-interactive` flag and no TTY auto-detection declared in schema. `gws auth login` opens browser without checking TTY state first.

**Solutions:**
Add `--non-interactive` flag that forces immediate failure with a structured error if any interactive path would otherwise be triggered.

Detect non-interactive context automatically:
```python
if not sys.stdin.isatty():
    # fail fast on any interactive path
    # never prompt; never open editor or browser
```

Document non-interactive operation guarantees in schema and AGENTS.md.

**Requirements that address this:**
- REQ-C-010 (High) — --non-interactive flag [Tier: C = you declare]
- REQ-F-011 (High) — TTY auto-detection [Tier: F = framework handles]

---

### §24 — Authentication & Secret Handling [Critical · 2/3]

**Gap:** Credentials via env vars only (good — no `--token` flag). Secret not echoed in errors (good). Missing: no auto-redaction framework, no `--secret-from-file` flag.

**Solutions:**
Add `--secret-from-file` / `--token-file` alternative to env var for containerized environments where env vars are harder to manage:
```bash
gws drive files list --token-file /run/secrets/gws-token
```

Add framework-level auto-redaction for any env var matching `*_TOKEN`, `*_SECRET`, `*_KEY`, `*_PASSWORD` in all log and debug output.

**Requirements that address this:**
- REQ-O-024 (Medium) — --secret-from-file flag [Tier: O = you opt in]
- REQ-F-025 (High) — Auto-redact sensitive env var values [Tier: F = framework handles]

---

### §61 — Bidirectional Pipe Payload Deadlock [Critical · 2/3]

**Gap:** No stdin data path for API operations (good — avoids deadlock). `--json` and `--params` take string arguments; `--upload` uses file paths. However, no `--input-file` for large `--json` payloads and no documented stdin size limit.

**Solutions:**
Add `--params-file` and `--json-file` flags as alternatives for large request bodies that would overflow CLI argument limits:
```bash
gws sheets spreadsheets values batchUpdate --json-file /tmp/batch-update.json
```

Document the safe payload size for `--json`/`--params` string arguments in schema.

**Requirements that address this:**
- REQ-O-061 (Medium) — --input-file for large payloads [Tier: O = you opt in]
- REQ-C-062 (Medium) — Document max arg size [Tier: C = you declare]

---

## Already Passing

§37 (REPL Triggering), §50 (Stdin Deadlock), §62 (Editor Trap) — score 3/3, no action needed
