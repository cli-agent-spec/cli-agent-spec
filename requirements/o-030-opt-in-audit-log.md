# REQ-O-030: Opt-In Audit Log and audit-log Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST provide a persistent audit log that is **off by default**.

**Enabling.** The application enables it with `app.enable_audit_log()`, optionally passing a path. The operator controls it through the prefixed environment variable `<PREFIX>AUDIT_LOG` (REQ-F-073), which accepts exactly three kinds of value:

| Value | Effect |
|-------|--------|
| `1` | On, at the application's configured path, or at the default path when the application set none |
| `0` | Off, even when the application enabled it |
| An absolute path | On, at that path; overrides both the application's path and the default |

Any other value (`true`, `off`, an empty string, a relative path) fails every invocation except `--help` and `--version` with exit `2` (`ARG_ERROR`) and error code `INVALID_AUDIT_LOG_SETTING`, naming the variable and the accepted values. The operator setting takes precedence over the application, so an agent runtime can turn the log on for a CLI whose author never did, and off for one that did. When the log is disabled, the framework MUST NOT create any file or directory for it. Whether or not the log is enabled, the manifest MUST declare `<PREFIX>AUDIT_LOG` and the session variable, each in its one home under REQ-F-073: root `env_vars` with a `description` (ManifestResponse 3.5), or the `env_vars` of the flag it already backs, as when the framework reuses a variable behind a flag as the session variable.

**What is logged.** When enabled, the framework MUST append one entry per invocation that resolves to a command, whatever its outcome. This includes argument errors raised after the command resolves, `--validate-only` (REQ-O-009), `--dry-run` (REQ-C-004, REQ-O-048), and a destructive command refused for lacking `--confirm-destructive` (REQ-O-021): an incident review needs exactly these. An invocation that never resolves to a command (an unknown command or group) is not logged, because its arguments cannot be redacted without a declared schema and raw argv is never written. Invocations that do no work are not logged: `--help`, `--version`, shell completion, schema or manifest introspection, and `audit-log` itself.

**Entry.** Each entry is one line of JSON matching [`audit-log-entry.json`](../schemas/audit-log-entry.json):

- `timestamp`, `command`, `exit_code`, `duration_ms`, and `request_id` are always present. `command` MUST equal the invocation's `meta.command` exactly, in whichever spelling the framework uses consistently for it: space-separated (`config set`) or dot-separated (`config.set`)
- `args` is the parsed argument map after REQ-F-034 redaction, never the raw argv. Framework flags that change what the invocation did (`--dry-run`, `--validate-only`, `--confirm-destructive`, `--no-injection-protection`) appear in it under their flag names
- `warnings` lists the `code` of every entry in the response's `warnings[]`, so an over-privileged credential (`CREDENTIAL_OVER_PRIVILEGED`, REQ-O-047) or disabled injection protection (`INJECTION_PROTECTION_DISABLED`, REQ-O-023) is recorded as a queryable code
- `trace_id` is present when `TOOL_TRACE_ID` is set (REQ-F-025)
- `session_id` is present when the agent runtime sets the framework's session variable. A framework that already reads an agent session id from a prefixed environment variable (for example to scope REQ-C-007 idempotency keys) uses that variable; otherwise the session variable is `<PREFIX>SESSION_ID`. The framework reads exactly one variable, records its value verbatim, derives `session_id` from nothing else, and documents the variable's name

Each entry MUST NOT exceed 16 KiB. When a serialized entry would, the framework replaces values in `args`, largest first, with the string `[TRUNCATED]` until it fits, and sets `truncated: true` on the entry. A command taking a large payload therefore still produces one bounded entry that fits a single write.

**Bounds.** The log MUST be bounded by the framework, not by the operator. It rotates when the active file exceeds a maximum size, keeps a maximum number of rotated files, and removes data older than a maximum age; the application MUST be able to configure all three. The defaults SHOULD be 10 MB, 5 rotated files, and 30 days. A framework MAY ship smaller defaults, but its default size bound, `max_size × (max_rotated_files + 1)`, SHOULD NOT exceed 60 MB, so a log the operator turns on for a CLI whose author configured nothing has a predictable footprint. The defaults of REQ-F-042 do not apply to the audit log. The maximum age applies to entries, not only to rotated files: before appending, the framework rotates the active file when its first entry is older than the maximum age, then deletes rotated files whose last modification is older than the maximum age. Total disk usage therefore never exceeds `max_size × (max_rotated_files + 1)` plus one entry. Entries are append-only within a file; rotation and pruning are the only operations that remove data. Each entry MUST be written as a single `O_APPEND` write of one complete line so that concurrent invocations never interleave, and rotation MUST be safe under concurrent invocations. Rotation and pruning run only while the log is enabled; `tool cleanup` (REQ-O-027) never removes the audit log, so the files of a log that is later disabled remain until the operator deletes them.

