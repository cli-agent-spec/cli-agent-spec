# Schema: AuditLogEntry

**File:** [`audit-log-entry.json`](audit-log-entry.json)

> **Used by:** [REQ-O-030](../requirements/o-030-opt-in-audit-log.md)

---

## Purpose

One line of the opt-in audit log, and one item of `data.entries` returned by `tool audit-log`. It records a single command invocation so that an incident review can reconstruct what an agent ran, with which arguments, and how it ended, long after the response itself is gone (§33).

Three design decisions shape the type:

- **Same values as the response.** `timestamp`, `command`, `exit_code`, `duration_ms`, `request_id`, and `trace_id` repeat the invocation's `meta` fields, so an entry joins to a captured response or trace by `request_id` or `trace_id`
- **Warnings as codes.** `warnings` keeps only the codes of the response's `warnings[]`. Facts that must be queryable later, such as an over-privileged credential or disabled injection protection, survive without copying message text
- **Bounded by construction.** An entry never exceeds 16 KiB; oversized `args` values are replaced with `[TRUNCATED]` and `truncated` is set, so one entry is always one write

---

## AuditLogEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string ISO 8601 date-time | yes | Invocation start time, matching `meta.timestamp` |
| `command` | string | yes | Space-separated command path, matching `meta.command` (`config set`) |
| `args` | object | yes | Parsed argument map after REQ-F-034 redaction; never the raw argv |
| `exit_code` | integer `0–255` | yes | Process exit code, matching `meta.exit_code` |
| `duration_ms` | integer | yes | Wall-clock milliseconds, matching `meta.duration_ms` |
| `request_id` | string | yes | Unique invocation identifier, matching `meta.request_id` |
| `trace_id` | string | when `TOOL_TRACE_ID` is set | Trace ID propagated from `TOOL_TRACE_ID` (REQ-F-025) |
| `session_id` | string | when `<PREFIX>SESSION_ID` is set | Agent session identifier, recorded verbatim |
| `warnings` | string[] | yes | Codes from the response's `warnings[]`, in emission order; may be empty |
| `truncated` | boolean | no | `true` when `args` values were replaced to fit 16 KiB |

---

## Examples

**Successful deploy with a redacted secret**
```json
{"timestamp": "2026-03-17T14:00:01Z", "command": "deploy", "args": {"env": "prod", "token": "[REDACTED]"}, "exit_code": 0, "duration_ms": 1247, "request_id": "req-001", "trace_id": "abc123", "warnings": []}
```

**Dry run under an over-privileged credential, inside an agent session**
```json
{"timestamp": "2026-03-17T14:05:22Z", "command": "delete", "args": {"resource_id": "r-42", "dry_run": true}, "exit_code": 0, "duration_ms": 8, "request_id": "req-002", "session_id": "s-1", "warnings": ["CREDENTIAL_OVER_PRIVILEGED"]}
```

**Large payload truncated to fit the entry cap**
```json
{"timestamp": "2026-03-17T14:07:00Z", "command": "import", "args": {"source": "s3://bucket/data.json", "raw_payload": "[TRUNCATED]"}, "exit_code": 0, "duration_ms": 5310, "request_id": "req-003", "warnings": [], "truncated": true}
```

**Invalid: raw argv instead of the parsed map**
```json
{"timestamp": "2026-03-17T14:00:01Z", "command": "deploy", "args": ["--env", "prod", "--token", "abc123"], "exit_code": 0, "duration_ms": 1247, "request_id": "req-001", "warnings": []}
```
Violation: `args` must be an object. Raw argv cannot be redacted reliably and leaks the token.

---

## Common mistakes

- **Logging raw argv.** Redaction (REQ-F-034) works on named arguments; a positional token or `--token=abc` inside a string list slips through
- **Writing `trace_id: null` when `TOOL_TRACE_ID` is unset.** Omit the field, as `meta.trace_id` does
- **Copying full warning objects.** `warnings` holds codes only; message text is for humans and bloats every line
- **Truncating the serialized line.** Cutting the JSON text produces an invalid line; replace values in `args` and set `truncated`
- **Using a dot path in `command`.** The entry uses the space-separated form of `meta.command`; the dot form belongs to `DispatchRequest._cmd`

---

## Agent interpretation

- Join an entry to a response or trace by `request_id` or `trace_id`, never by `timestamp`
- `exit_code` non-zero with `args.dry_run` or `args.validate_only` set means nothing was changed; the entry still shows what was attempted
- `truncated: true` means some `args` values are `[TRUNCATED]`; do not replay the invocation from the entry
- A `[REDACTED]` value is a declared secret; never try to recover it from other sources
- `warnings` containing `INJECTION_PROTECTION_DISABLED` marks an invocation whose external data was returned untagged; treat its outputs as untrusted during review
- An empty result from `tool audit-log` means no matching invocation was recorded while the log was enabled; a disabled log fails with `AUDIT_LOG_DISABLED` instead

---

## Coding agent notes

**Type representation**
- Generate `args` as a string-keyed map of JSON values, not as a typed struct; its keys are the command's argument names
- Generate `warnings` as a list of strings and `trace_id`, `session_id`, and `truncated` as optional fields that are omitted, not `null`

**Construction**
- Build the entry from the same values the envelope factory writes to `meta`, after the exit code is known and before the response is emitted
- Serialize once, check the byte length, and replace the largest `args` values with `[TRUNCATED]` until the line fits 16 KiB

**Tests to generate**
- Every written line validates against `audit-log-entry.json`
- A secret argument appears as `[REDACTED]`
- A 50 MB argument yields one entry of at most 16 KiB with `truncated: true`

---

## Implementation notes

- `additionalProperties: false` keeps the entry shape predictable for `tool audit-log` filters and external log shippers; command-specific facts belong in `args`
- The 16 KiB cap keeps each entry a single `O_APPEND` write well under common pipe and filesystem atomicity limits
- The log file is created with mode `0600`; entries still carry unredacted hostnames, ids, and paths
- The entry is not wrapped in a `ResponseEnvelope`; `tool audit-log --format json` returns entries inside `data.entries` of a normal envelope

---

## Related

| Document | Relationship |
|----------|-------------|
| [REQ-O-030](../requirements/o-030-opt-in-audit-log.md) | Consumes: defines the audit log and the `audit-log` command that emit this type |
| [schemas/response-envelope.md](response-envelope.md) | Provides: the `meta` values each entry repeats and the envelope around `data.entries` |
| [§33 Observability & Audit Trail](../challenges/07-medium-observability/33-medium-observability.md) | Sources: the failure mode this schema addresses |
