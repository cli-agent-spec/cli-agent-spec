# REQ-C-033: Commands Declare Interruption

**Tier:** Command Contract | **Priority:** P1

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

A command whose run length the author cannot bound in advance (it grows with input size, remote load, or data shape) SHOULD declare `interruption` at registration, saying how its work survives the caller's sync call budget ([REQ-F-080](f-080-sync-call-budget.md)). The declaration has two independent properties:

- `detach`: the work can continue in a background job after the call returns ([REQ-F-081](f-081-detached-job-runtime.md)). It suits work that cannot be cut but can run unattended: a long HTTP call, a deploy, a build
- `resume`: the command saves checkpoints, so the identical invocation continues the work after an interruption instead of starting over ([REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md)). It suits work made of chunks or steps, and it is the only protection when background processes do not survive (a CI container, a sandbox that kills orphans)

At least one of the two MUST be `true`. Work that is neither, such as a migration inside one transaction or an opaque third-party binary, declares no `interruption` and keeps the wall-clock limit of [REQ-F-011](f-011-default-timeout-per-command.md) with an honest `TIMEOUT (10)` entry.

A command that declares `interruption` MUST:

- declare an `INCOMPLETE (14)` entry in `exit_codes`: `retryable: true, side_effects: "none"` for read-only work, `retryable: false, side_effects: "partial"` for work that writes
- report progress ([REQ-C-034](c-034-long-running-commands-report-progress.md))

It MAY set `idle_timeout_ms`, how long its job may go without progress, and `max_lifetime_ms`, the bound on the whole work when the caller passes no `--timeout`.

The framework MUST refuse to register:

- `interruption` together with `async: true` ([REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md)), which already returns at once; with `streaming_default: true` or `supports_streaming: true` ([REQ-O-004](o-004-output-jsonl-stream-flag.md)), whose output is a sequence of events with no single result to hand back later; or with `stdout: "protocol"` ([REQ-C-032](c-032-protocol-server-commands-declare-stdout-protocol.md))
- `resume: true` on a `mutating` or `destructive` command without `--idempotency-key` ([REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md)): a continuation of writing work must be recognisably the same run

Detaching by default is left out on purpose. It costs a worker process on every call, and a command reading stdin needs its input spooled first; one line of declaration opts in where it pays.

## Acceptance Criteria

- `tool manifest` shows `interruption` on every command that declares it, and an `INCOMPLETE (14)` entry in its `exit_codes`
- Registering `interruption: {detach: false, resume: false}` raises a framework error
- Registering `interruption` without an `INCOMPLETE (14)` entry raises a framework error
- Registering `interruption` with `async: true`, a streaming declaration, or `stdout: "protocol"` raises a framework error
- Registering `resume: true` on a `mutating` command that does not accept `--idempotency-key` raises a framework error
- A command without `interruption` behaves exactly as before: no `--budget` flag, no handoff, `TIMEOUT (10)` at its wall-clock limit

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`exit-code-entry.md`](../schemas/exit-code-entry.md)

`CommandEntry.interruption` is `{detach, resume, idle_timeout_ms?, max_lifetime_ms?}`; the schema requires an `exit_codes` entry for `"14"` alongside it and excludes `async: true`, `streaming_default: true`, and `stdout`.

---

## Wire Format

```bash
$ tool manifest
```

```json
{
  "schema_version": "3.20",
  "framework_version": "2.4.0",
  "etag": "sha256:91d4c7",
  "commands": {
    "analyze": {
      "description": "Compute statistics over a data file",
      "danger_level": "safe",
      "required_scopes": [],
      "interruption": { "detach": true, "resume": true },
      "flags": {},
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "The statistics are computed", "retryable": false, "side_effects": "complete" },
        "14": { "name": "INCOMPLETE", "description": "The work continues; run data.continue_command", "retryable": true, "side_effects": "none" }
      }
    },
    "import": {
      "description": "Import rows from a CSV file",
      "danger_level": "mutating",
      "required_scopes": ["rows:write"],
      "interruption": { "detach": false, "resume": true, "max_lifetime_ms": 7200000 },
      "flags": {
        "idempotency-key": { "type": "string", "required": false, "description": "Key that makes a repeat of this import the same run" }
      },
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "Every row is imported", "retryable": false, "side_effects": "complete" },
        "14": { "name": "INCOMPLETE", "description": "Some rows are imported; run data.continue_command", "retryable": false, "side_effects": "partial" }
      }
    }
  }
}
```

---

## Example

| Command | `detach` | `resume` |
|---------|----------|----------|
| Analysis of a large file | `true` | `true` |
| One long HTTP call, a deploy | `true` | `false` |
| Chunked import where background processes do not survive | `false` | `true` |
| Migration inside one transaction | `false` | `false`: declares no `interruption` and keeps `TIMEOUT (10)` |

```
register command "analyze":
  danger_level: safe
  interruption: { detach: true, resume: true }
  exit_codes:
    SUCCESS   (0):  retryable: false, side_effects: complete
    INCOMPLETE(14): retryable: true,  side_effects: none
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-080](f-080-sync-call-budget.md) | F | Provides: the declaration that subjects the command to the sync call budget |
| [REQ-F-081](f-081-detached-job-runtime.md) | F | Provides: `detach`, which hands the work to a background job |
| [REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md) | C | Composes: `resume` promises the checkpoints that requirement defines |
| [REQ-C-034](c-034-long-running-commands-report-progress.md) | C | Composes: every interruptible command reports progress |
| [REQ-F-082](f-082-incomplete-work-response.md) | F | Provides: the `INCOMPLETE` entry whose `retryable` the response copies |
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Specializes: an undeclared command keeps the plain wall-clock limit |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Consumes: the key a resumable writer needs |
| [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md) | C | Composes: an async command already returns at once and declares no `interruption` |
