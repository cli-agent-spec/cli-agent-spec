# cube — Fix Report

**Generated:** 2026-08-06
**CLI version:** 1.7.16
**Scope:** Critical severity
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | 2 | 11 | 9 | 0 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §10 — Interactivity & TTY Requirements  [Critical · 0/3]

**Gap:** With closed stdin and `CI=true`, `cube login --url ...` launched the browser path and was still polling with no new output after the five-second check window; it required manual cancellation

**Solutions:**
**Always provide non-interactive flags:**
```bash
tool deploy --non-interactive
tool deploy --yes          # auto-confirm all prompts
tool deploy --no-input     # fail immediately if input would be needed
tool init --defaults       # use defaults, skip all prompts
```

**Detect non-interactive context and adapt:**
```python
import sys
if not sys.stdin.isatty():
    # non-interactive mode: use defaults, fail on ambiguity
    # never prompt
```

**Fail fast instead of hanging:**
```bash
$ tool deploy --no-input
Error: Config file not found. Run `tool init` first or provide --config.
exit 4   # precondition not met
# ← agent gets an immediate, actionable error instead of a hang
```

**For framework design:**
- Auto-detect `sys.stdin.isatty()` and set `--non-interactive` implicitly
- Never use pagers; respect `NO_COLOR`, `TERM=dumb`, `CI` env vars
- Any command with a confirmation prompt MUST have a `--yes`/`--force` flag
- Document which commands are interactive in help text
- Set `PAGER=cat` and `GIT_PAGER=cat` in agent execution environments

**Requirements that address this:**


---

### §11 — Timeouts & Hanging Processes  [Critical · 0/3]

**Gap:** `--timeout 2` is unsupported; a request whose server withheld its response was still active with no output after three seconds and required manual cancellation, with no structured timeout or partial progress

**Solutions:**
**Built-in timeout flags:**
```bash
tool operation --timeout 30s        # fail after 30 seconds
tool operation --connect-timeout 5s # specifically for connection phase
```

**Progress heartbeats to stderr:**
```bash
$ tool long-operation --output json
# stderr:
[  2s] Starting...
[  5s] Phase 1/3: downloading (23%)
[ 10s] Phase 1/3: downloading (67%)
[ 15s] Phase 2/3: processing
# stdout (only on completion):
{"ok": true, "data": {...}}
```

**Emit partial results before timeout:**
```json
{
  "ok": false,
  "partial": true,
  "data": {"processed": 42, "total": 100},
  "error": {"code": "TIMEOUT", "message": "Operation timed out after 30s"},
  "resume_token": "abc123"   // allows resuming if supported
}
```

**For framework design:**
- Every command has a default timeout; `--timeout 0` means no timeout (must be explicit)
- Timeout exits with a specific code (e.g., `7`) and always emits JSON error
- Provide `--heartbeat-interval` to control stderr progress frequency
- Track and report wall time in every JSON response's `meta.duration_ms`

**Requirements that address this:**


---

### §12 — Idempotency & Safe Retries  [Critical · 0/3]

**Gap:** The same mutating request was attempted twice with one idempotency key; both invocations rejected `--idempotency-key` at parse time, so Cube provides no CLI-level retry identity, noop effect, or universal dry-run

**Solutions:**
**Idempotency keys:**
```bash
tool create-order --amount 100 --idempotency-key "order-$(date +%s)-$RANDOM"
# Server deduplicates based on key
# Safe to retry indefinitely
```

**Declare operation effect in output:**
```json
{
  "ok": true,
  "effect": "created",        // "created" | "updated" | "noop" | "deleted"
  "data": {"id": 42}
}
```

```json
{
  "ok": true,
  "effect": "noop",
  "reason": "Already at version 1.2.3",
  "data": {"current_version": "1.2.3"}
}
```

**`--dry-run` flag for all mutating commands:**
```bash
tool deploy --version 1.2.3 --dry-run
# Output:
{
  "ok": true,
  "effect": "would_create",
  "changes": ["would update service to 1.2.3", "would restart 2 instances"]
}
```

**For framework design:**
- Mark commands as `safe` (read-only, always idempotent) or `unsafe` (mutating)
- Require `--idempotency-key` for all `unsafe` commands, or generate one automatically
- Emit `effect` field in all responses
- Implement `--dry-run` as a framework-level feature, not per-command