**Permissions.** The log holds every command's arguments, and redaction covers declared secrets only: hostnames, account ids, paths, and query text stay in clear. The framework MUST create the log file with mode `0600` and any directory it creates for it with mode `0700` (an owner-only ACL on Windows), regardless of the process umask. It MUST NOT change the mode of an existing file or directory.

**Location.** The default path is `$XDG_STATE_HOME/<toolname>/audit.jsonl` (falling back to `~/.local/state/<toolname>/audit.jsonl`), or the platform's per-user log directory outside XDG systems. While the log is enabled, the framework MUST list its path in the manifest's filesystem side effects as type `log` (REQ-C-011), without `clearable_with`, and MUST set `meta.audit_log_path` on every response; while it is disabled, neither appears.

**Write failures.** The framework writes the entry after the command's exit code is known and before it emits the response. A failed audit write (read-only filesystem, full disk, permission error) MUST NOT change the command's exit code or output data; the framework adds an `AUDIT_LOG_UNAVAILABLE` warning to `warnings[]` instead. When the output carries no envelope (`--format plain`, `tsv`, or a `jsonl` stream), the framework writes that warning to stderr as one JSON `WarningDetail` line.

**Querying.** The framework MUST register a built-in `tool audit-log` command on every CLI, since the operator can enable the log for any of them. It reads across the active and rotated files and accepts:

- `--since <duration or ISO datetime>`: a duration is a positive integer followed by `s`, `m`, `h`, or `d` (`30s`, `15m`, `1h`, `7d`); a datetime is ISO 8601 with a UTC offset. Any other value exits `2`
- `--command <path>`: matches a command path exactly or as a whole-word prefix, and MUST accept both spellings, space-separated (`config set`) and dot-separated (`config.set`), whichever one the entries use. The prefix rule holds in each spelling: `config` matches `config set` and `config.set` but never `configure`
- `--trace-id <id>`: matches `trace_id` exactly
- `--limit <n>`: keeps the newest `n` matching entries
- `--cursor <token>`: continues from the `meta.pagination.next_cursor` of a previous `audit-log` answer made with the same filters, returning the next-older batch of up to `n` matching entries. The token is opaque and stateless (REQ-O-003); a malformed or expired token, or one reused with different filters, fails as `INVALID_CURSOR` (REQ-O-003)
- `--format jsonl`: one entry per line, followed by the pagination summary line

Filters combine with AND. Entries are always returned oldest first.

`audit-log` is a list command and MUST accept `--cursor` as well as `--limit`, so it satisfies REQ-F-018 in full. Its default answer is one buffered envelope with the entries in `data.entries` and `meta.pagination`:

- `returned` is the number of entries in the response, and `total` is the number of entries that matched the filters, or `null` when the framework does not count them
- When `--limit` left out older matching entries, `truncated` and `has_more` are `true` and `next_cursor` is a non-null opaque token. Passing it as `--cursor` with the same filters returns the next-older batch of up to `n` matching entries, still oldest first within the page
- When no older entry matches, `truncated` and `has_more` are `false` and `next_cursor` is `null`

**Cursor anchor.** The `audit-log` cursor anchors on the position of the last entry the page returned, its `timestamp` plus `request_id`, never on a file offset or a rotated-file index, so rotation between pages does not move it. The next page returns the matching entries still older than the anchor, without an error or a warning, even when entries were removed in between: pruning removes the oldest entries, so the walk ends sooner, `total` may shrink from one page to the next, and `has_more` and `next_cursor` stay accurate for what remains. Entries appended after the first page are newer than the anchor and never appear on a later page; a caller that wants them starts a new query without `--cursor`.

A framework MAY make `audit-log` streaming-default under REQ-O-004, declaring `streaming_default: true` in the manifest; `--no-stream` then MUST return the buffered `data.entries` envelope. In streaming mode (`--format jsonl` or the streaming default) the same pagination fields go on the final summary line, as REQ-O-004 requires.

With the log disabled, `audit-log` exits `4` (`PRECONDITION`) with error code `AUDIT_LOG_DISABLED` and a `fix_required` naming `<PREFIX>AUDIT_LOG`, so an agent can tell "nothing was recorded" from "nothing happened".

## Acceptance Criteria

