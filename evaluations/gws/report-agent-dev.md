# gws — Integration Guide

**Generated:** 2026-05-14
**CLI version:** 0.17.0
**Scope:** Critical (22 failure modes)

## Invocation Invariants

These constraints must hold on every call to `gws`, regardless of language or framework:

```
binary:  gws
         (/opt/homebrew/bin/gws)
stdin:   closed (subprocess.DEVNULL or equivalent)
timeout: 30s external — gws has no --timeout flag
         macOS: perl -e 'alarm(30); exec @ARGV' -- gws <args>
         Python: subprocess.run([...], timeout=30)
env:     GOOGLE_WORKSPACE_CLI_TOKEN=<token>    # §45,§53,§64 — bypass stored creds; only safe headless auth method
output:  always parse stdout as JSON regardless of exit code
         exit 0 does NOT guarantee success — auth errors on list commands return exit 0
```

---

## Per-Failure-Mode Workarounds _(score < 3, sorted: severity desc, score asc)_

### §11 — Timeouts & Hanging Processes [Critical · 0/3]

**Gap:** No `--timeout` flag; network hangs block indefinitely.

**Workaround:**
Wrap every `gws` call with an external timeout. On macOS (no GNU `timeout`):

```python
import subprocess, json

def gws(args: list[str], timeout: int = 30) -> dict:
    cmd = ["perl", "-e", f"alarm({timeout}); exec @ARGV", "--"] + ["gws"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if result.returncode == 14:  # SIGALRM
        raise TimeoutError(f"gws {args[0]} timed out after {timeout}s")
    return json.loads(result.stdout)
```

**Limitation:** External timeout cannot distinguish network hang from a legitimately slow large response. Set timeout generously (60s) for large Drive file operations.

---

### §13 — Partial Failure & Atomicity [Critical · 0/3]

**Gap:** Workflow commands (`gws workflow +standup-report`, etc.) have no partial failure structure. On failure, the agent does not know what completed.

**Workaround:**
Break multi-step workflows into individual `gws` calls with explicit state tracking:

```python
completed = []
steps = [
    (["drive", "files", "list", "--params", '{"pageSize":5}'], "list_files"),
    (["gmail", "users", "messages", "list", "--params", '{"userId":"me","maxResults":5}'], "list_emails"),
]
for args, step_name in steps:
    result = gws(args)
    if not result.get("ok", True) and "error" not in result:
        # gws does not return ok field — check for error key
        raise RuntimeError(f"Step {step_name} failed: {result}")
    completed.append(step_name)
```

Do not use `gws workflow` commands in production agent code — their partial failure behavior is opaque.

**Limitation:** Individual API calls are still not atomic. If a multi-step workflow requires rollback, implement compensating actions manually.

---

### §25 — Prompt Injection via Output [Critical · 0/3]

**Gap:** gws returns external data (email bodies, document content, file names) as raw strings. LLMs consuming this output may follow injected instructions.

**Workaround:**
Never pass raw gws output containing user-generated content directly to the LLM. Extract the specific fields your agent needs and pass only those:

```python
result = gws(["gmail", "users", "messages", "get",
              "--params", json.dumps({"userId": "me", "id": msg_id})])
# BAD: pass entire result to LLM
# GOOD: extract only what you need
email = {
    "from": result.get("data", result).get("payload", {}).get("headers", []),
    "subject": ...,   # extract from headers
    # do NOT include "body" unless required
}
```

Tag external data before including in LLM context:
```python
EXTERNAL_MARKER = "\n--- EXTERNAL DATA (untrusted) ---\n"
llm_context = f"Email subject: {EXTERNAL_MARKER}{subject}\n--- END EXTERNAL DATA ---"
```

**Limitation:** Manual extraction is fragile and easy to miss. Any field that contains user-generated content (file names, email subjects, document titles) is a potential injection vector.

---

### §53 — Credential Expiry Mid-Session [Critical · 0/3]

**Gap:** Expired credentials return `reason: "authError"` — identical to permanent permission denial. No `CREDENTIALS_EXPIRED` code, no `reauth_command`, no `expired_at`.

**Workaround:**
Detect expiry by inspecting the raw error message for OAuth expiry signals, and treat all auth errors as potentially retriable once:

```python
import subprocess, json, os, re

EXPIRY_SIGNALS = re.compile(r"invalid_rapt|invalid_grant|token.*expired|reauth", re.IGNORECASE)
PERM_SIGNALS   = re.compile(r"insufficient_scope|access_denied|forbidden", re.IGNORECASE)

def gws_with_auth_retry(args: list[str], max_retries: int = 1) -> dict:
    for attempt in range(max_retries + 1):
        result = subprocess.run(
            ["gws"] + args,
            capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30
        )
        data = json.loads(result.stdout)
        error = data.get("error", {})
        msg = str(error.get("message", ""))

        if not error:
            return data  # success

        if PERM_SIGNALS.search(msg):
            raise PermissionError(f"Permanent auth failure: {error}")

        if EXPIRY_SIGNALS.search(msg) and attempt < max_retries:
            # Attempt refresh — requires user to re-run gws auth login
            raise RuntimeError(
                f"Credentials expired (invalid_rapt). Run `gws auth login` to refresh, "
                f"then set GOOGLE_WORKSPACE_CLI_TOKEN. Error: {msg}"
            )

        raise RuntimeError(f"gws call failed: {error}")
    raise RuntimeError("Auth retry limit reached")
```

**Limitation:** Cannot auto-refresh credentials because `gws auth login` requires a browser. Expiry forces human intervention. Mitigate by using short-lived tokens with early-refresh logic, or set `GOOGLE_WORKSPACE_CLI_TOKEN` from a token-refresh service.

---

### §1 — Exit Codes & Status Signaling [Critical · 1/3]

**Gap:** Auth errors exit 0 on list commands, exit 2 on get commands. Never branch on exit code alone.

**Workaround:**
Always parse stdout as JSON and check for an `error` key, regardless of exit code:

```python
import subprocess, json

result = subprocess.run(
    ["gws"] + args, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30
)
data = json.loads(result.stdout)
if "error" in data:
    code = data["error"].get("code")
    reason = data["error"].get("reason", "")
    raise RuntimeError(f"gws error {code} ({reason}): {data['error']['message']}")
# success — use data directly
```

Map known numeric HTTP codes to actions:
```python
HTTP_TO_ACTION = {
    400: "fix_params",    # bad request — do not retry
    401: "auth_retry",   # auth failure — check token
    403: "escalate",     # forbidden — do not retry
    404: "not_found",    # resource does not exist
    429: "backoff",      # rate limited — retry after delay
}
```

**Limitation:** The `error.code` field contains HTTP codes (400, 401), not symbolic names. Map defensively — future gws versions may change this.

---

### §2 — Output Format & Parseability [Critical · 1/3]

**Gap:** No top-level `ok`/`data`/`meta` envelope. Success response structure varies by API method. Prose error line also emitted to stderr.

**Workaround:**
Normalize the response before use. On success, gws returns the raw API response directly (no `ok` wrapper); on error it returns `{"error": {...}}`:

```python
def parse_gws_output(stdout: str, stderr: str) -> dict:
    data = json.loads(stdout)
    if "error" in data:
        return {"ok": False, "error": data["error"]}
    # Success: raw API response — wrap it
    return {"ok": True, "data": data}

# stderr contains a duplicate prose error line — ignore it
# stderr may also contain ANSI debug output if GOOGLE_WORKSPACE_CLI_LOG is set
```

**Limitation:** Success response structure is the raw Google API JSON, which varies per method. Use `gws schema <method>` to discover the response schema before parsing.

---

### §12 — Idempotency & Safe Retries [Critical · 1/3]

**Gap:** No `--idempotency-key` and no `effect` field. Retrying mutating calls (send email, create event) may cause duplicates.

**Workaround:**
For mutating operations, run a pre-flight read to confirm the action is needed before writing:

```python
# Before creating a calendar event, check if it already exists
existing = gws(["calendar", "events", "list", "--params",
                json.dumps({"calendarId": "primary", "q": event_title})])
if existing.get("items"):
    return existing["items"][0]  # already exists — skip create

# Only create if not found
return gws(["calendar", "events", "insert", "--json", json.dumps(event_body),
            "--params", '{"calendarId":"primary"}'])
```