**Requirements that address this:**


---

### §23 — Side Effects & Destructive Operations  [Critical · 0/3]

**Gap:** `--dry-run` was rejected, while the same DELETE against the local mock executed without confirmation and returned a deletion result; no danger declaration, preview, or explicit destructive confirmation exists

**Solutions:**
**Explicit destructive flag:**
```bash
tool delete-account --user 42 --confirm-destructive
# Without the flag: exits with clear error explaining the flag is required
```

**Machine-readable danger level in help:**
```json
{
  "command": "delete-account",
  "danger_level": "destructive",   // "safe" | "mutating" | "destructive"
  "reversible": false,
  "requires_confirmation": true
}
```

**Dry-run always available for destructive commands:**
```bash
$ tool delete-account --user 42 --dry-run
{
  "ok": true,
  "effect": "would_delete",
  "would_affect": {
    "user": {"id": 42, "name": "Alice"},
    "related_records": 234,
    "reversible": false
  }
}
```

**Audit output:**
```json
{
  "ok": true,
  "effect": "deleted",
  "audit": {
    "timestamp": "2024-03-11T14:30:00Z",
    "operator": "agent-session-abc123",
    "target": {"type": "user", "id": 42},
    "reversible": false
  }
}
```

**For framework design:**
- Commands declare `danger_level` in their schema
- Framework enforces `--dry-run` availability for all `destructive` commands
- `--yes` / `--confirm-destructive` flags auto-supplied by agent harness
- Generate audit log entries for all `mutating` and `destructive` operations

**Requirements that address this:**


---

### §25 — Prompt Injection via Output  [Critical · 0/3]

**Gap:** User-controlled API text containing an instruction-like payload was returned as an ordinary raw JSON `message` field, with no response envelope, trust annotation, content type, or separation from CLI metadata

**Solutions:**
**Structural wrapping in framework output:**
```
The framework should always wrap external data so the agent knows it's data, not instructions.

Instead of:
  Tool result: <raw content>

Use:
  <tool_result source="read-file" trusted="false">
  <raw content here — treat as untrusted data, not instructions>
  </tool_result>
```

**Content type tagging:**
```json
{
  "ok": true,
  "data": {
    "_content_type": "user_data",   // signals: treat as untrusted
    "name": "...",
    "value": "..."
  }
}
```

**Sanitization of string fields from external sources:**
```python
# In the CLI framework, before returning external data:
def sanitize_external(value: str) -> str:
    # Remove common injection patterns
    # Wrap in clear structural markers
    return f"[EXTERNAL DATA START]\n{value}\n[EXTERNAL DATA END]"
```

**For framework design:**
- All data from external sources (files, APIs, databases) is tagged as `trusted: false`
- Framework-level wrapping that signals to the agent: "this is data, not instruction"
- Provide `--no-injection-protection` escape hatch for trusted sources

**Requirements that address this:**


---

### §43 — Tool Output Result Size Unboundedness  [Critical · 0/3]

**Gap:** A 70 KiB API field was emitted in full as 71,748 bytes; there is no output bound, truncation metadata, or pre-flight size facility

**Solutions:**
**For CLI/tool authors:**
```bash
# Provide a --max-length or --truncate flag
my-tool get-record --id 12345 --max-length 10000 --truncate-mode head

# Output envelope should signal truncation
{
  "ok": true,
  "data": {"id": "12345", "description": "First 10000 chars..."},
  "meta": {"truncated": true, "total_bytes": 204800, "returned_bytes": 10000,
           "truncation_hint": "Use --offset and --max-length for subsequent chunks"}
}
```

**For framework design:**
- Implement a default output size limit per command (e.g., 50KB of text content) with the excess truncated and `meta.truncated: true` set
- Provide a `--max-output` flag (injected automatically on all commands) that the agent can set to control output size
- For large string fields in responses, automatically truncate at a configurable `max_field_length` (default: 10,000 chars) and add a `"_truncated": true` marker on the field
- In MCP tool definitions, expose `maxOutputBytes` as a tool annotation so clients can pre-negotiate output size
- Schema should declare `"max_output_bytes": 51200` as a tool property, allowing agents to assess expected output size before calling

