# docuseal-cli - Fix Report

**Generated:** 2026-05-20
**CLI version:** 1.0.3
**Scope:** all
**In findings:** 71 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Indeterminate (?) |
|---|---:|---:|---:|---:|
| Critical | 5 | 6 | 11 | 0 |
| High | 3 | 11 | 21 | 0 |
| Medium | 1 | 3 | 10 | 0 |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §1 - Exit Codes & Status Signaling  [Critical · 0/3]

**Gap:** Failures observed with generic exit 1; no documented semantic exit-code table or JSON error body.

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

---

**Requirements that address this:**
- REQ-F-001 (P0) - Standard Exit Code Table [Tier: F]
- REQ-F-002 (P0) - Exit Code 2 Reserved for Validation Failures [Tier: F]
- REQ-C-001 (P0) - Command Declares Exit Codes [Tier: C]

---

### §11 - Timeouts & Hanging Processes  [Critical · 0/3]

**Gap:** Network failure produced an uncaught Node stack trace; no timeout flag or `TIMEOUT` JSON.

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
- REQ-F-011 (P0) - Default Timeout Per Command [Tier: F]
- REQ-F-012 (P0) - Timeout Exit Code and JSON Error [Tier: F]
- REQ-F-039 (P1) - Duration Tracking in Response Meta [Tier: F]
- REQ-F-078 (P2) - Retry Count in Response Meta [Tier: F]
- REQ-C-012 (P0) - Commands with Network I/O Support --timeout [Tier: C]
- REQ-O-012 (P2) - --heartbeat-interval Flag [Tier: O]

---

### §12 - Idempotency & Safe Retries  [Critical · 0/3]

**Gap:** Mutating commands have no idempotency key or effect/noop field.

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
- REQ-C-003 (P0) - Mutating Commands Declare effect Field [Tier: C]
- REQ-C-007 (P1) - Mutating Commands Accept --idempotency-key [Tier: C]
- REQ-C-028 (P1) - ALREADY_EXISTS Response Pattern [Tier: C]

---

### §13 - Partial Failure & Atomicity  [Critical · 0/3]

**Gap:** No partial-failure/resume protocol.

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
- REQ-C-008 (P1) - Multi-Step Commands Emit Step Manifest [Tier: C]
- REQ-C-009 (P1) - Multi-Step Commands Report completed/failed/skipped [Tier: C]
- REQ-O-010 (P2) - --resume-from Flag for Multi-Step Commands [Tier: O]
- REQ-O-011 (P2) - --rollback-on-failure Flag [Tier: O]

---

### §23 - Side Effects & Destructive Operations  [Critical · 0/3]

**Gap:** Destructive archive operations have no `--dry-run` or machine-readable danger declaration.

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
- REQ-C-002 (P0) - Command Declares Danger Level [Tier: C]
- REQ-C-004 (P0) - Destructive Commands Must Support --dry-run [Tier: C]
- REQ-O-021 (P0) - --confirm-destructive Flag [Tier: O]

---

### §24 - Authentication & Secret Handling  [Critical · 0/3]

**Gap:** Secrets can be supplied via hidden `--api-key` CLI flag; no standard redaction framework.

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
- REQ-F-034 (P1) - Secret Field Auto-Redaction in Logs [Tier: F]
- REQ-C-016 (P1) - Secrets Accepted Only via Env Var or File [Tier: C]
- REQ-O-022 (P1) - --secret-from-env / --secret-from-file Flags [Tier: O]

---

### §25 - Prompt Injection via Output  [Critical · 0/3]

**Gap:** External API data is returned raw without a trusted/untrusted envelope.

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

---

**Requirements that address this:**
- REQ-F-035 (P1) - External Data Trust Tagging [Tier: F]
- REQ-O-023 (P3) - --no-injection-protection Flag [Tier: O]

---

### §43 - Tool Output Result Size Unboundedness  [Critical · 0/3]

**Gap:** No output limit, truncation metadata, or schema max-output declaration.

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
- Implement a default output size limit per command (e.g., 50KB of text content) with the excess truncated and `meta.truncated: true` set.
- Provide a `--max-output` flag (injected automatically on all commands) that the agent can set to control output size.
- For large string fields in responses, automatically truncate at a configurable `max_field_length` (default: 10,000 chars) and add a `"_truncated": true` marker on the field.
- In MCP tool definitions, expose `maxOutputBytes` as a tool annotation so clients can pre-negotiate output size.
- Schema should declare `"max_output_bytes": 51200` as a tool property, allowing agents to assess expected output size before calling.

**Requirements that address this:**
- REQ-F-052 (P0) - Response Size Hard Cap with Truncation Indicator [Tier: F]

---

### §53 - Credential Expiry Mid-Session  [Critical · 0/3]

**Gap:** No distinct credential-expiry code, reauth command, or expiry metadata.

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
- Add `exit 10` to the standard exit code table: `10 = credentials expired (retryable with refresh)`. Exit 8 = permanent permission denied.
- Framework MUST intercept HTTP 401/403 responses and attempt to classify expiry vs permission denial before surfacing the error.
- `error.reauth_command` is a mandatory field for all auth errors — the exact command to run to recover credentials.

**Requirements that address this:**
- REQ-F-063 (P1) - Credential Expiry Structured Error [Tier: F]

---

### §60 - OS Output Buffer Deadlock  [Critical · 0/3]

**Gap:** No streaming protocol or heartbeat for long-running commands.

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
- Framework MUST call `sys.stdout.reconfigure(line_buffering=True)` (Python) or `setvbuf(stdout, NULL, _IOLBF, 0)` (C) on startup when stdout is not a TTY.
- Long-running commands MUST emit a JSON heartbeat object to stdout every configurable interval (default: 10s) so the agent has proof of life.
- `PYTHONUNBUFFERED=1` and equivalent env vars MUST be set in the framework's bootstrap before any output.

**Requirements that address this:**
- REQ-F-053 (P0) - Stdout Unbuffering in Non-TTY Mode [Tier: F]
- REQ-O-038 (P1) - --heartbeat-ms Flag for Long-Running Commands [Tier: O]

---

### §74 - Credential Scope Declaration Absence  [Critical · 0/3]

**Gap:** No machine-readable required scopes or permission check command.

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
- REQ-C-029 (P0) - Command Declares Required Scopes [Tier: C]
- REQ-O-047 (P0) - tool check-permissions Built-In Command [Tier: O]

---

### §2 - Output Format & Parseability  [Critical · 1/3]

**Gap:** API commands emit JSON on success, but there is no `--output json` and no `ok`/`data`/`error` envelope; many errors are prose/stack traces.

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

---

> **Merged from §48:** The following content was originally a separate challenge.
> It is consolidated here because it describes a specific case of the same root problem.

**Requirements that address this:**
- REQ-F-003 (P0) - JSON Output Mode Auto-Activation [Tier: F]
- REQ-F-004 (P0) - Consistent JSON Response Envelope [Tier: F]
- REQ-F-005 (P0) - Locale-Invariant Serialization [Tier: F]
- REQ-F-074 (P1) - JSON Null/Absent/Empty Convention [Tier: F]
- REQ-O-001 (P0) - --output Format Flag [Tier: O]
- REQ-O-042 (P2) - Output Format Environment Variable Default [Tier: O]

---

### §10 - Interactivity & TTY Requirements  [Critical · 1/3]

**Gap:** `configure` has flags for non-interactive setup, but the prompt path still runs in non-TTY and can exit 0 without configuring.

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

---

> **Merged from §36:** The following content was originally a separate challenge.
> It is consolidated here because it describes a specific case of the same root problem.

**Requirements that address this:**
- REQ-F-009 (P0) - Non-Interactive Mode Auto-Detection [Tier: F]
- REQ-F-010 (P0) - Pager Suppression [Tier: F]
- REQ-F-046 (P0) - Pager Environment Variable Suppression [Tier: F]
- REQ-C-005 (P0) - Interactive Commands Must Support --yes / --non-interactive [Tier: C]

---

### §34 - Shell Injection via Agent-Constructed Commands  [Critical · 1/3]

**Gap:** No shell execution path found, but suspicious name/path values are not validated into structured errors.

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
- Reject arguments containing `../`, `./`, percent-encoded characters (`%[0-9a-fA-F]{2}`), embedded query string markers (`?`, `#`), and shell metacharacters (`;`, `&&`, `||`, backtick, `$()`) by default.
- Provide a whitelist-based argument sanitizer as a framework primitive: `@arg(pattern=r'^[\w\-\.]+$')`.
- Default to `subprocess.run(args_list)` (never `shell=True`) in all generated subprocess calls.
- Apply jpoehnelt Axis 5 level 2 checks at argument parsing time, before any execution.
- MCP wrappers: always receive arguments as typed JSON objects, never concatenate into shell strings.

**Requirements that address this:**
- REQ-F-044 (P0) - Shell Argument Escaping Enforcement [Tier: F]
- REQ-C-019 (P1) - Subprocess-Invoking Commands Declare Argument Schema [Tier: C]

---

### §45 - Headless Authentication / OAuth Browser Flow Blocking  [Critical · 1/3]

**Gap:** Missing auth exits immediately, but as an uncaught stack trace rather than `AUTH_REQUIRED` with `auth_methods`.

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
- Any command that triggers authentication must check `isatty()` and return a structured `AUTH_REQUIRED` error in non-interactive mode, never hang.
- The `AUTH_REQUIRED` error must include `auth_methods` — an array of structured objects describing how to authenticate non-interactively (env var name, config file format, token endpoint).
- Schema output should include `"requires_auth": true` and `"auth_methods": [...]` so agents can determine how to authenticate before first invocation.
- Support `--token` / `--api-key` as universal authentication flags that bypass stored credentials for headless use.
- Credential expiry should produce `{"code": "AUTH_EXPIRED"}` distinct from `AUTH_REQUIRED`, with instructions for renewal that work in headless mode.

