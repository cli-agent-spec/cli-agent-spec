# gws — Trace

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files get < /dev/null`, `gws badservice`, `gws drive files list --params '{"pageSize":1}'`
**Exit code:** 2 (auth, get), 3 (bad service), 0 (auth, list) — inconsistent
**Score:** 1/3

**stdout:**
```
{"error":{"code":401,"message":"Authentication failed...","reason":"authError"}}
```
```
{"error":{"code":400,"message":"Unknown service 'badservice'...","reason":"validationError"}}
```

**stderr:**
```
error[auth]: Authentication failed: ...
```

---

## §2 — Output Format & Parseability
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files list --format json --params '{"pageSize":1}' < /dev/null`
**Exit code:** 0
**Score:** 1/3

**stdout:**
```
{"error":{"code":401,"message":"...","reason":"authError"}}
```

**stderr:**
```
error[auth]: Authentication failed...
```

---

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `perl -e 'alarm(5); exec @ARGV' -- gws drive files list < /dev/null`
**Exit code:** 2
**Score:** 2/3

**stdout:**
```
{"error":{"code":401,"message":"Authentication failed...","reason":"authError"}}
```

**stderr:**
```
error[auth]: ...
```

---

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files list --timeout 1`
**Exit code:** 0
**Score:** 0/3

**stdout:**
```
{"error":{"code":400,"message":"error: unexpected argument '--timeout' found...","reason":"validationError"}}
```

---

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files create --help | grep -iE "idempotent|dry-run"`
**Score:** 1/3

**stdout:**
```
--dry-run    Validate the request locally without sending it to the API
```
No --idempotency-key, no effect field found.

---

## §13 — Partial Failure & Atomicity
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws --help | grep -iE "resume|rollback|partial"`, `gws workflow --help`
**Score:** 0/3

**stdout:**
```
No resume/rollback flags found. Workflow commands: +standup-report, +meeting-prep, +email-to-task, +weekly-digest, +file-announce
```
No completed_steps, no resume_from, no --rollback-on-failure.

---

## §23 — Side Effects & Destructive Operations
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files delete --help`
**Exit code:** 0
**Score:** 1/3

**stdout:**
```
Permanently deletes a file owned by the user without moving it to the trash.
--dry-run    Validate the request locally without sending it to the API
```
No effect: "would_delete", no danger_level in schema.

---

## §24 — Authentication & Secret Handling
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `GOOGLE_WORKSPACE_CLI_TOKEN="SUPERSECRETVALUE" gws drive files list 2>&1 | grep SUPERSECRETVALUE`
**Exit code:** 0
**Score:** 2/3

**stdout:**
```
secret not echoed in output
```
Only env vars accepted for credentials. No --token flag.

---

## §25 — Prompt Injection via Output
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws schema drive.files.list | python3 -c "...check for trusted field..."`
**Score:** 0/3

**stdout:**
```
has trusted field: False
top-level keys: ['description', 'httpMethod', 'parameters', 'path', 'response', 'scopes']
```
No injection protection on external data fields.

---

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files list --params '{"q":"name%2F=../../etc"}'`
**Exit code:** 0 (auth error before validation)
**Score:** 1/3

Compiled Rust binary — exec array, no shell=True. --params JSON passed to API without metacharacter validation at CLI layer.

---

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws --help | grep -iE "shell|repl|interactive|console"`
**Score:** 3/3

**stdout:**
```
no REPL/interactive commands found
```
Not applicable — no interactive mode exists.

---

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `GOOGLE_WORKSPACE_CLI_LOG=gws=debug gws drive files list < /dev/null`
**Exit code:** 0
**Score:** 1/3

**stderr (debug):**
```
[DEBUG] Discovery cache hit service=drive version=v3
Using keyring backend: keyring
```
No --debug/--verbose flags. ANSI codes in debug output. Token not observed in output, but no sensitive field declarations.

---

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws --help | grep -E "max|limit|page|truncat"`
**Score:** 1/3

**stdout:**
```
--page-all            Auto-paginate, one JSON line per page (NDJSON)
--page-limit <N>      Max pages to fetch with --page-all (default: 10)
--page-delay <MS>     Delay between pages in ms (default: 100)
```
No meta.truncated, no meta.total_bytes, no default size limit on response body.

---

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `GOOGLE_WORKSPACE_CLI_TOKEN="" GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="" gws drive files list < /dev/null`
**Exit code:** 0 (should be non-zero auth error)
**Score:** 1/3

**stdout:**
```
{"error":{"code":401,"message":"Authentication failed: GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE points to , but file does not exist","reason":"authError"}}
```
Exits immediately — no hang. But exit 0, reason "authError" not "AUTH_REQUIRED", no auth_methods array.

---

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `perl -e 'alarm(3); exec @ARGV' -- gws drive files list < /dev/null`
**Exit code:** 0
**Score:** 3/3

No stdin-reading commands. Input via --params/--json flags. No deadlock possible.

---

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws drive files list` (with expired reauth token)
**Exit code:** 0
**Score:** 0/3

**stdout:**
```
{"error":{"code":401,"message":"Authentication failed: ...invalid_rapt...","reason":"authError"}}
```
No CREDENTIALS_EXPIRED code. No reauth_command. No expired_at. Identical to permission denial.

---

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** long-running command observation (auth blocks); `gws --help | grep heartbeat`
**Score:** 1/3

No heartbeat, no explicit line-buffering. Single-shot API call model. Debug output has ANSI escape codes to stderr.

---

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `python3 -c "print('x'*70000)" | gws drive files list`
**Exit code:** 0
**Score:** 2/3

**stderr:**
```
BrokenPipeError: [Errno 32] Broken pipe  (from python3 side)
```
gws completed. No stdin data path for API operations — large stdin ignored. No --input-file, but no bidirectional pipe deadlock risk.

---

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws --help | grep -iE "editor|compose|write"`, write command with EDITOR=true
**Score:** 3/3

No editor-launching commands. Not applicable.

---

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws auth --help`
**Score:** 1/3

**stdout:**
```
login    Authenticate via OAuth2 (opens browser)
```
Browser opened on auth login. GOOGLE_WORKSPACE_CLI_TOKEN bypasses auth. No --print-url or --no-browser flag.

---

## §71 — Non-Interactive Installation Absence
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `brew info googleworkspace-cli`
**Score:** 1/3

Installed via Homebrew tap (googleworkspace-cli formula). brew install is non-interactive. Idempotent via brew upgrade. Not documented in AGENTS.md. Update 0.17.0 → 0.22.5 available.

---

## §74 — Credential Scope Declaration Absence
**Date:** 2026-05-14
**CLI version:** 0.17.0
**Check command:** `gws schema drive.files.list | python3 -c "...check scopes..."`
**Score:** 1/3

**stdout:**
```
scopes: ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.appdata', ...]  (8 scopes listed)
has required_scopes: False
```
`scopes` lists all possible OAuth scopes per method (not minimal required). No required_scopes, no over-privileged warning.
