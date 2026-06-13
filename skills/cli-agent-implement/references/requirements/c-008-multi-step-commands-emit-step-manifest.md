# REQ-C-008: Multi-Step Commands Emit Step Manifest

**Tier:** Command Contract | **Priority:** P1

**Source:** [§13 Partial Failure & Atomicity](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Any command whose execution consists of multiple discrete, ordered steps MUST declare a step manifest in its registration metadata. The manifest MUST list step names in execution order. When running with `--output json` or in streaming mode, the command MUST emit a step-start and step-complete event for each step as it executes (via the framework's step tracking API). The final response MUST include `completed_steps`, `failed_step` (if any), and `skipped_steps`.

## Acceptance Criteria

- A multi-step command's schema output includes `steps: [...]` listing all step names.
- A partial failure response includes `completed_steps` as an array of completed step names.
- A partial failure response includes `failed_step` as the name of the failed step.
- The SIGTERM/timeout response includes the same step tracking fields.

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

The step manifest is declared at registration and appears in `--schema` output. The step tracking fields appear in the final response.

```json
{
  "steps": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Ordered list of step names the command will execute; declared at registration time"
  },
  "completed_steps": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Step names that completed successfully before failure or termination"
  },
  "failed_step": {
    "type": ["string", "null"],
    "description": "Name of the step that caused failure; null if the command completed fully"
  },
  "skipped_steps": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Step names not reached due to earlier failure"
  }
}
```

---

## Wire Format

Schema output:

```bash
$ tool migrate-database --schema
```

```json
{
  "command": "migrate-database",
  "steps": ["backup", "apply_schema", "migrate_data", "verify"]
}
```

Partial failure response:

```bash
$ tool migrate-database
```

```json
{
  "ok": false,
  "data": {
    "partial": true,
    "completed_steps": ["backup", "apply_schema"],
    "failed_step": "migrate_data",
    "skipped_steps": ["verify"],
    "resume_from": "migrate_data"
  },
  "error": { "code": "DISK_FULL", "message": "Disk full during data migration" },
  "warnings": [],
  "meta": { "duration_ms": 4210 }
}
```

---

## Example

A multi-step command declares its steps at registration and uses the framework's step tracking API during execution.

```
register command "migrate-database":
  danger_level: mutating
  steps: ["backup", "apply_schema", "migrate_data", "verify"]
  exit_codes:
    SUCCESS        (0): description: "Migration completed",           retryable: false, side_effects: complete
    PARTIAL_FAILURE(3): description: "Migration failed mid-execution", retryable: false, side_effects: partial
    TIMEOUT       (10): description: "Migration timed out",           retryable: false, side_effects: partial

  execute(args, step_tracker):
    step_tracker.start("backup")
    backup_database()
    step_tracker.complete("backup")

    step_tracker.start("apply_schema")
    apply_schema_changes()
    step_tracker.complete("apply_schema")

    step_tracker.start("migrate_data")
    migrate_data()           # may raise → framework sets failed_step and skipped_steps
    step_tracker.complete("migrate_data")
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) | C | Composes: `completed_steps`/`failed_step`/`skipped_steps` are the runtime counterpart to the static `steps` declaration |
| [REQ-O-010](o-010-resume-from-flag-for-multi-step-commands.md) | O | Extends: `--resume-from` uses the step names declared here to skip already-completed steps |
| [REQ-O-011](o-011-rollback-on-failure-flag.md) | O | Extends: `--rollback-on-failure` uses `completed_steps` to determine what to undo |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `PARTIAL_FAILURE (3)` must be declared in the command's `exit_codes` map |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: step tracking fields are carried inside `ResponseEnvelope.data` |