Track operation IDs in your agent's state to detect duplicates:
```python
if operation_id in completed_operations:
    return completed_operations[operation_id]
```

**Limitation:** Read-before-write has a TOCTOU race. This is best-effort deduplication, not true idempotency. For critical write operations (financial, email), require human confirmation before first attempt.

---

### §23 — Side Effects & Destructive Operations [Critical · 1/3]

**Gap:** `--dry-run` validates locally but does not return a `would_delete` envelope showing what would be affected. No `danger_level` in schema.

**Workaround:**
Always run `--dry-run` before destructive commands and confirm the target before proceeding:

```python
# Step 1: dry-run to see what would happen
dry = gws(["drive", "files", "delete", "--params",
           json.dumps({"fileId": file_id}), "--dry-run"])
# dry-run exits 0 but does not show "would_delete" — it only validates params

# Step 2: fetch the file metadata first to confirm identity
meta = gws(["drive", "files", "get", "--params",
            json.dumps({"fileId": file_id, "fields": "id,name,size"})])
file_name = meta.get("name", "unknown")

# Step 3: require explicit confirmation in agent plan before deleting
```

**Limitation:** `--dry-run` only validates request params locally — it does not contact the API or confirm the resource exists. Always fetch resource metadata before destructive calls.

---

### §34 — Shell Injection via Agent-Constructed Commands [Critical · 1/3]

**Gap:** No metacharacter validation at CLI layer. LLM-generated resource IDs or query values passed directly to `--params` reach the API unvalidated.

**Workaround:**
Validate all LLM-generated values before passing to `--params` or `--json`:

```python
import re, urllib.parse

SAFE_ID_RE   = re.compile(r'^[\w\-\.]+$')
TRAVERSAL_RE = re.compile(r'\.\./|%[0-9a-fA-F]{2}|[?#;|<>`$]')

def safe_param(value: str, field_name: str) -> str:
    if TRAVERSAL_RE.search(value):
        raise ValueError(f"Unsafe value for {field_name}: {value!r}")
    return value

# Usage
file_id = safe_param(llm_generated_file_id, "fileId")
params = json.dumps({"fileId": file_id})
```

Never use `shell=True` when calling gws. Always use exec-array form:
```python
subprocess.run(["gws", "drive", "files", "get", "--params", params], ...)
# NOT: subprocess.run(f"gws drive files get --params '{params}'", shell=True)
```

**Limitation:** Validation catches common patterns but cannot anticipate all LLM hallucination patterns. Review `--params` values from LLM output before any write or delete call.

---

### §42 — Debug / Trace Mode Secret Leakage [Critical · 1/3]

**Gap:** `GOOGLE_WORKSPACE_CLI_LOG=gws=debug` emits ANSI codes to stderr. No auto-redaction of token values in debug output.

**Workaround:**
Never set `GOOGLE_WORKSPACE_CLI_LOG` in production agent code. If debugging is required, strip ANSI codes from captured stderr before logging:

```python
import re
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text)

result = subprocess.run(["gws"] + args, capture_output=True, text=True)
clean_stderr = strip_ansi(result.stderr)
```

Never log the value of `GOOGLE_WORKSPACE_CLI_TOKEN` or any `*_SECRET` environment variable. Redact before logging:
```python
def redact_env(env: dict) -> dict:
    return {k: "[REDACTED]" if any(s in k.upper() for s in ["TOKEN","SECRET","KEY","PASSWORD"]) else v
            for k, v in env.items()}
```

**Limitation:** Cannot prevent the token from appearing in debug output if `GOOGLE_WORKSPACE_CLI_LOG` is set externally. Ensure debug logging is disabled in production via environment controls.

---

### §43 — Tool Output Result Size Unboundedness [Critical · 1/3]

**Gap:** `--page-limit 10` caps list pagination but not individual response body size. Large documents or emails return in full.

**Workaround:**
Always request minimal fields from the API using the `fields` parameter to limit response size:

```python
# Instead of returning the full file metadata
gws(["drive", "files", "list", "--params", '{"pageSize":10}'])

# Request only the fields you need
gws(["drive", "files", "list", "--params",
     json.dumps({"pageSize": 10, "fields": "files(id,name,size,modifiedTime)"})])