**Requirements that address this:**
- REQ-C-021 (P0) - Auth Commands Declare Headless Mode Support [Tier: C]
- REQ-O-033 (P0) - --headless and --token-env-var Flags for Auth Commands [Tier: O]

---

### §42 - Debug / Trace Mode Secret Leakage  [Critical · 2/3]

**Gap:** No debug/trace mode found to leak secrets, but no sensitive schema/redaction declaration exists.

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
- Apply name-based heuristics to automatically redact argument values whose names match `token|secret|password|key|credential|auth|apikey` in all trace/debug output.
- Never echo argument values in error messages for arguments marked `sensitive=True` or matching the redaction pattern.
- Provide a framework-level `--trace-safe` mode that produces a trace with sensitive fields replaced by `[REDACTED]`.
- For `--trace` or `--debug` modes: require explicit `--no-redact` opt-out to expose sensitive values.
- Use environment variables (not CLI flags) as the preferred injection mechanism for secrets — they are not visible in `process.argv` or process tables.
- Document in `--schema` output which arguments are marked sensitive: `"sensitive": true`.

**Requirements that address this:**
- REQ-F-051 (P0) - Debug and Trace Mode Secret Redaction [Tier: F]

---

### §71 - Non-Interactive Installation Absence  [Critical · 2/3]

**Gap:** README documents non-interactive npm install/use; no AGENTS.md install protocol and global install idempotency was not exercised.

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
- REQ-O-044 (P1) - Non-Interactive Install Command Documentation [Tier: O]

---

### §15 - Race Conditions & Concurrency  [High · 0/3]

**Gap:** No lock protocol for mutating/config operations.

**Solutions:**
**Session-isolated temp paths:**
```bash
tool process --input data.csv --session-id $AGENT_SESSION_ID
# Uses /tmp/tool/$AGENT_SESSION_ID/result.json automatically
```

**Advisory locking with timeout:**
```bash
$ tool build
Error: {
  "code": "LOCK_HELD",
  "message": "Another build is running (pid 1234, started 30s ago)",
  "suggestion": "Wait for it to complete or use --force-unlock if process is dead",
  "retry_after_ms": 5000
}
```

**For framework design:**
- All temp files scoped to `$TOOL_SESSION_ID` or a random run ID
- Lock acquisition has a timeout and emits `retry_after_ms`
- Config mutations use atomic write (write to temp, rename)

**Requirements that address this:**
- REQ-F-032 (P2) - Session-Scoped Temp Directory [Tier: F]
- REQ-F-033 (P2) - Lock Acquisition with Timeout and retry_after_ms [Tier: F]
- REQ-F-070 (P1) - Atomic Write via Rename [Tier: F]

---

### §16 - Signal Handling & Graceful Cancellation  [High · 0/3]

**Gap:** No SIGTERM partial-result protocol.

**Solutions:**
**Register signal handlers that emit JSON then exit cleanly:**
```python
import signal, sys, json, atexit

_cleanup_done = False

def handle_sigterm(signum, frame):
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    # Emit partial result to stdout before exit
    result = {
        "ok": False,
        "partial": True,
        "error": {"code": "CANCELLED", "message": "Process received SIGTERM"},
        "completed_steps": get_completed_steps(),
        "resume_from": get_current_step()
    }
    sys.stdout.write(json.dumps(result) + "\n")
    sys.stdout.flush()
    cleanup_temp_files()
    release_locks()
    sys.exit(143)  # 128 + SIGTERM

signal.signal(signal.SIGTERM, handle_sigterm)
atexit.register(cleanup_temp_files)
```

**SIGPIPE handling:**
```python
# Python: suppress BrokenPipeError on stdout
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
# or wrap all stdout writes in try/except BrokenPipeError
```

**Advertise cancellation support in schema:**
```json
{
  "command": "migrate-database",
  "cancellable": true,
  "cancel_signal": "SIGTERM",
  "cancel_grace_period_ms": 5000,
  "on_cancel": "emits partial result + rollback available"
}
```

**For framework design:**
- Framework installs SIGTERM and SIGPIPE handlers automatically for every command
- Every command declares a `cleanup()` hook called on signal
- Grace period: framework sends SIGTERM, waits `cancel_grace_period_ms`, then SIGKILL
- Partial result always emitted to stdout before exit, even on cancellation

**Requirements that address this:**
- REQ-F-013 (P0) - SIGTERM Handler Installation [Tier: F]
- REQ-F-014 (P0) - SIGPIPE Handler Installation [Tier: F]
- REQ-F-069 (P0) - SIGINT Handler Installation [Tier: F]
- REQ-C-017 (P1) - Commands Register cleanup() Hook [Tier: C]

---

### §18 - Error Message Quality  [High · 0/3]

**Gap:** Validation/auth/file/network errors are prose or stack traces without `code`, `suggestion`, or context.

**Solutions:**
**Structured error format:**
```json
{
  "ok": false,
  "error": {
    "code": "CONNECTION_REFUSED",      // machine-readable code
    "message": "Cannot connect to database at db.example.com:5432",
    "cause": "Connection refused (ECONNREFUSED)",
    "suggestion": "Verify the database is running: `tool db status`",
    "docs_url": "https://docs.example.com/errors/CONNECTION_REFUSED",
    "context": {
      "host": "db.example.com",
      "port": 5432,
      "timeout_ms": 5000
    }
  }
}
```

**Error code taxonomy:**
```
{DOMAIN}_{NOUN}_{CONDITION}

Examples:
  DB_CONNECTION_REFUSED
  AUTH_TOKEN_EXPIRED
  FILE_CONFIG_NOT_FOUND
  API_RATE_LIMIT_EXCEEDED
  INPUT_PARAM_INVALID
```

**Suggestion field for common errors:**
```json
"suggestion": "Run `tool login` to refresh your credentials"
"suggestion": "Use --force to overwrite existing file"
"suggestion": "Check network connectivity with: ping db.example.com"
```

**For framework design:**
- All errors MUST have a `code` (machine) and `message` (human)
- `suggestion` field is encouraged for recoverable errors
- Never emit raw stack traces to stdout; log them to stderr or a file
- Provide an error code registry queryable via `tool errors list`

**Requirements that address this:**
- REQ-C-013 (P0) - Error Responses Include Code and Message [Tier: C]

---

### §19 - Retry Hints in Error Responses  [High · 0/3]

**Gap:** No `retryable` or `retry_after_ms` fields.

**Solutions:**
**`retryable` and `retry_after_ms` in every error:**
```json
{
  "ok": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "API rate limit exceeded",
    "retryable": true,
    "retry_after_ms": 5000,
    "retry_strategy": "exponential_backoff",
    "max_retries": 3
  }
}
```

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email address",
    "retryable": false,
    "fix_required": "Correct the --email argument before retrying"
  }
}
```

**Retry classification taxonomy:**
```
retryable: false   → VALIDATION_ERROR, NOT_FOUND, PERMISSION_DENIED, CONFLICT
retryable: true    → TIMEOUT, SERVICE_UNAVAILABLE, RATE_LIMITED, NETWORK_ERROR
retryable: "maybe" → INTERNAL_ERROR (sometimes transient, sometimes not)
```

**Exit code alignment:**
```
Exit 9 (RATE_LIMITED)       → always retryable, check retry_after_ms
Exit 7 (TIMEOUT)            → retryable, immediate retry ok
Exit 8 (PERMISSION_DENIED)  → never retryable without auth change
Exit 2 (BAD_ARGS)           → never retryable without arg change
```

**For framework design:**
- Every error class has a default `retryable` value in the error registry
- `retry_after_ms` sourced from response header (Retry-After) when available
- Framework-level retry logic: honor `retryable` and `retry_after_ms` automatically
- Emit `attempt` and `max_attempts` in `meta` so agents know retry history

**Requirements that address this:**
- REQ-C-014 (P1) - Error Responses Include retryable and retry_after_ms [Tier: C]

---

### §22 - Schema Versioning & Output Stability  [High · 0/3]

**Gap:** No `meta.schema_version` in responses.

**Solutions:**
**Schema version in every response:**
```json
{
  "ok": true,
  "meta": {
    "schema_version": "2.1.0",
    "tool_version": "2.4.1"
  },
  "data": {...}
}
```

**Deprecation warnings before removal:**
```json
{
  "ok": true,
  "data": {
    "name": "Alice",        // deprecated, use full_name
    "full_name": "Alice"    // new field
  },
  "warnings": [
    {
      "code": "FIELD_DEPRECATED",
      "message": "Field 'name' is deprecated. Use 'full_name' instead.",
      "removed_in": "3.0.0"
    }
  ]
}
```

**Stability tiers declared in schema:**
```json
{
  "fields": {
    "id":         {"stability": "stable"},
    "full_name":  {"stability": "stable"},
    "score":      {"stability": "experimental", "may_change": true},
    "_internal":  {"stability": "private", "do_not_depend_on": true}
  }
}
```

**Version negotiation:**
```bash
tool get-user --id 42 --schema-version 1
# Returns v1-compatible output even from v2 tool
# Allows gradual migration
```

**For framework design:**
- `meta.schema_version` in every response (semver)
- `--schema-version` flag to request compatible output
- Deprecation warnings 2 major versions before removal
- `tool changelog --output json` lists all schema changes by version

**Requirements that address this:**
- REQ-F-022 (P1) - Schema Version in Every Response [Tier: F]
- REQ-F-023 (P1) - Tool Version in Every Response [Tier: F]
- REQ-F-075 (P1) - Subcommand Additive Stability [Tier: F]
- REQ-O-014 (P2) - --schema-version Compatibility Flag [Tier: O]
- REQ-O-029 (P2) - tool changelog Built-In Command [Tier: O]

---

### §26 - Stateful Commands & Session Management  [High · 0/3]

**Gap:** Implicit global config/env state; no `status --output json` context report.

**Solutions:**
**Explicit context per invocation:**
```bash
tool deploy --context production           # never rely on implicit current context
tool list-resources --token $TOKEN         # stateless auth per-call
tool --config /tmp/agent-session-42.json deploy  # isolated config file
```

**State inspection command:**
```bash
$ tool status --output json
{
  "logged_in": true,
  "user": "alice@example.com",
  "current_context": "production",
  "token_expires": "2024-03-11T16:00:00Z"
}
```

**For framework design:**
- Provide `--config` / `--context` override for every command
- Default to stateless operation; state is opt-in
- Document all global state locations in `tool status --show-state-files`

**Requirements that address this:**
- REQ-O-024 (P1) - --context / --config Override Flag [Tier: O]
- REQ-O-028 (P2) - tool status Built-In Command [Tier: O]

---

### §31 - Network Proxy Unawareness  [High · 0/3]

**Gap:** Network errors include no proxy context.

**Solutions:**
**Respect all standard proxy env vars:**
```python
import urllib.request
# Python requests library — auto-reads env vars:
import requests
session = requests.Session()
# requests automatically reads: HTTP_PROXY, HTTPS_PROXY, NO_PROXY
# This is the default — don't override it with proxies={}

