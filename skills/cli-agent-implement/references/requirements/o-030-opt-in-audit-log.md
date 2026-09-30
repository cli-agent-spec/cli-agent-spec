# REQ-O-030: Opt-In Audit Log and audit-log Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST provide a persistent audit log that is **off by default**. It is enabled either by the application (`app.enable_audit_log()`) or by the operator through the prefixed environment variable `<PREFIX>AUDIT_LOG` (REQ-F-073): `1` enables it at the default path, an absolute path enables it at that path, and `0` disables it even when the application enabled it. The operator setting takes precedence, so an agent runtime can turn the log on for a CLI whose author never did, and off for one that did. When the log is disabled, the framework MUST NOT create any file or directory for it.

When enabled, the framework MUST append one JSONL entry per command invocation, whether the command succeeded or failed. Each entry MUST include: `timestamp`, `command`, `args` (the parsed argument map after REQ-F-034 redaction, never the raw argv), `exit_code`, `duration_ms`, `trace_id`, and `request_id`; `operator` is included when a session identifier is available. Invocations that do no work are not logged: `--help`, `--version`, shell completion, schema or manifest introspection, and `audit-log` itself.

The log MUST be bounded by the framework, not by the operator: it rotates when the active file exceeds a maximum size (default: 10 MB), keeps a maximum number of rotated files (default: 5), and prunes rotated files older than a maximum age (default: 30 days). Entries are append-only within a file; rotation and pruning are the only operations that remove data. Each entry MUST be written as a single `O_APPEND` write of one complete line so that concurrent invocations never interleave, and rotation MUST be safe under concurrent invocations.

The default path is `$XDG_STATE_HOME/<toolname>/audit.jsonl` (falling back to `~/.local/state/<toolname>/audit.jsonl`), or the platform's per-user log directory outside XDG systems. The framework MUST list the audit log path in the manifest's filesystem side effects as type `log` (REQ-C-011) whenever it is enabled.

A failed audit write (read-only filesystem, full disk, permission error) MUST NOT change the command's exit code or output data; the framework adds an `AUDIT_LOG_UNAVAILABLE` entry to `warnings[]` instead.

The framework MUST provide a built-in `tool audit-log` command that queries the log across the active and rotated files. The command MUST accept `--since <duration or ISO datetime>`, `--command <name>`, `--trace-id <id>`, `--format jsonl`, and `--limit <n>`.

## Acceptance Criteria

- With the log not enabled by the application or the operator, running any command creates no audit file or directory
- `<PREFIX>AUDIT_LOG=1 tool deploy` appends one entry to the default path; `<PREFIX>AUDIT_LOG=0` suppresses the log for an application that enabled it
- An entry is appended for a command that exits non-zero
- `tool --help`, `tool --version`, and shell completion append no entry
- The entry for a command invoked with a secret argument does not contain the secret value
- The audit log is valid JSONL after concurrent invocations from parallel sessions
- Total audit log disk usage stays bounded by the configured size and retention across unlimited invocations
- With the log path unwritable, the command exits with its normal exit code and `warnings[]` contains `AUDIT_LOG_UNAVAILABLE`
- `tool audit-log --since 1h --format jsonl` returns all invocations from the past hour, one per line
- `tool audit-log --trace-id abc123` returns only entries with that trace ID
- `--limit 100` returns at most 100 entries

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.audit_log_path` is present on every response while the log is enabled. The `audit-log` command returns `data.entries`, an array of audit log entry objects with `timestamp`, `command`, `args`, `exit_code`, `duration_ms`, `trace_id`, and `request_id`.

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
{"timestamp":"2026-03-17T14:00:01Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,"duration_ms":1247,"trace_id":"abc123","request_id":"req-001"}
{"timestamp":"2026-03-17T14:05:22Z","command":"delete","args":{"resource_id":"r-42"},"exit_code":5,"duration_ms":8,"trace_id":"def456","request_id":"req-002"}
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
→ ~/.local/state/tool/audit.jsonl appended:
  {"timestamp":"2026-03-17T14:00:01Z","command":"deploy","args":{"env":"prod","token":"[REDACTED]"},"exit_code":0,...}

$ tool deploy --env prod
→ no audit file written (not enabled)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `request_id` and `trace_id` values written to each audit log entry |
| [REQ-F-025](f-025-tool-trace-id-environment-variable-propagation.md) | F | Provides: the caller-supplied trace ID recorded in each entry |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Provides: `duration_ms` value written to each audit log entry |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret fields are redacted in every audit log entry and query result |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | F | Composes: the audit log uses the same rotation mechanism with its own bounds |
| [REQ-F-073](f-073-env-var-namespace-prefix.md) | F | Consumes: `<PREFIX>AUDIT_LOG` follows the tool env var prefix |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Extends: the enabled audit log appears in the declared filesystem side effects |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Extends: `meta.audit_log_path` is added to the standard response meta |