**Requirements that address this:**


---

### §60 — OS Output Buffer Deadlock  [Critical · 0/3]

**Gap:** The server flushed the first JSON fragment immediately, yet the CLI emitted no stdout after one second and released the entire response only after the server completed; no heartbeat or incremental JSON lines were present

**Solutions:**
**Unbuffer stdout explicitly in non-TTY mode:**
```python
# Python: disable buffering
import sys, os
if not sys.stdout.isatty():
    sys.stdout.reconfigure(line_buffering=True)
    # or: os.environ['PYTHONUNBUFFERED'] = '1'
```

```bash
# Wrapper: force unbuffered output
$ stdbuf -o0 my-tool migrate
$ unbuffer my-tool migrate   # via expect package
```

**Emit JSON heartbeats every N seconds for long operations:**
```json
{"status": "running", "step": "migrating table users", "elapsed_ms": 5000, "heartbeat": true}
```

**For framework design:**
- Framework MUST call `sys.stdout.reconfigure(line_buffering=True)` (Python) or `setvbuf(stdout, NULL, _IOLBF, 0)` (C) on startup when stdout is not a TTY
- Long-running commands MUST emit a JSON heartbeat object to stdout every configurable interval (default: 10s) so the agent has proof of life
- `PYTHONUNBUFFERED=1` and equivalent env vars MUST be set in the framework's bootstrap before any output

**Requirements that address this:**


---

### §64 — Headless Display and GUI Launch Blocking  [Critical · 0/3]

**Gap:** `cube login` invoked the platform browser command despite `CI=true`, closed stdin, isolated config, and `--json`; it then remained in the OAuth polling loop until manually cancelled, and the URL was ANSI-styled prose rather than JSON

**Solutions:**
**Detect headless environment and skip GUI operations:**
```python
import os, sys
def is_headless():
    return (
        not sys.stdout.isatty() or
        os.environ.get('CI') or
        not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY')
    )

if is_headless():
    # Skip browser launch; emit URL in JSON instead
    return {"ok": True, "data": {"url": url, "opened": False, "open_hint": f"open {url}"}}
```

**Schema declares GUI operations:**
```json
{
  "name": "deploy",
  "gui_operations": ["browser_open"],
  "headless_behavior": "emit_url_in_output"
}
```

**Wrap graphical commands in headless fallback:**
```bash
# Tool wraps GUI launch:
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo '{"url": "'"$URL"'", "note": "open this URL in your browser"}'
else
    xdg-open "$URL"
fi
```

**For framework design:**
- Framework MUST detect headless environment on startup and set `framework.headless = true`
- Commands that declare `gui_operations` MUST implement headless fallbacks; framework raises a registration error if `headless_behavior` is not declared
- In headless mode, browser/GUI launch attempts MUST be replaced with URL/path emission in the JSON response rather than blocking

**Requirements that address this:**


---

### §74 — Credential Scope Declaration Absence  [Critical · 0/3]

**Gap:** Neither `--schema` nor `check-permissions` exists, and official CLI docs do not map command groups to minimum API-key/OAuth scopes; agents cannot compare required, active, or excessive privileges

**Solutions:**
**Declare `required_scopes` per command in `--schema` output:**
```json
{
  "command": "issue list",
  "danger_level": "safe",
  "required_scopes": ["repo:read"],
  "flags": { "repo": { "type": "string", "required": true } }
}
```

**Provide a `check-permissions` pre-flight command:**
```bash
$ tool check-permissions --for issue:list
{
  "ok": true,
  "required_scopes": ["repo:read"],
  "active_scopes": ["repo:read", "repo:write"],
  "over_privileged": true,
  "warnings": ["Active credential has scopes beyond what this command needs"]
}
```

**Warn in `warnings[]` when active credential exceeds declared scopes:**
```json
{
  "ok": true,
  "data": { ... },
  "warnings": [
    "Credential has write access; this command only requires read — consider a scoped token"
  ]
}
```