# For lower-level: urllib respects env vars by default
# Never do: urllib.request.urlopen(url, context=ssl_context_that_ignores_env)
```

**Use system certificate store:**
```python
import ssl, certifi
# Use certifi for cross-platform cert bundle
ctx = ssl.create_default_context(cafile=certifi.where())
# Or respect REQUESTS_CA_BUNDLE env var
```

**Include proxy info in network error output:**
```json
{
  "ok": false,
  "error": {
    "code": "NETWORK_CONNECTION_FAILED",
    "message": "Cannot reach api.example.com",
    "network_context": {
      "proxy_used": "http://proxy.corp.example.com:8080",
      "proxy_source": "HTTPS_PROXY env var",
      "no_proxy": "localhost,internal.corp",
      "ssl_verify": true
    },
    "suggestion": "Check proxy connectivity: curl -x $HTTPS_PROXY https://api.example.com"
  }
}
```

**`--proxy` explicit override:**
```bash
tool fetch-data --proxy http://proxy.corp.example.com:8080
tool fetch-data --no-proxy   # bypass proxy for this call
```

**For framework design:**
- Framework HTTP client reads `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` automatically
- Network errors include `network_context` block showing proxy settings used
- `tool doctor` checks: can reach key endpoints with current proxy config
- `--proxy` and `--no-proxy` are framework-level flags on all network commands

**Requirements that address this:**
- REQ-F-036 (P1) - HTTP Client Proxy Environment Variable Compliance [Tier: F]
- REQ-F-037 (P1) - Network Error Context Block [Tier: F]
- REQ-O-019 (P2) - --proxy and --no-proxy Flags [Tier: O]

---

### §35 - Agent Hallucination Input Patterns  [High · 0/3]

**Gap:** Percent-encoded/path-like values are not rejected with structured validation suggestions.

**Solutions:**
**Rejecting traversal patterns:**
```python
import re, urllib.parse

def validate_resource_id(value: str) -> str:
    # Reject path traversal
    if '..' in value.split('/'):
        raise ValueError(f"Path traversal detected in resource ID: {value!r}")
    # Reject percent-encoding (when not expected)
    decoded = urllib.parse.unquote(value)
    if decoded != value:
        raise ValueError(f"Percent-encoded characters in resource ID: {value!r} (decoded: {decoded!r})")
    # Reject embedded query params
    if '?' in value or '#' in value:
        raise ValueError(f"Embedded URL metacharacters in: {value!r}")
    return value
```

**Error message for agent self-correction:**
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "field": "name",
    "message": "Resource ID contains percent-encoded characters. Pass the literal value without URL-encoding.",
    "input": "acme%2Fwidgets",
    "suggestion": "acme/widgets"
  }
}
```

**For framework design:**
- Implement an `agent_hardening=True` flag on `Argument` / `Option` declarations that enables the full Axis 5 level 2 check set by default.
- For string arguments representing names, IDs, or paths: reject `../`, `./`, `%XX` sequences, `?`, `#`, null bytes, and the string literals `"null"`, `"undefined"`, `"None"` by default (override with `allow_unsafe=True`).
- Error messages for these rejections must explain *why* the value was rejected in terms an LLM can act on — not just "invalid value."
- Include the decoded/normalized form in the error `suggestion` field so the agent can self-correct without a retry.
- Consider jpoehnelt's "agent is not a trusted operator" as a default security posture: apply stricter validation to agent-invoked CLIs than to human-interactive ones.

**Requirements that address this:**
- REQ-F-045 (P0) - Agent Hallucination Input Pattern Rejection [Tier: F]
- REQ-C-020 (P1) - Resource ID Fields Declare Validation Pattern [Tier: C]

---

### §38 - Runtime Dependency Version Mismatch  [High · 0/3]

**Gap:** No `engines` declaration or startup runtime-version JSON check.

**Solutions:**
**For CLI authors:**
```python
# Python: check version at startup, emit structured error
import sys, json
MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:
    print(json.dumps({"ok": False, "error": {
        "code": "RUNTIME_VERSION",
        "message": f"Requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+, found {sys.version}",
        "requirement": f"python>={MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
        "actual": sys.version
    }}))
    sys.exit(5)  # NOT_FOUND / precondition failure
```

```javascript
// Node.js: check version at top of entry file
const [major] = process.versions.node.split('.').map(Number);
if (major < 18) {
    process.stderr.write(JSON.stringify({ok: false, error: {
        code: "RUNTIME_VERSION",
        message: `Requires Node.js 18+, found ${process.versions.node}`,
    }}) + '\n');
    process.exit(5);
}
```

**For framework design:**
- Emit a structured `{"code": "RUNTIME_VERSION"}` error as the first output when minimum version check fails, before any other initialization.
- Include `"requirement"` and `"actual"` fields in the error so agents can surface the mismatch to operators.
- Expose minimum runtime requirements in `--schema` output: `"runtime": {"python": ">=3.10"}`.
- Prefer packaging tools as self-contained binaries when possible (PyInstaller, pkg for Node.js) to eliminate runtime dependency entirely.

**Requirements that address this:**
- REQ-O-031 (P1) - Dependency Version Matrix Declaration [Tier: O]

---

### §40 - parse() vs parseAsync() Silent Race Condition  [High · 0/3]

**Gap:** Source uses `program.parse()` with async action handlers.

**Solutions:**
**Detection (for agents):**
```python
# Commander.js tools: if exit code is 0 but expected output is absent, re-invoke with verbose flag
# or apply a short artificial wait after exit to see if async work completes (not reliable)
# Better: use --format json and check for explicit "ok: true" in output
```

**For CLI authors:**
```javascript
// Always use parseAsync() when any action handler is async
(async () => {
    program
        .command('deploy')
        .action(async (options) => {
            await deployToCloud(options);
            console.log(JSON.stringify({ok: true}));
        });
    await program.parseAsync();  // ✓ awaits async handlers
})();
```

**For framework design:**
- Auto-detect async action handlers and require `parseAsync()` (emit a compile-time or startup-time error if `parse()` is called with async handlers).
- TypeScript: use return-type overloading to make `parse()` return `void` for sync handlers and a compile error for async handlers, forcing `parseAsync()`.
- Runtime check: if any registered action handler is async and `parse()` is called, emit a warning to stderr: `"Warning: async action handler detected; use parseAsync() to ensure completion"`.
- Framework-level test harnesses should always use `parseAsync()` and await results.

**Requirements that address this:**
- REQ-F-049 (P1) - Async Command Handler Enforcement [Tier: F]

---

### §47 - MCP Wrapper Schema Staleness  [High · 0/3]

**Gap:** No MCP wrapper health, schema version, or stale-schema mapping.

**Solutions:**
**Wrapper health-check command:**
```typescript
// Add a schema validation tool to the MCP wrapper
server.tool("_wrapper_health", {}, async () => {
    const cliVersion = await execAndCapture("my-cli --version");
    const knownVersion = "2.3.1";  // version wrapper was written against
    return {
        content: [{type: "text", text: JSON.stringify({
            wrapper_schema_version: knownVersion,
            cli_actual_version: cliVersion.trim(),
            schema_may_be_stale: cliVersion.trim() !== knownVersion,
        })}]
    };
});
```

**Schema auto-generation from --help:**
```python
# Parse --help output to detect new flags not in wrapper schema
def detect_schema_drift(tool_name: str, wrapper_schema: dict) -> list[str]:
    help_output = subprocess.run([tool_name, "--help"], capture_output=True).stdout.decode()
    # Extract flags from help text using regex
    help_flags = set(re.findall(r'--(\w[\w-]*)', help_output))
    wrapper_flags = set(wrapper_schema["properties"].keys())
    new_flags = help_flags - wrapper_flags
    return list(new_flags)
```

**For framework design:**
- MCP wrapper generators should pin the `cli_version` in tool annotations and emit a `schema_stale` warning when the CLI version changes.
- Auto-generate MCP wrapper schemas from CLI `--help` or `--schema` JSON output (where available) rather than requiring manual authoring.
- Include a `_meta.schema_cli_version` field in tool results so agents can detect version mismatches.
- When an MCP tool call produces a non-zero exit code with "unknown option" or "unrecognized argument" in the error, the wrapper should emit `{"code": "SCHEMA_STALE", "hint": "The underlying CLI may have changed; wrapper schema may be outdated"}`.
- MCP protocol: add optional `toolSchemaVersion` annotation to tool definitions, allowing version-to-version compatibility tracking.

**Requirements that address this:**
- REQ-O-035 (P2) - tool mcp-validate Built-In Command [Tier: O]
- REQ-O-045 (P1) - Integration Artifact Version Declaration [Tier: O]

---

### §49 - Async Job / Polling Protocol Absence  [High · 0/3]