```

For document/email bodies, always paginate or truncate:
```python
# Gmail: only get metadata, not body, unless needed
gws(["gmail", "users", "messages", "get",
     "--params", json.dumps({"userId": "me", "id": msg_id, "format": "metadata"})])

# Get body separately and truncate
body_result = gws(["gmail", "users", "messages", "get",
                   "--params", json.dumps({"userId": "me", "id": msg_id, "format": "full"})])
body = body_result.get("payload", {}).get("body", {}).get("data", "")[:10000]  # 10KB cap
```

Pre-estimate output size for large operations before running.

**Limitation:** The `fields` parameter is a Google API feature, not a gws feature. Some APIs do not support it. Body size limits are manual — gws does not enforce them automatically.

---

### §45 — Headless Authentication / OAuth Browser Flow Blocking [Critical · 1/3]

**Gap:** Auth errors exit 0 (not 8). No `AUTH_REQUIRED` code and no `auth_methods` array.

**Workaround:**
Pre-check authentication before any command sequence using `gws auth status`:

```python
def verify_auth() -> bool:
    result = subprocess.run(
        ["gws", "auth", "status"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=10
    )
    try:
        status = json.loads(result.stdout)
        return status.get("token_valid", False)
    except json.JSONDecodeError:
        return False

if not verify_auth():
    raise RuntimeError(
        "gws authentication required. Set GOOGLE_WORKSPACE_CLI_TOKEN or run "
        "`gws auth login` in an interactive session, then export the token."
    )
```

Set `GOOGLE_WORKSPACE_CLI_TOKEN` from a token service to bypass stored credentials entirely:
```python
env = {**os.environ, "GOOGLE_WORKSPACE_CLI_TOKEN": token_service.get_token()}
subprocess.run(["gws", ...], env=env, ...)
```

**Limitation:** `gws auth login` requires a browser; there is no headless device-code or service-account flow built into gws. For fully headless operation, obtain the OAuth token externally (e.g., using the Google Python client library) and pass via `GOOGLE_WORKSPACE_CLI_TOKEN`.

---

### §60 — OS Output Buffer Deadlock [Critical · 1/3]

**Gap:** Single-shot API calls; no heartbeat for workflow commands; ANSI in debug stderr.

**Workaround:**
For workflow commands that may take multiple seconds, set a generous timeout and run in a thread with progress logging:

```python
import subprocess, threading, time

def run_with_progress(args: list[str], timeout: int = 60) -> dict:
    result_holder = {}
    def _run():
        r = subprocess.run(["gws"] + args, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=timeout)
        result_holder["result"] = r

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    elapsed = 0
    while t.is_alive():
        time.sleep(5); elapsed += 5
        print(f"[{elapsed}s] gws {args[0]} still running...", flush=True)
    t.join()
    return json.loads(result_holder["result"].stdout)
```

**Limitation:** No built-in heartbeat from gws; the polling above is agent-side only. Long-running `gws workflow` commands are opaque — no step-level progress.

---

### §64 — Headless Display and GUI Launch Blocking [Critical · 1/3]

**Gap:** `gws auth login` opens a browser; no `--print-url` flag.

**Workaround:**
Never call `gws auth login` from agent code. Obtain auth tokens externally and inject via env var:

```python
import os
# Obtain token outside agent (e.g., from a token service, Vault, or one-time human setup)
os.environ["GOOGLE_WORKSPACE_CLI_TOKEN"] = get_token_from_service()

# All subsequent gws calls will use this token
```

For CI environments, use a service account token generated via the Google Cloud SDK:
```bash
# One-time human setup:
gcloud auth print-access-token --scopes=https://www.googleapis.com/auth/drive.readonly
# → export as GOOGLE_WORKSPACE_CLI_TOKEN in CI secrets
```

**Limitation:** `GOOGLE_WORKSPACE_CLI_TOKEN` accepts only OAuth2 access tokens (short-lived, ~1hr). Service accounts require generating tokens via the Google auth library, not via `gws auth login`. There is no service-account JSON key support built into gws.

---

### §71 — Non-Interactive Installation Absence [Critical · 1/3]

**Gap:** Install via Homebrew is non-interactive but not documented in AGENTS.md. Version 0.17.0 is outdated (0.22.5 available).

**Workaround:**
Use this non-interactive install sequence in CI/agent setup scripts:

```bash
# Install (non-interactive, idempotent)
brew install googleworkspace-cli

# Verify
gws --version   # exits 0 if installed correctly

# Auth (must be done once in an interactive session before agent use)
# Then export token for headless agent use:
export GOOGLE_WORKSPACE_CLI_TOKEN=$(gws auth export --json | jq -r '.access_token')
```

Update to 0.22.5: `brew upgrade googleworkspace-cli`

**Limitation:** Homebrew install is macOS-only. Linux/container environments require the binary to be downloaded directly from the GitHub releases page — no package manager support is documented.

---

### §74 — Credential Scope Declaration Absence [Critical · 1/3]

**Gap:** `gws schema` returns all possible OAuth scopes, not minimal required scopes. No `check-permissions` command. Agents may use over-privileged credentials.

**Workaround:**
Manually specify the minimal scopes when creating OAuth credentials via `gws auth login`:

```bash
# Request only the scopes needed for your workflow
gws auth login --scopes https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/gmail.readonly

# Or use service-level restriction
gws auth login -s drive,gmail --readonly
```

Before any agentic workflow, run `gws auth status` and verify the active scopes match the minimum required:
```python
status = gws(["auth", "status"])
active_scopes = status.get("scopes", [])
required = {"https://www.googleapis.com/auth/drive.readonly"}
if not required.issubset(set(active_scopes)):
    raise RuntimeError(f"Missing required scopes: {required - set(active_scopes)}")
```

**Limitation:** gws has no `required_scopes` per command. The scope list from `gws schema` shows all scopes that *could* work, not the minimal set. Manual scope management is required until gws adds `required_scopes` to schema output.

---

### §10 — Interactivity & TTY Requirements [Critical · 2/3]

**Gap:** No `--non-interactive` flag. gws does not hang on stdin=DEVNULL for API commands, but `gws auth login` opens browser without TTY check.

**Workaround:**
Always pass `stdin=subprocess.DEVNULL`. Never call `gws auth login` from agent code (see §64 workaround).

```python
subprocess.run(["gws"] + args, stdin=subprocess.DEVNULL, capture_output=True, text=True)
```

**Limitation:** No hang risk on current API commands, but the `--non-interactive` flag is absent, so future commands that add prompts would hang without this workaround.

---

### §24 — Authentication & Secret Handling [Critical · 2/3]

**Gap:** Credentials via env vars only (correct). No `--secret-from-file` flag for container environments.

**Workaround:**
Load token from a secrets file at runtime and inject via env var (rather than mounting as env var directly):

```python
import os
token = open("/run/secrets/gws-token").read().strip()
env = {**os.environ, "GOOGLE_WORKSPACE_CLI_TOKEN": token}
subprocess.run(["gws", ...], env=env, stdin=subprocess.DEVNULL)
```

**Limitation:** Token is briefly in memory but not exposed via process table or CLI flags. Ensure the secrets file has appropriate permissions (chmod 600).

---

### §61 — Bidirectional Pipe Payload Deadlock [Critical · 2/3]

**Gap:** No stdin data path means no pipe deadlock risk. However, very large `--json` string arguments (spreadsheet batch updates, etc.) may exceed OS argument limits.

**Workaround:**
For large request bodies, write to a temp file and pass via shell substitution is unsafe. Instead, keep payloads under 64KB in `--json` or use the Sheets/Docs API directly for bulk operations:

```python
import json, os

body = {"values": large_2d_array}  # may be large
body_str = json.dumps(body)

if len(body_str) > 65536:
    raise ValueError(
        f"Request body {len(body_str)} bytes exceeds safe --json arg size. "
        "Split the operation into smaller batches."
    )

gws(["sheets", "spreadsheets", "values", "append",
     "--params", json.dumps({"spreadsheetId": sid, "range": "Sheet1"}),
     "--json", body_str])
```

**Limitation:** No `--json-file` flag exists — large payloads must be batched or sent via the Google API Python client directly.

---

## No Action Needed

§37 (REPL Triggering), §50 (Stdin Deadlock), §62 (Editor Trap) — score 3/3, no workaround required