**Document minimal credential recipes in AGENTS.md:**
```markdown
## Minimal credentials by workflow

| Workflow | Required scopes | How to create |
|----------|----------------|---------------|
| Read issues and PRs | `repo:read` | Fine-grained PAT → Contents: Read |
| Comment on issues | `repo:read`, `issues:write` | Fine-grained PAT → Issues: Read+Write |
| Never needed by agents | `delete_repo`, `admin:org` | Do not grant |
```

**For framework design:**
- Commands declare `required_scopes: []` at registration; framework enforces that the field is present
- Framework compares `required_scopes` against the credential's active scopes at invocation and emits structured warnings on over-privilege
- `check-permissions` is a built-in command that accepts `--for <command>` and returns a machine-readable scope report
- Credentials with `admin` or `owner`-level scopes trigger an unconditional warning when used in agent sessions

**Requirements that address this:**


---

### §1 — Exit Codes & Status Signaling  [Critical · 1/3]

**Gap:** Missing arguments used clap exit 2, but both a 404 resource and a connection failure exited 1; codes are not documented and no JSON error body embeds the code

**Solutions:**
**For CLI tool authors:**
```
Exit code conventions to follow:
  0  = success, operation completed as intended
  1  = general error (use sparingly — be specific)
  2  = misuse / bad arguments (before operation starts)
  3  = operation started but failed mid-way
  4  = precondition not met (dependency missing, not initialized)
  5  = not found (the thing you asked about doesn't exist)
  6  = conflict / already exists
  7  = timeout
  8  = permission denied
  9  = rate limited / quota exceeded
```

**Separate "not found" from "error":**
```bash
# Bad: exits 1 for both "error" and "not found"
tool get-user --id 123
# exit 1

# Good: exits 5 for "not found", 1 for actual errors
tool get-user --id 123
# exit 5  ← agent knows to stop, not retry
```

**For CLI framework design:**
- Define a standard exit code table in your framework
- Provide typed exit code constants (not magic numbers)
- Make every command document its possible exit codes in `--help`
- Support `--exit-on-warning` flag to make strict mode opt-in

**Requirements that address this:**


---

### §2 — Output Format & Parseability  [Critical · 1/3]

**Gap:** Global `--json` produced valid raw success JSON, but without `ok`/`data`; a 404 under the same flag emitted prose only on stderr, so the output contract changes between success and failure

**Solutions:**
**Machine-readable output flag:**
```bash
# Always provide a structured output mode
tool list-users --output json
tool list-users --output jsonl   # one JSON object per line for streaming
tool list-users --output tsv     # tab-separated, good for piping
tool list-users --output plain   # minimal, no decoration (for humans too)
```

**JSON output schema:**
```json
{
  "ok": true,
  "data": [...],      // always present, even if empty array/null
  "error": null,      // always present
  "meta": {
    "count": 2,
    "duration_ms": 45
  }
}
```

**On failure:**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "User with id=999 does not exist",
    "details": {}
  }
}
```

**Rules for agent-compatible output:**
1. Same schema whether 0, 1, or N results
2. No prose mixed into data output (prose goes to stderr)
3. No color codes in `--output json` mode (detect `NO_COLOR` env var)
4. Numbers always in invariant locale (`.` decimal, no thousands separator)
5. Dates always in ISO 8601 (`2024-03-11T14:30:00Z`)
6. Boolean as `true`/`false`, never `yes`/`no`/`1`/`0` in JSON mode

**For framework design:**
- Auto-detect output format based on `--output` flag or `CI=true` env
- Provide output formatters as first-class framework primitives
- Emit a JSON schema for every command's output via `--output-schema`

**Requirements that address this:**


---

### §13 — Partial Failure & Atomicity  [Critical · 1/3]

**Gap:** A deploy transaction failed deliberately at file upload after hashing and transaction start; stderr named the file and failing endpoint, but `--json` still returned no `partial`, completed-step list, rollback state, or resume token

**Solutions:**
**Structured partial failure output:**
```json
{
  "ok": false,
  "partial": true,
  "completed_steps": ["backup", "apply_schema"],
  "failed_step": "migrate_data",
  "error": {"code": "DISK_FULL", "message": "..."},
  "resume_from": "migrate_data",
  "rollback_available": true
}
```

**Batch result per item:**
```json
{
  "ok": false,
  "partial": true,
  "results": [
    {"id": 1, "ok": true,  "effect": "sent"},
    {"id": 2, "ok": true,  "effect": "sent"},
    {"id": 3, "ok": false, "error": {"code": "INVALID_EMAIL"}},
    {"id": 4, "ok": true,  "effect": "sent"},
    {"id": 5, "ok": false, "error": {"code": "RATE_LIMITED"}}
  ],
  "summary": {"total": 5, "succeeded": 3, "failed": 2}
}
```

**Resumable commands:**
```bash
tool migrate-database --resume-from migrate_data
# Only runs remaining steps
```

**For framework design:**
- All multi-step commands emit a step manifest at start
- Each step emits its result as it completes (streaming JSON lines)
- Final summary always includes `completed`, `failed`, `skipped` counts
- `--rollback-on-failure` flag as standard option

**Requirements that address this:**


---

### §24 — Authentication & Secret Handling  [Critical · 1/3]

**Gap:** A fake credential supplied through `CUBE_API_KEY` was not echoed, but Cube also accepts secrets through `--token`/`login --api-key` and maps authentication failure to generic exit 1 rather than a defined auth code

**Solutions:**
**Prefer environment variables:**
```bash
TOOL_API_TOKEN=sk-... tool deploy
# Convention: TOOL_VARNAME
```

**Support secrets files:**
```bash
tool deploy --token-file /run/secrets/api-token
# File path, not the value
```

**Never echo secrets in output or errors:**
```json
// Bad
{"error": "Invalid token: sk-prod-abc123xyz789"}