**Gap:** No async job/status protocol or distinct running/done exit codes.

**Solutions:**
**Async commands MUST return a typed job descriptor:**
```json
{
  "ok": true,
  "data": {
    "job_id": "dep_abc123",
    "status": "running",
    "terminal": false,
    "status_command": "tool job status dep_abc123",
    "cancel_command": "tool job cancel dep_abc123",
    "poll_interval_ms": 5000,
    "timeout_ms": 600000,
    "started_at": "2024-03-11T14:00:00Z"
  }
}
```

**Status command uses distinct exit codes:**
```
exit 0  = job complete (terminal, success)
exit 3  = job still running (non-terminal, poll again)
exit 4  = job failed (terminal, failure)
exit 7  = job timed out (terminal)
exit 5  = job ID not found / expired
```

**Terminal vs non-terminal distinction in response:**
```json
{ "status": "running", "terminal": false, "progress_pct": 60 }
{ "status": "complete", "terminal": true, "result": {...} }
```

**For framework design:**
- Provide a first-class `AsyncJob` return type; framework automatically generates `job status <id>` and `job cancel <id>` subcommands.
- The job descriptor schema (status_command, cancel_command, poll_interval_ms, timeout_ms) must be part of the standard response envelope for any async operation.
- Document the exit code contract for status commands prominently as part of the framework's standard.

**Requirements that address this:**
- REQ-C-022 (P0) - Async Commands Declare Job Descriptor Schema [Tier: C]
- REQ-O-038 (P1) - --heartbeat-ms Flag for Long-Running Commands [Tier: O]

---

### §54 - Conditional / Dependent Argument Requirements  [High · 0/3]

**Gap:** No machine-readable arg groups or all-at-once dependent-argument validation.

**Solutions:**
**Schema declares conditional requirement groups:**
```json
{
  "arg_groups": [
    {
      "condition": {"arg": "auth-type", "equals": "oauth"},
      "required": ["client-id", "client-secret"]
    }
  ]
}
```

**Phase 1 validation reports ALL missing co-requirements at once:**
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "missing_args": [
      {"name": "client-id", "reason": "required when --auth-type=oauth"},
      {"name": "client-secret", "reason": "required when --auth-type=oauth"}
    ]
  }
}
```

**For framework design:**
- Schema format MUST support `required_when` and `arg_groups` conditional dependency declarations.
- Phase 1 validation MUST evaluate all conditional requirements simultaneously and report all missing args in a single error response.

**Requirements that address this:**
- REQ-C-026 (P1) - Commands Declare Conditional Argument Dependencies [Tier: C]

---

### §55 - Silent Data Truncation  [High · 0/3]

**Gap:** No schema max lengths or `FIELD_TRUNCATED`/validation warning protocol.

**Solutions:**
**Truncated fields MUST appear in `warnings[]`:**
```json
{
  "ok": true,
  "warnings": [
    {
      "code": "FIELD_TRUNCATED",
      "field": "title",
      "original_length": 71,
      "truncated_to": 41
    }
  ]
}
```

**Better: reject at Phase 1 validation with field constraints from schema:**
```json
{ "name": "title", "type": "string", "max_length": 64 }
{ "name": "tags",  "type": "array",  "max_items": 10 }
```

**For framework design:**
- Schema MUST declare `max_length`, `max_items`, `max_bytes` for all bounded fields; Phase 1 rejects inputs exceeding these limits.
- If backend silently truncates anyway, framework MUST compare returned vs sent value and inject `FIELD_TRUNCATED` warning automatically.

**Requirements that address this:**
- REQ-F-064 (P1) - Output Truncation Detection and Warning [Tier: F]

---

### §56 - Exit Code Masking in Shell Pipelines  [High · 0/3]

**Gap:** No `ok`, `meta.ok`, or `meta.exit_code` fields.

**Solutions:**
**Primary defense: check `.ok` in the JSON envelope, not only the exit code:**
```bash
result=$(tool list-users)
echo "$result" | jq -e '.ok' > /dev/null || { echo "$result" | jq '.error'; exit 1; }
echo "$result" | jq '.data[].id'
```

**`meta.ok` mirrors top-level `ok` for pipeline detection:**
```json
{"ok": false, "meta": {"ok": false, "exit_code": 9}, "error": {...}}
```

**For framework design:**
- Document prominently: agents MUST check `.ok` in the JSON envelope, not only the exit code, when piping.
- Framework SHOULD write `TOOL_FAILED=1` to stderr on failure so pipeline callers can detect failure without `pipefail`.

**Requirements that address this:**
- REQ-F-065 (P0) - Pipeline Exit Code Propagation [Tier: F]

---

### §58 - Multi-Agent Concurrent Invocation Conflict  [High · 0/3]

**Gap:** Config writes use direct writes to shared config; no locking or conflict code.

**Solutions:**
**File locking for all config writes:**
```python
with framework.config_lock(timeout_ms=5000) as lock:
    config = lock.read()
    config['region'] = 'us-east-1'
    lock.write(config)
# If lock times out: exit 6 (conflict) with error.code: "CONCURRENT_MODIFICATION"
```

**Per-agent-instance state namespacing:**
```bash
$ tool --instance-id agent-1 config set region=us-east-1
# Writes to ~/.tool/instances/agent-1/config.json
```

**For framework design:**
- All config and state writes MUST use advisory file locking with configurable timeout (default 5s).
- Config writes MUST use atomic rename to prevent partial-write corruption.
- Framework MUST provide `--instance-id <id>` to namespace all per-instance state so parallel agents operate without interference.

**Requirements that address this:**
- REQ-O-036 (P1) - --instance-id Flag for Agent State Namespacing [Tier: O]

---

### §65 - Global Configuration State Contamination  [High · 0/3]

**Gap:** Config writes default to global user config without `--global` or write-scope metadata.

**Solutions:**
**Default all writes to local/session scope:**
```bash
# Bad: writes to global ~/.config/tool/config.json
$ tool config set region=us-east-1

# Good: writes to ./.tool-config (local, git-ignorable)
$ tool config set region=us-east-1
# Requires explicit --global flag for home-dir writes:
$ tool config set --global region=us-east-1
```

**Strict scope declaration in schema:**
```json
{
  "name": "config set",
  "write_scope": "local",   // "local" | "global" | "session"
  "global_flag": "--global",
  "danger_level": "mutating"
}
```

**Config write audit trail:**
```json
{
  "ok": true,
  "warnings": [
    {
      "code": "GLOBAL_CONFIG_MODIFIED",
      "path": "~/.config/tool/config.json",
      "key": "region",
      "previous_value": "eu-west-1",
      "new_value": "us-east-1"
    }
  ]
}
```

**For framework design:**
- Framework MUST default all config writes to the nearest `.tool-config` file in the working directory hierarchy, not to `~/.config/`.
- Global config writes MUST require an explicit `--global` flag and MUST emit a `GLOBAL_CONFIG_MODIFIED` warning in the JSON response.
- Auto-migrations MUST be opt-in: `tool migrate-config --confirm` rather than running silently on startup.

**Requirements that address this:**
- REQ-F-073 (P1) - Environment Variable Namespace Prefix [Tier: F]
- REQ-C-025 (P0) - Config-Writing Commands Declare Write Scope [Tier: C]

---

### §67 - Agent-Generated Input Syntax Rejection  [High · 0/3]

**Gap:** Strict JSON parse errors produce raw stack traces; no `INVALID_JSON` corrected input.

**Solutions:**
**Accept JSON5 / forgiving JSON for all structured inputs:**
```python
import json5  # pip install json5
config = json5.loads(user_input)
# Accepts: trailing commas, comments, unquoted keys, single quotes
```

**Normalize before parsing:**
```python
import re
def normalize_json(s):
    s = re.sub(r',\s*([}\]])', r'\1', s)   # remove trailing commas
    s = re.sub(r'//.*?$', '', s, flags=re.M)  # remove line comments
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)  # remove block comments
    return json.loads(s)
```

**Surface clear correction in error:**
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "Trailing comma at line 1, position 38.",
    "corrected_input": "{\"name\": \"prod\", \"region\": \"us-east-1\"}",
    "hint": "Remove trailing comma after last key-value pair."
  }
}
```

**For framework design:**
- Framework MUST use a forgiving JSON parser (JSON5 or equivalent) for all `--config`, `--filter`, `--data`, and `--raw-payload` flag inputs.
- When strict JSON is required (e.g., for schema validation), the framework normalizes the input before validation and emits the corrected form in the error if validation fails.
- The `corrected_input` field in parse errors enables agents to retry with minimal reasoning.

**Requirements that address this:**
- REQ-F-059 (P1) - JSON5 Input Normalization [Tier: F]

---

### §68 - Third-Party Library Stdout Pollution  [High · 0/3]

**Gap:** No stdout interception or warnings envelope.

**Solutions:**
**Framework-level stdout interception:**
```python
import sys, io

class StdoutInterceptor(io.TextIOWrapper):
    def write(self, data):
        if self._json_mode and not self._in_framework_output:
            # Route to stderr instead of stdout
            sys.stderr.write(f"[INTERCEPTED STDOUT]: {data}")
        else:
            super().write(data)

# Install before any imports:
sys.stdout = StdoutInterceptor(sys.stdout.buffer)
```

**Buffer stdout, validate before flushing:**
```python
# Collect all stdout writes; on command completion, validate that
# the buffer is valid JSON. If not, separate legitimate output from
# pollution and emit pollution as warnings[].
```

**Intercept at the file descriptor level:**
```python
import os
# Redirect fd 1 to a buffer; only framework's output() call writes to original fd 1
old_stdout_fd = os.dup(1)
os.dup2(pipe_write_fd, 1)
# After command completes, read buffer, filter non-JSON lines, emit as warnings
```

