# REQ-C-022: Async Commands Declare Job Descriptor Schema

**Tier:** Command Contract | **Priority:** P0

**Source:** [§49 Async Job / Polling Protocol Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

Any command that initiates an asynchronous operation (one that does not complete before the process exits) MUST declare `async: true` in its registration metadata and MUST return a typed job descriptor in `data`. The job descriptor MUST include: `job_id`, `status` (`running`|`complete`|`failed`|`cancelled`), `terminal` (boolean), `status_command` (exact invocation to check status), `cancel_command` (exact invocation to cancel), `poll_interval_ms`, and `timeout_ms`. The framework auto-generates `job status <id>` and `job cancel <id>` subcommands for all registered async commands.

## Acceptance Criteria

- An async command's `--schema` output includes `async: true` and the job descriptor schema
- The job descriptor returned at invocation time includes all required fields
- `tool job status <id>` exits 0 for complete, 3 for still-running, 4 for failed, 5 for not-found
- Attempting to register an async command without a job descriptor schema raises a framework error

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Async commands extend `CommandEntry` with:

| Field | Type | Description |
|-------|------|-------------|
| `async` | boolean (`true`) | Marks the command as asynchronous |
| `job_descriptor_schema` | JSON Schema object | Schema for the job descriptor object returned in `ResponseEnvelope.data` |

The `data` field of the initial response conforms to:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_id` | string | yes | Stable identifier for this job instance |
| `status` | `"running"` \| `"complete"` \| `"failed"` \| `"cancelled"` | yes | Current job state |
| `terminal` | boolean | yes | `true` when `status` is `complete`, `failed`, or `cancelled` |
| `status_command` | string | yes | Exact invocation to check current status |
| `cancel_command` | string | yes | Exact invocation to cancel this job |
| `poll_interval_ms` | integer | yes | Recommended interval between status polls |
| `timeout_ms` | integer | yes | Time after which the job is considered failed |

---

## Wire Format

```bash
$ tool build --schema
```
```json
{
  "async": true,
  "parameters": {
    "target": { "type": "string", "required": true, "description": "Build target name" }
  },
  "job_descriptor_schema": {
    "type": "object",
    "required": ["job_id", "status", "terminal", "status_command", "cancel_command", "poll_interval_ms", "timeout_ms"],
    "properties": {
      "job_id":          { "type": "string" },
      "status":          { "type": "string", "enum": ["running", "complete", "failed", "cancelled"] },
      "terminal":        { "type": "boolean" },
      "status_command":  { "type": "string" },
      "cancel_command":  { "type": "string" },
      "poll_interval_ms":{ "type": "integer" },
      "timeout_ms":      { "type": "integer" }
    }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Job accepted and started", "retryable": false, "side_effects": "partial" }
  }
}
```

Initial response when the command is invoked:

```json
{
  "ok": true,
  "data": {
    "job_id": "build-7f3a",
    "status": "running",
    "terminal": false,
    "status_command": "tool job status build-7f3a",
    "cancel_command": "tool job cancel build-7f3a",
    "poll_interval_ms": 5000,
    "timeout_ms": 600000
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 22 }
}
```

---

## Example

```
register command "build":
  async: true
  job_descriptor_schema:
    type: object
    required: [job_id, status, terminal, status_command, cancel_command, poll_interval_ms, timeout_ms]
    properties:
      job_id:           { type: string }
      status:           { type: string, enum: [running, complete, failed, cancelled] }
      terminal:         { type: boolean }
      status_command:   { type: string }
      cancel_command:   { type: string }
      poll_interval_ms: { type: integer }
      timeout_ms:       { type: integer }
  parameters:
    target: type=string, required=true, description="Build target name"

# framework auto-generates: tool job status <id>  and  tool job cancel <id>
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-049](f-049-async-command-handler-enforcement.md) | F | Enforces: async handler contract that commands with `async: true` must implement |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `async` flag and `job_descriptor_schema` are part of the `--schema` output |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: exit codes for `job status` subcommand are declared alongside the async command |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: job descriptor is returned as `ResponseEnvelope.data` |