// Good
{"error": {"code": "AUTH_TOKEN_INVALID", "message": "Token is invalid or expired"}}
```

**Secret output handling:**
```json
{
  "ok": true,
  "data": {
    "key_id": "key-42",          // safe to log
    "key_preview": "sk-prod-abc...xyz",  // truncated
    "secret": "REDACTED"          // never return in --output json
  },
  "secret_written_to": "/run/secrets/key-42"  // written to file instead
}
```

**For framework design:**
- Framework-level redaction: any field named `*token*`, `*secret*`, `*password*`, `*key*` is auto-redacted in logs
- Provide `--secret-from-env VAR_NAME` and `--secret-from-file PATH` as standard flags
- Document which env vars each command reads for credentials

**Requirements that address this:**


---

### §34 — Shell Injection via Agent-Constructed Commands  [Critical · 1/3]

**Gap:** `acme%2Fwidgets` was accepted and sent to the API; `../../etc/test` reached filesystem handling and produced only a prose path error, with no structured validation or correction suggestion

**Solutions:**
**For CLI consumers (agents):**
```python
import shlex

# Safe: never interpolate into shell strings
subprocess.run(["git", "commit", "-m", message])  # ✓ list form

# Validate before passing: reject traversal and metacharacter patterns
import re
SAFE_VALUE_RE = re.compile(r'^[^;&|<>`$\\\n\r]+$')
if not SAFE_VALUE_RE.match(message):
    raise ValueError(f"Unsafe value for --message: {message!r}")
```

**For CLI authors / MCP wrapper authors:**
```typescript
import shellEscape from 'shell-escape';

// In MCP tool handler: receive typed args from JSON, construct safely
const args = ["git", "commit", "-m", request.params.arguments.message];
const result = await execFile(args[0], args.slice(1));  // ✓ never shell=True
```

**For framework design:**
- Reject arguments containing `../`, `./`, percent-encoded characters (`%[0-9a-fA-F]{2}`), embedded query string markers (`?`, `#`), and shell metacharacters (`;`, `&&`, `||`, backtick, `$()`) by default
- Provide a whitelist-based argument sanitizer as a framework primitive: `@arg(pattern=r'^[\w\-\.]+$')`
- Default to `subprocess.run(args_list)` (never `shell=True`) in all generated subprocess calls
- Apply jpoehnelt Axis 5 level 2 checks at argument parsing time, before any execution
- MCP wrappers: always receive arguments as typed JSON objects, never concatenate into shell strings

**Requirements that address this:**


---

### §42 — Debug / Trace Mode Secret Leakage  [Critical · 1/3]

**Gap:** `--debug` is unsupported and the parser did not echo the fake token, but the documented `--token` option exposed the credential verbatim in the process table; no safe trace mode or sensitive schema exists