**For framework design:**
- Framework MUST intercept `sys.stdout` (Python) or `process.stdout` (Node.js) at startup, buffering all writes not made through the framework's `output()` API.
- Any stdout writes not from `output()` MUST be reclassified: moved to `warnings[]` if they are prose, or dropped with a `THIRD_PARTY_STDOUT` warning in debug mode.
- Framework MUST install the interceptor before any imports so that import-time prints are captured.

**Requirements that address this:**
- REQ-F-060 (P1) - Third-Party Stdout Interception [Tier: F]

---

### §70 - Single-Argument Arity Forcing Agent Loop Overhead  [High · 0/3]

**Gap:** Single-ID commands do not accept variadic IDs with per-item results.

**Solutions:**
**Accept variadic positional arguments for any command whose logic is item-by-item:**

```python
# argparse
parser.add_argument("paths", nargs="+", help="One or more paths to delete")

# Click
@click.argument("paths", nargs=-1, required=True)

# Clap (Rust)
#[arg(num_args = 1..)]
paths: Vec<PathBuf>,

# Cobra (Go)
Args: cobra.MinimumNArgs(1),
```

**Report per-item results so the agent can detect partial failure:**

```json
{
  "ok": true,
  "results": [
    {"path": "/notes/a.md", "ok": true},
    {"path": "/notes/b.md", "ok": false, "error": {"code": "NOT_FOUND", "message": "Path does not exist"}}
  ]
}
```

**Declare arity in the schema manifest so agents can pre-determine call structure:**

```json
{
  "name": "delete",
  "args": [
    {"name": "paths", "nargs": "+", "description": "Paths to delete"}
  ]
}
```

**For framework design:**
- Commands that perform the same stateless operation per item MUST accept `nargs="+"` (one or more) positional arguments
- Per-item results MUST be returned as an array even when a single path is passed, so the agent can parse the response uniformly
- The manifest's `args` array MUST include `nargs` (`"1"`, `"?"`, `"*"`, `"+"`); absence of `nargs` MUST be treated as `"1"` by agents
- Partial success MUST be reported per-item with a top-level `ok: false` when any item fails; the agent must not have to infer failure count from missing output

**Requirements that address this:**
_No direct requirement mapping found in requirements index._

---

### §72 - Integration Artifact Version Drift  [High · 0/3]

**Gap:** Skill metadata version `1.0.6` differs from binary/package version `1.0.3`, confirming integration artifact drift.

**Solutions:**
**For CLI authors:**

Include a version field in every integration artifact, matching the binary version exactly:

```yaml
# openapi.yaml
info:
  title: My CLI API
  version: "2.1.0"   # must match `my-cli --version` output exactly
```

```markdown
<!-- AGENTS.md -->
<!-- cli-version: 2.1.0 -->
```

Co-version artifacts with the binary — release them in the same CI pipeline, with the same version tag:

```yaml
# .github/workflows/release.yml
- name: Release binary and artifacts together
  run: |
    VERSION=$(my-cli --version)
    sed -i "s/version: .*/version: \"$VERSION\"/" openapi.yaml
    git commit -am "Release $VERSION"
    git tag $VERSION
```

If artifacts live in a separate package, version-lock it to the binary with an explicit compatibility field:

```yaml
# companion-package/package.json
{
  "name": "my-cli-openapi",
  "version": "2.1.0",
  "peerDependencies": {
    "my-cli": "2.1.0"
  }
}
```

**For framework designers:**

Generate integration artifacts automatically from the registered command schema at release time. Generated artifacts cannot drift because they are produced from the same source of truth as the binary.

**Requirements that address this:**
- REQ-O-045 (P1) - Integration Artifact Version Declaration [Tier: O]

---

### §3 - Stderr vs Stdout Discipline  [High · 1/3]

**Gap:** Data is normally stdout, but help/prose success/error output can also appear on stdout.

**Solutions:**
**Strict stream discipline:**
```
stdout: ONLY the command's primary output (data, result, id)
stderr: progress indicators, warnings, debug info, timing, counts
```

```bash
# Good
$ tool create-user --name Alice 2>/dev/null
{"id": 42, "name": "Alice"}

$ tool create-user --name Alice 1>/dev/null
Creating user Alice...
Done. (45ms)
```

**Structured warnings in JSON output:**
```json
{
  "ok": true,
  "data": {"records": [...]},
  "warnings": [
    {"code": "DEPRECATED_KEY", "message": "...", "location": "line 12"}
  ]
}
```

**For framework design:**
- Route all `log()`, `progress()`, `debug()` calls to stderr by default
- Only `print()` / `output()` writes to stdout
- Provide `--quiet` to suppress all stderr
- Provide `--warnings-as-errors` to exit non-zero on any warning

---

> **Merged from §39:** The following content was originally a separate challenge.
> It is consolidated here because it describes a specific case of the same root problem.

**Requirements that address this:**
- REQ-F-006 (P0) - Stdout/Stderr Stream Enforcement [Tier: F]
- REQ-F-048 (P0) - Help Output Routing to Stderr in Non-TTY Mode [Tier: F]
- REQ-O-025 (P3) - --warnings-as-errors Flag [Tier: O]

---

### §5 - Pagination & Large Output  [High · 1/3]

**Gap:** List commands expose limit/cursor flags, but no standard pagination metadata envelope.

**Solutions:**
**Always indicate truncation and total:**
```json
{
  "ok": true,
  "data": [...],
  "pagination": {
    "total": 50000,
    "returned": 100,
    "truncated": true,
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```

**Cursor-based pagination (stateless):**
```bash
tool list-users --limit 100 --cursor "eyJpZCI6MTAwfQ=="
```

**Streaming output (JSONL):**
```bash
tool list-logs --output jsonl --stream
# Emits one JSON object per line
# Agent can process incrementally
{"timestamp": "...", "level": "error", "message": "..."}
{"timestamp": "...", "level": "info",  "message": "..."}
```

**Default sensible limits:**
```bash
tool list-users           # default: --limit 20
tool list-users --limit 0 # explicit: no limit
```

**For framework design:**
- All list commands have `--limit` (default: 20) and `--cursor`
- Response always includes `pagination` metadata
- `--stream` flag for JSONL output when processing large sets

**Requirements that address this:**
- REQ-F-018 (P0) - Pagination Metadata on List Commands [Tier: F]
- REQ-F-019 (P0) - Default Output Limit [Tier: F]
- REQ-O-003 (P0) - --limit and --cursor Pagination Flags [Tier: O]
- REQ-O-004 (P2) - --output jsonl / --stream Flag [Tier: O]

---

### §14 - Argument Validation Before Side Effects  [High · 1/3]

**Gap:** Commander validates some arguments before execution, but exit code is generic and errors are not structured JSON.

**Solutions:**
**Two-phase execution: validate-then-execute:**
```python
def run(args):
    # Phase 1: validate ALL args before touching anything
    errors = validate(args)
    if errors:
        emit_validation_errors(errors)
        sys.exit(2)  # exit 2 = bad args, no side effects occurred

    # Phase 2: execute (side effects start here)
    execute(args)
```

**Validation result in structured output:**
```json
{
  "ok": false,
  "phase": "validation",          // side effects: none
  "errors": [
    {
      "param": "--key-file",
      "code": "FILE_NOT_FOUND",
      "message": "Key file '/missing.pem' does not exist",
      "value": "/missing.pem"
    },
    {
      "param": "--workers",
      "code": "TYPE_ERROR",
      "message": "Expected integer, got 'abc'",
      "value": "abc"
    }
  ]
}
```

**Preflight flag:**
```bash
tool deploy --env prod --version 1.2.3 --validate-only
# Runs all validation, reports errors, exits without deploying
# exit 0 = would succeed
# exit 2 = validation errors (listed in JSON)
```

**For framework design:**
- Framework enforces: all `@validate` hooks run before any `@execute` hooks
- Exit code `2` reserved exclusively for validation failures (no side effects)
- `--validate-only` is a framework-level flag available on all commands
- Validation errors always list all problems at once (not just the first one)

**Requirements that address this:**
- REQ-F-002 (P0) - Exit Code 2 Reserved for Validation Failures [Tier: F]
- REQ-F-015 (P0) - Validate-Before-Execute Phase Order [Tier: F]
- REQ-C-006 (P0) - All Args Validated in Phase 1 [Tier: C]
- REQ-O-009 (P1) - --validate-only Flag [Tier: O]

---

### §28 - Config File Shadowing & Precedence  [High · 1/3]

**Gap:** README documents precedence and `configure --list` shows config, but sources are not machine-readable.

**Solutions:**
**`--show-config` flag that reveals effective configuration:**
```bash
$ tool --show-config --output json
{
  "effective_config": {
    "env": "production",
    "registry": "internal.registry.example.com",
    "timeout": 30
  },
  "sources": {
    "env":      {"source": "~/.config/tool/config.toml", "value": "production"},
    "registry": {"source": "./.toolrc",                  "value": "internal..."},
    "timeout":  {"source": "default",                    "value": 30}
  }
}
```

**Include active config in every response `meta`:**
```json
{
  "meta": {
    "effective_config_hash": "sha256:abc123",
    "config_sources": ["~/.config/tool/config.toml", "./.toolrc"]
  }
}
```

**`--no-config` flag for isolated runs:**
```bash
tool deploy --no-config --env staging
# Ignores all config files and env vars
# Uses only explicit flags + compiled defaults
# Reproducible behavior regardless of environment
```

**Explicit config path:**
```bash
tool --config /dev/null deploy --env staging
# Guaranteed: no config file loaded
```

**For framework design:**
- Documented, stable precedence order (flags > env vars > local file > global file > defaults)
- `tool --show-config` is a built-in framework command
- `--no-config` disables all file-based config loading
- `meta.config_sources` included in every response

**Requirements that address this:**
- REQ-F-028 (P1) - Config Source Tracking in Response Meta [Tier: F]
- REQ-O-015 (P1) - --show-config Flag [Tier: O]
- REQ-O-016 (P1) - --no-config Flag [Tier: O]