- With the log not enabled by the application or the operator, running any command creates no audit file or directory, `meta.audit_log_path` is absent, and the manifest lists no `log` side effect for it
- `<PREFIX>AUDIT_LOG=1 tool deploy` appends one entry to the default path; `<PREFIX>AUDIT_LOG=0` suppresses the log for an application that enabled it
- With the application's path set, `<PREFIX>AUDIT_LOG=1` writes to the application's path and `<PREFIX>AUDIT_LOG=/tmp/a/audit.jsonl` writes to `/tmp/a/audit.jsonl`
- `<PREFIX>AUDIT_LOG=true tool deploy` and `<PREFIX>AUDIT_LOG=logs/audit.jsonl tool deploy` exit `2` with error code `INVALID_AUDIT_LOG_SETTING` and write nothing
- With the log enabled, every response carries `meta.audit_log_path` and the manifest lists that path as a `log` filesystem side effect
- An entry is appended for a command that exits non-zero, for `--validate-only`, for `--dry-run`, and for a destructive command refused without `--confirm-destructive`
- An unknown command appends no entry
- `tool --help`, `tool --version`, shell completion, `tool manifest`, `--schema`, and `tool audit-log` append no entry
- The entry for a command invoked with a secret argument does not contain the secret value
- An invocation that emits `CREDENTIAL_OVER_PRIVILEGED` has that code in the entry's `warnings`
- With the framework's session variable set to `s-1`, the entry has `session_id: "s-1"`; without it, the entry has no `session_id`
- A framework that has no other session variable uses `<PREFIX>SESSION_ID`, and its documentation names the session variable it reads
- `tool manifest` lists `<PREFIX>AUDIT_LOG` in root `env_vars` with a `description`, and the session variable there too unless it backs a flag, whether or not the log is enabled
- Every entry validates against `audit-log-entry.json`
- An invocation with a 50 MB argument appends one entry of at most 16 KiB with `truncated: true`
- With a umask of `0022`, a freshly created audit log file has mode `0600` and a directory created for it has mode `0700`
- The audit log is valid JSONL after concurrent invocations from parallel sessions
- The application can set the maximum size, rotated file count, and maximum age, and the log honors each value
- Total audit log disk usage stays bounded by the configured size and retention across unlimited invocations
- An active file whose first entry is older than the maximum age is rotated on the next write, and rotated files older than the maximum age are deleted
- With the log path unwritable, the command exits with its normal exit code and `warnings[]` contains `AUDIT_LOG_UNAVAILABLE`; with `--format plain`, the warning appears on stderr
- `tool audit-log --since 1h --format jsonl` returns all invocations from the past hour, one per line, oldest first
- `tool audit-log --since 2026-03-17T14:00:00Z` returns only entries at or after that time; `--since 1w` exits `2`
- Every entry's `command` equals the `meta.command` of the invocation it records
- `tool audit-log --command config` returns entries for `config set` and `config get` but not `configure`
- For a framework whose `meta.command` is dot-separated, entries record `config.set`; `tool audit-log --command config` and `--command "config set"` both return it, and neither returns `configure`
- `tool audit-log --trace-id abc123` returns only entries with that trace ID
- With more than 100 matching entries, `--limit 100` returns the newest 100, oldest first
- `tool audit-log` without `--format jsonl` returns one envelope with the entries in `data.entries` and `meta.pagination`
- With 250 matching entries, `--limit 100` returns the newest 100 with `returned: 100`, `truncated: true`, `has_more: true`, and a non-null `next_cursor`; `total` is `250` or `null`
- Passing that `next_cursor` as `--cursor` with the same filters and `--limit 100` returns the 100 entries before those, oldest first; passing the second page's `next_cursor` returns the oldest 50 with `returned: 50`, `truncated: false`, `has_more: false`, and `next_cursor: null`
- A malformed `--cursor` value exits `2` (`ARG_ERROR`) with error code `INVALID_CURSOR` (REQ-O-003)
- A `next_cursor` from `tool audit-log --command config --limit 100` passed to `tool audit-log --command deploy --cursor <token>` exits `2` with error code `INVALID_CURSOR`
- With 250 matching entries, when pruning removes the oldest 120 between the first and second page, passing the first page's `next_cursor` returns the remaining 30 older matches with `returned: 30`, `has_more: false`, and `next_cursor: null`, and no error or warning
- An entry appended between the first and second page does not appear on the second page
- With `--format jsonl`, the final line is a summary line carrying the same pagination fields
- When `audit-log` declares `streaming_default: true` in the manifest, `tool audit-log --no-stream` returns the buffered `data.entries` envelope
- With the log disabled, `tool audit-log` exits `4` with error code `AUDIT_LOG_DISABLED`