**Solutions:**
**For CLI authors:**
```python
from pydantic import SecretStr

class DeployConfig(BaseModel):
    api_key: SecretStr  # repr never shows value; model_dump() returns "[REDACTED]"
    region: str

# Argparse: use action to mask value in namespace repr
import argparse
class SecretAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
    def __repr__(self):
        return f"{self.dest}=[REDACTED]"
```

**For framework design:**
- Apply name-based heuristics to automatically redact argument values whose names match `token|secret|password|key|credential|auth|apikey` in all trace/debug output
- Never echo argument values in error messages for arguments marked `sensitive=True` or matching the redaction pattern
- Provide a framework-level `--trace-safe` mode that produces a trace with sensitive fields replaced by `[REDACTED]`
- For `--trace` or `--debug` modes: require explicit `--no-redact` opt-out to expose sensitive values
- Use environment variables (not CLI flags) as the preferred injection mechanism for secrets — they are not visible in `process.argv` or process tables
- Document in `--schema` output which arguments are marked sensitive: `"sensitive": true`

**Requirements that address this:**


---

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · 1/3]

**Gap:** An authenticated command with no credentials exited immediately, but even `--json` produced only a prose stderr error with exit 1 and no `AUTH_REQUIRED` code or `auth_methods` array

**Solutions:**
**For CLI authors:**
```python
# Check for non-interactive auth options before attempting browser flow
if not sys.stdin.isatty():
    # Non-interactive mode: check for token in env vars
    token = os.environ.get("MY_TOOL_TOKEN") or os.environ.get("MY_TOOL_API_KEY")
    if not token:
        print(json.dumps({"ok": False, "error": {
            "code": "AUTH_REQUIRED",
            "message": "No credentials found. Set MY_TOOL_TOKEN environment variable.",
            "auth_methods": [
                {"type": "env_var", "name": "MY_TOOL_TOKEN", "description": "API token"},
                {"type": "env_var", "name": "MY_TOOL_API_KEY", "description": "Legacy API key"}
            ]
        }}))
        sys.exit(8)  # PERMISSION_DENIED exit code
    authenticate_with_token(token)
else:
    # Interactive: offer browser flow
    launch_browser_auth_flow()
```

**For framework design:**
- Any command that triggers authentication must check `isatty()` and return a structured `AUTH_REQUIRED` error in non-interactive mode, never hang
- The `AUTH_REQUIRED` error must include `auth_methods` — an array of structured objects describing how to authenticate non-interactively (env var name, config file format, token endpoint)
- Schema output should include `"requires_auth": true` and `"auth_methods": [...]` so agents can determine how to authenticate before first invocation
- Support `--token` / `--api-key` as universal authentication flags that bypass stored credentials for headless use
- Credential expiry should produce `{"code": "AUTH_EXPIRED"}` distinct from `AUTH_REQUIRED`, with instructions for renewal that work in headless mode

**Requirements that address this:**


---

### §50 — Stdin Consumption Deadlock  [Critical · 1/3]

**Gap:** `-d -` with closed stdin failed immediately rather than hanging, but returned a generic prose JSON-parse error with exit 1 instead of a structured `STDIN_REQUIRED` error and hint

**Solutions:**
**Non-TTY stdin reads must fail immediately with exit 4:**
```json
{
  "ok": false,
  "error": {
    "code": "STDIN_REQUIRED",
    "message": "Argument '--ids' requires input but stdin is not a TTY and no value was provided.",
    "hint": "Pass --ids <value> or pipe data: echo '123' | my-tool delete --ids -"
  }
}
```

**Schema must declare all stdin-reading paths:**
```json
{
  "args": [
    {
      "name": "ids",
      "stdin_fallback": true,
      "stdin_format": "newline-separated IDs",
      "non_tty_behavior": "fail_with_exit_4"
    }
  ]
}
```

**For framework design:**
- All stdin reads must be declared in the command schema; undeclared stdin reads are a framework error
- In non-TTY mode, the framework wraps `stdin.read()` calls with an immediate-fail guard that exits 4 with a structured error listing the flag to pass instead
- The `--schema` output for every command must indicate which args accept stdin as input and what format is expected

**Requirements that address this:**


---