---

### §46 - API Schema to CLI Flag Translation Loss  [High · 1/3]

**Gap:** `-d` accepts JSON/bracket notation, but there is no full `--json` body flag or API-schema validation.

**Solutions:**
**Level 1 — Raw JSON payload input:**
```bash
# Accept raw JSON payload for complex commands (jpoehnelt Axis 2 level 2)
my-tool user create --json '{"name": "Alice", "roles": ["admin", "viewer"], "metadata": {...}}'
```

**Level 2 — Stdin JSON for structured input:**
```bash
echo '{"name": "Alice", "roles": ["admin", "viewer"]}' | my-tool user create --from-stdin
```

**Level 3 — Zero translation loss (jpoehnelt Axis 2 level 3):**
```bash
# CLI accepts the exact API request body; maps directly to API call with no reinterpretation
my-tool api POST /users --body '{"user": {"name": "Alice", "roles": [...]}}'
# Agent uses the OpenAPI spec as CLI documentation directly
```

**For framework design:**
- For every mutating command, accept `--json <payload>` as an alternative to individual flags, where the payload maps directly to the underlying API request body.
- Expose a `--raw-api` mode (jpoehnelt Axis 2 level 3) that accepts the API request body directly and performs no flag-to-body translation.
- Validate that the `--json` payload passes the same JSON Schema as the API request body (i.e., the CLI's JSON Schema and the API's JSON Schema are identical for mutating operations).
- `--schema` output should include both the CLI flag schema and, where applicable, the underlying API JSON Schema with a reference to where translation occurs.
- Generate CLI wrappers from OpenAPI specs (rather than hand-writing them) to guarantee zero initial translation loss.

**Requirements that address this:**
- REQ-O-032 (P1) - --raw-payload Flag for Mutating Commands [Tier: O]

---

### §51 - Shell Word Splitting and Glob Expansion Interference  [High · 1/3]

**Gap:** Exec-array invocation preserves spaced file paths, but missing files become unstructured `ENOENT` stack traces.

**Solutions:**
**Tools must validate received arguments against declared constraints:**
```bash
# If --file expects a single file path, tool validates it exists before acting
$ my-tool process report
Error: file 'report' not found. Did you mean 'report 2024.txt'?
# This surfaces the word-split mistake
```

**Schema declares which args expect file paths or glob patterns:**
```json
{
  "name": "files",
  "type": "glob_pattern",
  "glob_expanded_by": "caller",
  "or": "filepath"
}
```

**Framework-provided invocation helpers use exec-array:**
```python
# Framework's subprocess API (exec-array, no shell):
result = framework.run(["my-tool", "process", filename])
# filename is passed as a single argument regardless of spaces or special chars
```

**For framework design:**
- The framework's subprocess API MUST use exec-array (not shell string) — this fully prevents the problem for tool-to-tool invocations.
- Document prominently in the agent guide: "never construct shell strings; always use exec-array invocation."
- Tools that accept file paths MUST validate existence and emit a distinct `FILE_NOT_FOUND` error to surface word-split mistakes.

**Requirements that address this:**
- REQ-F-062 (P0) - Glob Expansion and Word-Splitting Prevention [Tier: F]

---

### §59 - High-Entropy String Token Poisoning  [High · 1/3]

**Gap:** `configure --list` masks stored `api_key`, but there is no semantic token summary/unmask protocol.

**Solutions:**
**Auto-mask high-entropy fields in structured output:**
```json
{
  "token": "[JWT: expires 2024-03-11T15:00:00Z, sub=user_123]",
  "token_raw": "<available via: tool auth token --show --unmask>"
}
```

**Schema marks fields as `high_entropy: true`:**
```json
{ "name": "token", "type": "string", "high_entropy": true, "mask_in_output": true }
```

**Framework detects high-entropy strings automatically:**
- Strings matching `^[A-Za-z0-9+/]{40,}={0,2}$` (base64) or JWT pattern (`xxx.yyy.zzz`) are masked unless `--unmask` is passed.
- Instead of the raw value, output: entropy type, meaningful metadata extracted from the payload (expiry, subject), and the flag to retrieve the raw value.

**For framework design:**
- Framework MUST provide a `high_entropy` field type with automatic masking in non-`--unmask` mode.
- The mask replacement MUST include the semantic metadata from the string (JWT: expiry + claims summary; UUID: just the ID truncated; API key: first 8 chars + `...`).
- `--unmask` flag explicitly opts into showing raw high-entropy values.

**Requirements that address this:**
- REQ-F-058 (P1) - High-Entropy Field Masking [Tier: F]
- REQ-O-037 (P2) - --unmask Flag for High-Entropy Fields [Tier: O]

---

### §69 - Argument Order Ambiguity  [High · 1/3]

**Gap:** Subcommand-level global flags work after the subcommand; root-level placement is rejected.

**Solutions:**
**Enforce interspersed option parsing at the framework level:**

Options are accepted in any position relative to subcommands and positional arguments. `tool cmd --flag arg`, `tool --flag cmd arg`, and `tool cmd arg --flag` are all equivalent.

```python
# argparse
parser = argparse.ArgumentParser()
parser.parse_intermixed_args()  # allows interspersed options

# Click
@click.command(context_settings={"allow_interspersed_args": True})

# Commander.js
program.enablePositionalOptions(false)  # disable strict positional ordering
```

**For global flags that must precede subcommands, declare this constraint in the manifest:**

```json
{
  "option_placement": "strict",
  "note": "Global options must appear before the subcommand"
}
```

**Framework design:**
- Default parser configuration MUST use interspersed/permissive option parsing
- If a command passes remaining args verbatim to a subprocess (e.g., a wrapper), it MUST declare `option_placement: "strict"` in its manifest so agents know to front-load flags
- The manifest's `--schema` output MUST include the effective `option_placement` value

**Requirements that address this:**
- REQ-F-067 (P1) - Interspersed Option Parsing [Tier: F]
- REQ-C-027 (P1) - Commands Declare Option Placement Convention [Tier: C]

---

### §73 - Documentation Accuracy Drift  [High · 1/3]

**Gap:** No AGENTS.md; available CLAUDE/skill docs are useful but version drift exists.

**Solutions:**
**For CLI authors:**

Include a version field in AGENTS.md that agents can compare against `<binary> --version`:

```markdown
<!-- cli-version: 3.1.2 -->
<!-- last-validated: 2026-04-01 -->
# AGENTS.md — My CLI
```

Add AGENTS.md validation to CI — run a script that checks each documented flag and command against `--help` output:

```bash
# ci/validate-agents-md.sh
BINARY_VERSION=$(my-cli --version)
DOC_VERSION=$(grep 'cli-version:' AGENTS.md | sed 's/.*cli-version: //')
if [ "$BINARY_VERSION" != "$DOC_VERSION" ]; then
  echo "AGENTS.md version $DOC_VERSION does not match binary $BINARY_VERSION"
  exit 1
fi
# Spot-check documented flags
for flag in $(grep -oP '\-\-[\w-]+' AGENTS.md); do
  if ! my-cli --help | grep -q "$flag"; then
    echo "Flag $flag in AGENTS.md not found in --help"
    exit 1
  fi
done
```

Update AGENTS.md in the same PR as any flag, command, or env var change — enforce this via PR template or CI gate.

**For framework designers:**

Generate AGENTS.md automatically from registered command schemas. If AGENTS.md cannot drift from the schema, it cannot drift from the binary.

Provide a `--validate-agents-md` command or make `generate-skills` verify existing AGENTS.md against live schema on each run.

**Requirements that address this:**
- REQ-O-043 (P1) - AGENTS.md Required Content [Tier: O]
- REQ-O-046 (P2) - AGENTS.md CI Validation [Tier: O]

---

### §9 - Binary & Encoding Safety  [High · 2/3]

**Gap:** File uploads use Buffer/base64 for binary content; error handling remains unstructured.

**Solutions:**
**Detect and handle encoding explicitly:**
```python
def safe_read(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # Return base64 for binary, with metadata
        return None  # signal: use binary path

def safe_field(value: bytes | str) -> dict:
    if isinstance(value, bytes):
        try:
            text = value.decode("utf-8")
            return {"type": "text", "value": text}
        except UnicodeDecodeError:
            import base64
            return {"type": "binary", "encoding": "base64",
                    "value": base64.b64encode(value).decode()}
    return {"type": "text", "value": value}
```

**Binary fields use base64 in JSON output:**
```json
{
  "ok": true,
  "data": {
    "name": "photo.png",
    "content": {
      "type": "binary",
      "encoding": "base64",
      "value": "iVBORw0KGgo...",
      "size_bytes": 45231
    }
  }
}
```

**Null byte sanitization:**
```python
def sanitize_string(s: str) -> str:
    return s.replace("\x00", "\ufffd")  # replacement character
```

**Declare content type in output:**
```json
{
  "data": {
    "content": "...",
    "content_encoding": "utf-8",    // or "base64", "latin-1"
    "content_type": "text/plain"    // or "application/octet-stream"
  }
}
```

**For framework design:**
- All string fields pass through a UTF-8 sanitizer before JSON serialization
- Binary fields automatically base64-encoded with `{type, encoding, value}` wrapper
- Framework catches UnicodeDecodeError and emits structured error, never crashes raw
- `--binary-mode base64|hex|skip` flag for commands that may return binary

**Requirements that address this:**
- REQ-F-016 (P1) - UTF-8 Sanitization Before Serialization [Tier: F]
- REQ-F-017 (P1) - Binary Field Base64 Encoding [Tier: F]

---

### §41 - Update Notifier Side-Channel Output Pollution  [High · 2/3]

**Gap:** No update notifier found; CI/NO_UPDATE_NOTIFIER produced no side-channel notice.