---

## Schema

**Types:** [`audit-log-entry.json`](../schemas/audit-log-entry.json) · [`response-envelope.json`](../schemas/response-envelope.json) · [`manifest-response.json`](../schemas/manifest-response.json)

Each log line and each item of the `audit-log` command's `data.entries` is an `AuditLogEntry`. `meta.audit_log_path` is present on every response while the log is enabled. The enabled log appears in the manifest as a `FilesystemSideEffect` of type `log`. `<PREFIX>AUDIT_LOG` and the session variable are `EnvVarEntry` items in the manifest's root `env_vars`, unless the session variable already backs a flag.

---

## Wire Format

`meta.audit_log_path` in the response envelope when the log is enabled:

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 412,
    "request_id": "req_01HZ",
    "audit_log_path": "/home/user/.local/state/mytool/audit.jsonl"
  }
}
```

Querying the log:

```bash
$ tool audit-log --since 1h --format jsonl
```

```
{"timestamp":"2026-03-17T14:00:01Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,"duration_ms":1247,"request_id":"req-001","trace_id":"abc123","warnings":[]}
{"timestamp":"2026-03-17T14:05:22Z","command":"delete","args":{"resource_id":"r-42","dry_run":true},"exit_code":0,"duration_ms":8,"request_id":"req-002","trace_id":"def456","session_id":"s-1","warnings":["CREDENTIAL_OVER_PRIVILEGED"]}
{"_summary":true,"total":2,"returned":2,"truncated":false,"has_more":false,"next_cursor":null,"duration_ms":14}
```

Querying a disabled log:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "AUDIT_LOG_DISABLED",
    "message": "The audit log is not enabled for this tool",
    "retryable": false,
    "fix_required": "Set TOOL_AUDIT_LOG=1 for future invocations; invocations made while the log was disabled were not recorded"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 3 }
}
```

---

## Example

Enabled by the application, with the default bounds made explicit:

```
app = Framework("tool")
app.enable_audit_log(max_size_mb=10, max_rotated_files=5, max_age_days=30)
```

Enabled by the operator for a CLI that never opted in:

```
$ TOOL_AUDIT_LOG=1 tool deploy --env prod --token abc123
→ ~/.local/state/tool/audit.jsonl (mode 0600) appended:
  {"timestamp":"2026-03-17T14:00:01Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,...}

$ tool deploy --env prod
→ no audit file written (not enabled)

$ TOOL_AUDIT_LOG=yes tool deploy --env prod
→ exit 2, INVALID_AUDIT_LOG_SETTING: accepted values are 1, 0, or an absolute path
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `request_id` and `command` values written to each audit log entry |
| [REQ-F-025](f-025-tool-trace-id-environment-variable-propagation.md) | F | Provides: the caller-supplied trace ID recorded in each entry |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Provides: `duration_ms` value written to each audit log entry |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret fields are redacted in every audit log entry and query result |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | F | Composes: the audit log uses the same rotation mechanism with its own bounds |
| [REQ-F-073](f-073-env-var-namespace-prefix.md) | F | Consumes: `<PREFIX>AUDIT_LOG` and the session variable (`<PREFIX>SESSION_ID` unless the framework already reads a prefixed one) follow the tool env var prefix and are declared in root `env_vars`, or on the flag the session variable already backs |
| [REQ-F-018](f-018-pagination-metadata-on-list-commands.md) | F | Provides: `meta.pagination` on every `audit-log` answer |
| [REQ-O-003](o-003-limit-and-cursor-pagination-flags.md) | O | Consumes: `--limit` and the stateless `--cursor` token that pages through `audit-log` |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Extends: `audit-log` MAY be streaming-default, with `--no-stream` returning the buffered envelope |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Extends: the enabled audit log appears in the declared filesystem side effects |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Extends: `meta.audit_log_path` is added to the standard response meta |
| [REQ-O-009](o-009-validate-only-flag.md) | O | Consumes: `--validate-only` invocations are logged |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Consumes: destructive confirmation and refusal are recorded through `args` |
| [REQ-O-023](o-023-no-injection-protection-flag.md) | O | Consumes: `INJECTION_PROTECTION_DISABLED` is recorded in the entry's `warnings` |
| [REQ-O-027](o-027-tool-cleanup-built-in-command.md) | O | Composes: `tool cleanup` leaves the audit log in place |
| [REQ-O-047](o-047-tool-check-permissions-built-in-command.md) | O | Consumes: `CREDENTIAL_OVER_PRIVILEGED` is recorded in the entry's `warnings` |
