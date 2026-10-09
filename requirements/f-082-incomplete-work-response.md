# REQ-F-082: Incomplete-Work Response

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

When a call returns before its work ends and the work is not lost, the framework MUST exit `INCOMPLETE (14)` with a structured response that says how far the work got and how to continue it. Two states share one shape: `running`, when the work goes on in a background job ([REQ-F-081](f-081-detached-job-runtime.md)), and `paused`, when it stopped at a checkpoint ([REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md)) and waits for the next call.

`INCOMPLETE` is neither success nor failure. It is not `0`, because [REQ-F-001](f-001-standard-exit-code-table.md) reserves `0` for an operation completed as intended, and `tool analyze && tool report` must not run `report` without a result. It is not `TIMEOUT (10)`, because that code means the work stopped and its progress since the last checkpoint is gone.

The response MUST carry:

- `ok: false` and `error.code: "INCOMPLETE"`
- `error.retryable` and the exit's `side_effects` from the command's declared `INCOMPLETE` `ExitCodeEntry` ([REQ-C-033](c-033-commands-declare-interruption.md)): `retryable: true` with `side_effects: "none"` for read-only work, `retryable: false` with `side_effects: "partial"` for work that writes
- `data.state`: `"running"` or `"paused"`
- `data.job_id`: the job or checkpoint identifier
- `data.progress`: `{done, total?, unit?}` from the command's last progress report ([REQ-C-034](c-034-long-running-commands-report-progress.md))
- `data.continue_command`: an exact invocation that continues the work, run verbatim. For `running` it is `tool job wait <id>`. For `paused` it is the original invocation, with `--idempotency-key <key>` appended when the command writes ([REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md)), so that a continuation is never a second, independent run
- `data.cancel_command`: an exact invocation that stops the work and discards its checkpoint
- `meta.budget_ms` ([REQ-F-080](f-080-sync-call-budget.md))

`tool job wait` and `tool job status` return this response, with exit `14`, for any job that has not ended, including jobs of [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md) async commands.

The agent's loop is part of the contract: run `continue_command` until the exit is not `14`; compare `progress.done` between continuations, and when it has not grown over three of them, run `cancel_command` and escalate. An agent never needs to know in advance how long the work takes.

## Acceptance Criteria

- A call whose budget runs out on a `detach: true` command exits `14` with `data.state: "running"` and `data.continue_command` of the form `tool job wait <id>`
- A call whose budget runs out on a `resume: true, detach: false` command exits `14` with `data.state: "paused"` and `data.continue_command` equal to the original invocation
- On a command declared `mutating`, a `paused` response's `continue_command` carries `--idempotency-key`, and `error.retryable` is `false`
- Running `data.continue_command` verbatim, repeatedly, ends with the same response the work gives with `--budget 0`
- `data.progress.done` never decreases from one response of the same job to the next
- `tool job status <id>` exits `14` for a running job of an async command, not `3`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`exit-code.md`](../schemas/exit-code.md)

`INCOMPLETE (14)` in the `ExitCode` table. The `data` of the response conforms to:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | `"running"` \| `"paused"` | yes | `running`: the work continues in a background job; `paused`: it stopped at a checkpoint |
| `job_id` | string | yes | Identifier of the job or checkpoint |
| `progress` | object | yes | `done` (integer `≥ 0`, never decreasing), `total` (integer, when known), `unit` (string, when meaningful) |
| `continue_command` | string | yes | Exact invocation that continues the work |
| `cancel_command` | string | yes | Exact invocation that stops the work and discards its checkpoint |

---

## Wire Format

A read-only command handed to the background:

```json
{
  "ok": false,
  "data": {
    "state": "running",
    "job_id": "analyze-7f3a",
    "progress": { "done": 120000000, "total": 980000000, "unit": "bytes" },
    "continue_command": "tool job wait analyze-7f3a",
    "cancel_command": "tool job cancel analyze-7f3a"
  },
  "error": {
    "code": "INCOMPLETE",
    "message": "Call budget of 30000ms reached at 12%; the work continues in the background",
    "retryable": true
  },
  "warnings": [],
  "meta": { "exit_code": 14, "duration_ms": 30004, "budget_ms": 30000 }
}
```

A writing command paused at a checkpoint:

```json
{
  "ok": false,
  "data": {
    "state": "paused",
    "job_id": "import-c19e",
    "progress": { "done": 4000, "total": 25000, "unit": "rows" },
    "continue_command": "tool import rows.csv --idempotency-key imp-2f81",
    "cancel_command": "tool job cancel import-c19e"
  },
  "error": {
    "code": "INCOMPLETE",
    "message": "Call budget of 30000ms reached after 4000 of 25000 rows; state is saved",
    "retryable": false
  },
  "warnings": [],
  "meta": { "exit_code": 14, "duration_ms": 30870, "budget_ms": 30000 }
}
```

---

## Example

Framework-Automatic: the framework builds the response from the declaration, the job, and the last progress report.

```
on budget exhausted:
  entry = command.exit_codes[INCOMPLETE]
  continue = state == "running"
    ? "tool job wait " + job.id
    : original_argv + (command.writes ? ["--idempotency-key", job.key] : [])
  write envelope(ok=false, exit_code=14,
                 error={code: "INCOMPLETE", retryable: entry.retryable},
                 data={state, job_id: job.id, progress: job.last_progress,
                       continue_command: continue,
                       cancel_command: "tool job cancel " + job.id})

# Agent loop:
response = run(command)
stalls = 0
while response.exit_code == 14:
  previous = response.data.progress.done
  response = run(response.data.continue_command)
  if response.exit_code == 14 and response.data.progress.done <= previous:
    stalls += 1
    if stalls == 3: run(response.data.cancel_command); escalate
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Extends: adds `INCOMPLETE (14)` to the standard table |
| [REQ-F-080](f-080-sync-call-budget.md) | F | Consumes: the budget whose end produces this response |
| [REQ-F-081](f-081-detached-job-runtime.md) | F | Consumes: the job behind the `running` state and its `job wait` |
| [REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md) | C | Consumes: the checkpoint behind the `paused` state |
| [REQ-C-034](c-034-long-running-commands-report-progress.md) | C | Consumes: the progress report copied into `data.progress` |
| [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md) | C | Composes: `job status` of an async command uses this response for a running job |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Consumes: the key that makes a paused writer's continuation the same run |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Composes: `TIMEOUT` remains the response when work stops and is lost |