**Solutions:**
**For agents:**
```python
env = {**os.environ, "NO_UPDATE_NOTIFIER": "1",  # npm ecosystem standard
       "CI": "true",  # suppresses update notifiers in many tools
       "DISABLE_UPDATE_NOTIFIER": "true"}  # some tools check this
result = subprocess.run(cmd, env=env, capture_output=True)
```

**For CLI authors:**
```javascript
// Check TTY and CI before enabling update notifier
const updateNotifier = require('update-notifier');
if (process.stdout.isTTY && !process.env.CI) {
    updateNotifier({pkg: require('./package.json')}).notify();
}
// Better: surface in meta.update_available field of JSON response
```

**For framework design:**
- Suppress all update notifications when `isatty(stdout) == False` or `CI == "true"`.
- If an update is available, place `"update_available": {"version": "2.0.0", "command": "npm install -g my-tool"}` in the `meta` section of the structured JSON response — never as prose on stdout or stderr.
- Never emit ANSI box-drawing characters in update notifications.
- Rate-limit update checks to once per week per installation, not once per invocation.

**Requirements that address this:**
- REQ-F-050 (P1) - Update Notifier Side-Channel Suppression [Tier: F]
- REQ-F-077 (P2) - Telemetry Non-Blocking [Tier: F]

---

### §6 - Command Composition & Piping  [Medium · 0/3]

**Gap:** No `--output id` mode and no stdin `-` ID protocol.

**Solutions:**
**`--output id` mode (extract single value):**
```bash
$ tool get-user --name Alice --output id
42
# Just the primary identifier, no JSON, pipeable
```

**Stdin acceptance for IDs:**
```bash
$ tool get-user --name Alice --output id | tool send-welcome-email --user-id -
# --user-id - means "read from stdin"
```

**Batch input from file/stdin:**
```bash
$ tool list-users --output jsonl | tool send-welcome-email --users-jsonl -
```

**`--from` flag for reading prior command output:**
```bash
$ tool get-user --name Alice --output json > /tmp/user.json
$ tool send-welcome-email --from-file /tmp/user.json
```

**For framework design:**
- Every command that takes an ID also accepts `-` to read from stdin
- Provide `--output id` as a standard extraction mode
- Define a pipe protocol: each framework command can declare what it emits and what it accepts

**Requirements that address this:**
- REQ-O-005 (P3) - --output id Extraction Mode [Tier: O]
- REQ-O-006 (P3) - Stdin as ID Source (-) [Tier: O]

---

### §7 - Output Non-Determinism  [Medium · 0/3]

**Gap:** Raw API output has no stable-output mode or volatile-field isolation.

**Solutions:**
**Sort all collections in output:**
```json
// Always sort arrays of objects by a stable key
{"users": [{"id": 1}, {"id": 2}, {"id": 3}]}

// Always sort string arrays lexicographically
{"permissions": ["admin", "delete", "read", "write"]}
```

**Separate volatile metadata from stable data:**
```json
{
  "ok": true,
  "data": {                          // stable — safe to cache/compare
    "status": "ok",
    "version": "1.2.3"
  },
  "meta": {                          // volatile — do not compare
    "checked_at": "2024-03-11T14:30:01Z",
    "duration_ms": 45,
    "request_id": "req-abc"
  }
}
```

**Deterministic dry-run IDs:**
```bash
# Dry-run preview ID derived from inputs, not random
preview_id = sha256(command + args + timestamp_truncated_to_minute)
# Same args within the same minute → same preview ID
```

**`--stable-output` flag:**
```bash
tool list-users --stable-output
# Sorts all collections, omits volatile fields (timestamps, durations)
# Output is deterministic for identical inputs
```

**For framework design:**
- All array fields sorted by default in `--output json` mode
- `data` and `meta` are top-level siblings; agents compare `data` only
- Dry-run IDs are content-addressed, not random
- Document which fields are volatile in the output schema (`"volatile": true`)

**Requirements that address this:**
- REQ-F-020 (P2) - Stable Array Sorting in JSON Output [Tier: F]
- REQ-F-021 (P1) - Data/Meta Separation in Response Envelope [Tier: F]
- REQ-O-007 (P3) - --stable-output Flag [Tier: O]

---

### §20 - Environment & Dependency Discovery  [Medium · 0/3]

**Gap:** No `doctor --output json` or structured dependency preflight.

**Solutions:**
**Preflight check command:**
```bash
$ tool doctor --output json
{
  "ok": false,
  "checks": [
    {"name": "docker",   "ok": true,  "version": "24.0.5", "required": ">=20.0"},
    {"name": "kubectl",  "ok": false, "found": "1.18.0", "required": ">=1.24",
     "fix": "brew upgrade kubectl"},
    {"name": "db_conn",  "ok": true},
    {"name": "redis",    "ok": false, "error": "connection refused at localhost:6379",
     "fix": "docker run -d redis"}
  ]
}
```

**Dependency declaration in help:**
```bash
$ tool build --show-requirements --output json
{
  "required": [
    {"name": "docker", "version": ">=20.0", "install": "https://docs.docker.com/..."},
    {"name": "DOCKER_BUILDX_BUILDER", "type": "env_var", "optional": true}
  ]
}
```

**For framework design:**
- Framework provides a `preflight()` hook for each command
- `tool doctor` runs all preflight checks without executing any commands
- Each failed check includes a `fix` field with the exact command to run

**Requirements that address this:**
- REQ-O-026 (P1) - tool doctor Built-In Command [Tier: O]

---

### §21 - Schema & Help Discoverability  [Medium · 0/3]

**Gap:** No `--schema --output json`; help is prose only.

**Solutions:**
**Machine-readable command manifest:**
```bash
$ tool --schema --output json
{
  "commands": [
    {
      "name": "deploy",
      "description": "Deploy the application to an environment",
      "danger_level": "mutating",
      "parameters": [
        {"name": "env", "type": "string", "required": true,
         "enum": ["staging", "prod"], "description": "Target environment"},
        {"name": "version", "type": "string", "required": false,
         "description": "Version tag to deploy (default: latest)"},
        {"name": "dry-run", "type": "boolean", "default": false}
      ],
      "output_schema": {
        "type": "object",
        "properties": {
          "ok": {"type": "boolean"},
          "effect": {"type": "string", "enum": ["deployed", "noop"]},
          "data": {
            "deployment_id": {"type": "string"},
            "version": {"type": "string"}
          }
        }
      },
      "exit_codes": {
        "0": "success",
        "1": "deployment failed",
        "4": "environment not found",
        "7": "deployment timed out"
      }
    }
  ]
}
```

**For framework design:**
- Every command auto-generates its schema from its parameter declarations
- `tool --schema` outputs the full manifest
- Output schema is declared alongside input schema, not separate
- Schema versioning: `tool --schema-version` to track evolution

**Requirements that address this:**
- REQ-C-015 (P1) - Commands Declare Input and Output Schema [Tier: C]
- REQ-O-013 (P1) - --schema / --output-schema Flag [Tier: O]

---

### §29 - Working Directory Sensitivity  [Medium · 0/3]

**Gap:** File paths are resolved relative to CWD with no `meta.cwd` or framework `--cwd`.

**Solutions:**
**Always output absolute paths:**
```json
{
  "files": [
    "/project/src/index.ts",
    "/project/src/utils.ts"
  ]
}
```

**Include CWD used in `meta`:**
```json
{
  "meta": {
    "cwd": "/project",
    "project_root": "/project"
  }
}
```

**Explicit `--cwd` / `--root` flag:**
```bash
tool build --cwd /project
tool validate --root /project
# CWD-independent: agent always passes explicit path
```

**Never mutate CWD of the calling process:**
```python
# Bad: os.chdir(target_dir)
# Good: use absolute paths internally; never change process CWD
import os
old_cwd = os.getcwd()
# operate with absolute paths throughout
```

**For framework design:**
- All path outputs are absolute by default
- `meta.cwd` included in every response
- `--cwd` flag available on all commands as a framework standard
- Framework never calls `os.chdir()` / `process.chdir()`

**Requirements that address this:**
- REQ-F-027 (P2) - CWD in Response Meta [Tier: F]
- REQ-F-040 (P2) - Absolute Path Output Enforcement [Tier: F]
- REQ-F-041 (P2) - Process CWD Immutability [Tier: F]
- REQ-O-017 (P2) - --cwd / --root Flag [Tier: O]

---

### §30 - Undeclared Filesystem Side Effects  [Medium · 0/3]

**Gap:** Config filesystem side effects are not declared or inventoried.

**Solutions:**
**Declare all side effect locations in schema:**
```json
{
  "command": "fetch-schema",
  "filesystem_side_effects": [
    {
      "path": "~/.cache/tool/schemas/",
      "type": "cache",
      "ttl_seconds": 3600,
      "clearable_with": "tool cache clear --scope schemas"
    }
  ]
}
```

**`--no-cache` and `--cache-ttl` flags:**
```bash
tool fetch-schema --url ... --no-cache
tool fetch-schema --url ... --cache-ttl 0
```

**Temp files registered for cleanup:**
```json
{
  "ok": true,
  "data": {"path": "/tmp/tool-export-abc123.xlsx"},
  "cleanup": {
    "command": "tool cleanup --file /tmp/tool-export-abc123.xlsx",
    "auto_cleanup_after_seconds": 3600
  }
}
```

**`tool status --show-side-effects` inventory:**
```bash
$ tool status --show-side-effects --output json
{
  "cache": {"path": "~/.cache/tool/", "size_bytes": 45000000},
  "logs":  {"path": "~/.local/share/tool/logs/", "size_bytes": 524000000},
  "temp":  {"path": "/tmp/tool-*/", "count": 14, "size_bytes": 2000000}
}
```

**For framework design:**
- Every command declares `filesystem_side_effects` in its schema
- Framework provides `tool cleanup` that removes all known side effect paths
- Temp files use a session-scoped directory, auto-cleaned when session ends
- Log rotation built into framework (max size, max age)