### §53 — Credential Expiry Mid-Session  [Critical · 1/3]

**Gap:** A mocked 401 was described as “session expired” with a re-login hint, but only in prose; there was no structured expiry code, timestamp, or reauthentication field, and exit 1 was generic

**Solutions:**
**Auth errors MUST distinguish expiry from permission denial:**
```json
{
  "ok": false,
  "error": {
    "code": "CREDENTIALS_EXPIRED",
    "message": "Access token expired at 2024-03-11T14:15:00Z.",
    "expired": true,
    "expired_at": "2024-03-11T14:15:00Z",
    "retryable": true,
    "reauth_command": "tool auth refresh",
    "reauth_env_var": "TOOL_TOKEN"
  }
}
```

**For framework design:**
- Add `exit 10` to the standard exit code table: `10 = credentials expired (retryable with refresh)`. Exit 8 = permanent permission denied
- Framework MUST intercept HTTP 401/403 responses and attempt to classify expiry vs permission denial before surfacing the error
- `error.reauth_command` is a mandatory field for all auth errors — the exact command to run to recover credentials

**Requirements that address this:**


---

### §61 — Bidirectional Pipe Payload Deadlock  [Critical · 1/3]

**Gap:** A 70,014-byte stdin JSON object was accepted and a 71,727-byte response was emitted successfully, but no stdin size limit or `STDIN_TOO_LARGE` signal exists; `-d @file.json` is the documented file alternative

**Solutions:**
**Use temporary files for large payloads instead of pipes:**
```bash
# Avoid: pipe large data
echo "$large_json" | my-tool transform

# Good: use file reference
echo "$large_json" > /tmp/input.json
my-tool transform --input-file /tmp/input.json > result.json
```

**Schema declares maximum stdin payload size:**
```json
{
  "stdin_input": {
    "max_bytes": 65536,
    "overflow_flag": "--input-file",
    "overflow_hint": "For payloads >64KB, use --input-file <path> instead of stdin"
  }
}
```

**Framework enforces size limit on stdin reads:**
```python
# Framework reads stdin with size limit:
data = sys.stdin.buffer.read(MAX_STDIN_BYTES)
if len(data) >= MAX_STDIN_BYTES:
    exit_with_error("STDIN_TOO_LARGE", "Payload exceeds 64KB. Use --input-file instead.")
```

**For framework design:**
- Framework MUST enforce a maximum stdin payload size (default: 64KB) and fail with exit 2 if exceeded, directing the caller to use `--input-file` instead
- The `--input-file` flag MUST be auto-generated by the framework for any command that accepts stdin input
- Framework MUST document the pipe buffer limit prominently in the agent integration guide

**Requirements that address this:**


---

### §71 — Non-Interactive Installation Absence  [Critical · 2/3]

**Gap:** The official README documents a non-interactive installer; two isolated runs both exited 0 and `cube --version` returned `Cube CLI 1.7.16`, but no `AGENTS.md` documents the agent install and verification contract

**Solutions:**
**For CLI authors:**

Document a fully non-interactive install command in AGENTS.md:

```bash
# In AGENTS.md — exact non-interactive install command agents must use
## Installation
pip install my-cli==2.1.0        # exact version pin
my-cli --version                  # verify install succeeded
```

Design installation to be non-interactive by default:
- Accept license terms implicitly when `--yes` or `CI=true` is detected
- Move post-install configuration to first-use, with `--non-interactive` producing a JSON error rather than a wizard
- Use package manager flags: `pip install --yes`, `apt-get install -y`, `brew install --quiet`
- Document any system dependency with its non-interactive install command

Make installation idempotent — running the install command twice must succeed:

```bash
# Idempotent: second run must exit 0
pip install my-cli==2.1.0   # first run: installs
pip install my-cli==2.1.0   # second run: already satisfied, exit 0
```

Provide a health-check command agents can run after install to confirm the binary is functional:

```bash
my-cli --version             # exits 0, prints version string
my-cli doctor --json         # optional: structured health check
```

**For framework designers:**

Provide a `--non-interactive` flag that suppresses all post-install prompts and fails fast with a JSON error if any required configuration is absent.

**Requirements that address this:**


---

## Already Passing

§37, §62  _(score 3/3 — no action needed)_