**Requirements that address this:**
- REQ-F-042 (P3) - Log Rotation in Framework Logger [Tier: F]
- REQ-F-043 (P2) - Temp File Session-Scoped Auto-Cleanup [Tier: F]
- REQ-C-011 (P3) - Commands Declare Filesystem Side Effects [Tier: C]
- REQ-O-018 (P3) - --no-cache and --cache-ttl Flags [Tier: O]
- REQ-O-027 (P2) - tool cleanup Built-In Command [Tier: O]
- REQ-O-028 (P2) - tool status Built-In Command [Tier: O]

---

### §33 - Observability & Audit Trail  [Medium · 0/3]

**Gap:** No `request_id`, `duration_ms`, trace propagation, or audit log.

**Solutions:**
**Request/trace ID in every response:**
```json
{
  "ok": true,
  "meta": {
    "request_id": "req-abc123",
    "trace_id": "trace-xyz789",
    "duration_ms": 4521,
    "timestamp": "2024-03-11T14:30:00Z",
    "command": "deploy",
    "version": "1.2.3"
  }
}
```

**Correlation ID propagation:**
```bash
TOOL_TRACE_ID=agent-session-42-step-7 tool deploy
# All log entries for this call include the trace ID
```

**Structured audit log:**
```bash
$ tool audit-log --since 1h --output jsonl
{"timestamp": "...", "command": "deploy", "params": {...},
 "exit_code": 0, "duration_ms": 4521, "operator": "agent-session-42"}
```

**For framework design:**
- Every response includes `meta.request_id` (server-assigned) and `meta.trace_id` (caller-supplied)
- `TOOL_TRACE_ID` env var propagated automatically
- Framework writes append-only audit log to `~/.local/share/tool/audit.jsonl`

**Requirements that address this:**
- REQ-F-024 (P2) - Request ID and Trace ID in Every Response [Tier: F]
- REQ-F-025 (P2) - TOOL_TRACE_ID Environment Variable Propagation [Tier: F]
- REQ-F-026 (P2) - Append-Only Audit Log [Tier: F]
- REQ-F-039 (P1) - Duration Tracking in Response Meta [Tier: F]
- REQ-O-030 (P2) - tool audit-log Built-In Command [Tier: O]

---

### §52 - Recursive Command Tree Discovery Cost  [Medium · 0/3]

**Gap:** No `--schema` command tree; agents must recurse through help text.

**Solutions:**
**Single-call full tree export:**
```bash
$ tool --schema --full
```
```json
{
  "tool": "my-tool",
  "version": "1.2.3",
  "schema_version": "1.0",
  "commands": [
    {
      "name": "create",
      "description": "Create a new resource",
      "args": [],
      "flags": [],
      "subcommands": []
    },
    {
      "name": "config",
      "subcommands": [
        { "name": "get", "args": [] },
        { "name": "set", "args": [] }
      ]
    }
  ]
}
```

**For framework design:**
- `tool --schema` (REQ-O-013) MUST return the full command tree by default, not just the top-level command.
- Each command node in the tree includes: name, description, args with types and constraints, flags, required/optional status, subcommands.
- The full schema export must be a single synchronous call completing in under 500ms regardless of command count.

**Requirements that address this:**
- REQ-O-041 (P1) - tool manifest Built-In Command [Tier: O]

---

### §57 - Locale-Dependent Error Messages  [Medium · 0/3]

**Gap:** OS/file errors surface as raw stack traces, not normalized structured errors.

**Solutions:**
**Separate machine-readable code from locale message:**
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Permission denied: '/etc/hosts'",
    "locale_message": "Permission refusée: '/etc/hosts'",
    "locale": "fr_FR"
  }
}
```

**Framework normalizes OS errors to English (`LC_MESSAGES=C`) before serialization.**

**For framework design:**
- The framework's exception handler MUST normalize all OS/runtime error messages to English before placing them in `error.message`.
- `error.code` is the ONLY field agents should use for error classification; `error.message` is human-readable context only.

**Requirements that address this:**
- REQ-F-066 (P1) - Subprocess Locale Normalization [Tier: F]

---

### §63 - Terminal Column Width Output Corruption  [Medium · 0/3]

**Gap:** No JSON mode; help prose wraps at terminal width.

**Solutions:**
**Disable hard-wrapping in non-TTY mode:**
```python
# Python: don't wrap when stdout is not a TTY
import shutil, sys
columns = shutil.get_terminal_size().columns if sys.stdout.isatty() else 0
# columns=0 means "no wrap"
```

**`--width=0` flag disables all hard-wrapping:**
```bash
$ tool describe resource --width=0 --output json
# All strings output as single lines regardless of length
```

**JSON output mode MUST never hard-wrap string values:**
- In JSON output mode, the framework serializes all strings without newline injection.
- Table/human output mode may wrap; JSON output mode MUST NOT.

**For framework design:**
- Framework MUST disable all terminal-width-based formatting when JSON output mode is active.
- Framework MUST NOT inject newlines into string field values during serialization regardless of `$COLUMNS` value.
- The `--width` flag (default: `0` in non-TTY, terminal width in TTY) MUST be respected by all formatting functions.

**Requirements that address this:**
- REQ-F-056 (P0) - Terminal Width Wrapping Disabled in JSON Mode [Tier: F]

---

### §4 - Verbosity & Token Cost  [Medium · 1/3]

**Gap:** No progress spam observed, but there is no quiet/fields control and CI does not activate structured mode.

**Solutions:**
**Tiered verbosity:**
```bash
tool deploy --quiet          # only emit final JSON result, no prose
tool deploy                  # default: minimal human output + JSON
tool deploy --verbose        # progress to stderr, JSON to stdout
tool deploy --debug          # full debug trace to stderr
```

**`CI` environment auto-detection:**
```bash
# When CI=true, behave as --quiet automatically
if [ "$CI" = "true" ]; then
  VERBOSITY=quiet
fi
```

**Minimal JSON output by default:**
```json
// Bad default: everything
{"id": 42, "name": "Alice", "email": "alice@example.com", "created_at": "...",
 "updated_at": "...", "role": "user", "preferences": {...}, "metadata": {...}}

// Good default: just what was asked for
{"id": 42, "name": "Alice"}

// With --full flag: everything
```

**`--fields` selector:**
```bash
tool list-users --fields id,name --output json
# Returns only requested fields
```

**For framework design:**
- Default verbosity is `--quiet` when stdout is not a TTY
- JSON output never includes prose, only structured data
- Provide `--fields` filtering at framework level
- Track and log token-approximate output sizes for monitoring

**Requirements that address this:**
- REQ-F-038 (P2) - Verbosity Auto-Quiet in Non-TTY Context [Tier: F]
- REQ-O-002 (P2) - --fields Selector [Tier: O]
- REQ-O-008 (P1) - --quiet / --verbose / --debug Verbosity Flags [Tier: O]

---

### §27 - Platform & Shell Portability  [Medium · 1/3]

**Gap:** Node CLI is portable in principle, but there is no doctor command and failures are raw.

**Solutions:**
**Portable shebang and runtime detection:**
```bash
#!/usr/bin/env -S python3 -u
# -S: allows arguments after env command (GNU env >=8.30 / macOS 12+)
```

**Explicit shell and version requirements:**
```json
{
  "requires": {
    "shell": "bash>=4.0",
    "platform": ["linux", "darwin"],
    "tools": ["curl>=7.0", "jq>=1.6"]
  }
}
```

**For framework design:**
- `tool doctor` checks platform compatibility
- Framework abstracts platform differences (dates, paths, colors)
- All paths use forward slashes, never backslash (for cross-platform scripts)

**Requirements that address this:**
- REQ-C-018 (P3) - Commands Declare Platform Requirements [Tier: C]

---

### §44 - Agent Knowledge Packaging Absence  [Medium · 1/3]

**Gap:** Repository ships CLAUDE.md and a skill, but no AGENTS.md/CONTEXT.md and no `--schema` danger/requires fields.

**Solutions:**
**Minimum viable AGENTS.md:**
```markdown
# AGENTS.md

## Quick Reference
- Deploy: `my-tool deploy --env <staging|production> --dry-run` (always dry-run first)
- Auth: `my-tool auth login` must be run before any other command; tokens expire in 8 hours
- Status check: `my-tool status --json` returns current system health

## Known Gotchas
- If you see "invalid token", run `my-tool auth refresh` (tokens expire every 8 hours)
- `deploy` to production requires `--confirm` flag; staging does not
- The `--region` flag defaults to us-east-1 in CI, eu-west-1 locally

## Safe Operations
Read-only: `list`, `get`, `status`, `logs`
Mutating: `deploy`, `delete`, `update` (run with --dry-run first)
Irreversible: `delete --permanent` (no dry-run available)
```

**OpenClaw skill file with machine-readable metadata:**
```yaml
---
name: my-tool
version: "1.0.0"
triggers:
  - "deploy to production"
  - "my-tool"
tools: [bash]
---
[Skill body with agent-specific guidance]
```

**For framework design:**
- Auto-generate a minimal AGENTS.md template from schema metadata at `my-tool --generate-agents-md`.
- Include in `--schema` output: `"danger_level"`, `"requires"` (prerequisite commands), `"read_only"`, and `"docs_url"` fields.
- Provide a CLI hook to load and display skill files: `my-tool --skill` returns the tool's OpenClaw skill.
- Score frameworks against Axis 7 and require at least level 1 (CONTEXT.md or AGENTS.md present) before an "agent-ready" designation.

**Requirements that address this:**
- REQ-O-034 (P2) - tool generate-skills Built-In Command [Tier: O]
- REQ-O-043 (P1) - AGENTS.md Required Content [Tier: O]
- REQ-O-046 (P2) - AGENTS.md CI Validation [Tier: O]

---

## Already Passing

§37, §50, §61, §62, §64, §66, §17, §8, §32  _(score 3/3 - no action needed)_

## Could Not Verify

None.
