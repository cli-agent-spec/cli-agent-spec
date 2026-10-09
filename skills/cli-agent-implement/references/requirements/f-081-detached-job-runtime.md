# REQ-F-081: Detached Job Runtime

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md) · [§49 Async Job / Polling Protocol Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

For a command declaring `interruption.detach: true` ([REQ-C-033](c-033-commands-declare-interruption.md)), the framework MUST let the work outlive the call: when the sync call budget runs out ([REQ-F-080](f-080-sync-call-budget.md)), the work continues as a background job and the call returns `INCOMPLETE (14)` with `data.state: "running"` ([REQ-F-082](f-082-incomplete-work-response.md)). The command's handler is unchanged; the framework owns the process model.

The framework MUST guarantee these observable properties; the mechanism is the framework's choice ([`IMPLEMENTING.md`](../IMPLEMENTING.md#long-running-commands) gives a reference pattern):

- **The caller is released.** Once the response is written, the front process exits and every descriptor it shares with the caller (stdin, stdout, stderr) is closed, so a caller reading to end-of-file returns. A background job that keeps the caller's pipe open hangs the caller as surely as a blocked call
- **The job is detached.** The job runs in its own session or process group, so a signal to the caller's process group, or the caller's terminal closing, does not reach it. SIGTERM to the front process before the budget runs out hands the work off at once and writes the response instead of killing it ([REQ-F-013](f-013-sigterm-handler-installation.md))
- **The job's state outlives the front process.** Status, progress, the final response, and the log live in a per-user job directory outside the session temp directory ([REQ-F-032](f-032-session-scoped-temp-directory.md)), written atomically ([REQ-F-070](f-070-atomic-write-via-rename.md)). Stdin is read to a file in the job directory before the job starts, so the job never reads the caller's stdin
- **The job is reachable.** The framework generates `tool job wait <id>`, `tool job status <id>`, and `tool job cancel <id>`, shared with [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md). `job wait` holds its caller up to the sync call budget: it returns the job's final response, with the command's own exit code, when the job ends; otherwise `INCOMPLETE (14)` with fresh `data.progress`. `job cancel` stops the job at its next checkpoint or progress report, discards its checkpoint, and exits `0`
- **The identical invocation attaches.** The framework keys each job by the command path, the normalized arguments, the working directory, the tool version, a digest of stdin, and the `--idempotency-key` when given ([REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md)). Repeating an invocation whose job is still running attaches to that job, behaving as `job wait`, and never starts a second one
- **A dead job is reported, not waited on.** A job whose worker has exited without writing a terminal status ends as failed: `job wait` and `job status` return `GENERAL_ERROR (1)` with `error.code: "JOB_LOST"` and the tail of the job log in `error.detail`. With `resume: true` too, the identical invocation then starts a new job from the last checkpoint
- **A stalled job ends.** A job whose `progress.done` ([REQ-C-034](c-034-long-running-commands-report-progress.md)) does not change for `interruption.idle_timeout_ms` (default `300000`) ends with `TIMEOUT (10)` and `error.code: "STALLED"`. A job also ends with `TIMEOUT (10)` when the whole work exceeds `--timeout`, or `interruption.max_lifetime_ms` (default `3600000`) when no `--timeout` was passed
- **Finished jobs are cleaned.** A job directory is removed a retention period (default 24 h) after its job ends; until then `job wait` returns the stored final response

## Acceptance Criteria

- With a 2 s budget, `tool analyze big.csv | cat` returns within 3 s of the budget running out: the pipe reaches end-of-file although the job runs on
- `kill -TERM -<pgid>` on the caller's process group after the response leaves the job running
- `tool job wait <id>` exits `14` with a larger `data.progress.done` while the job runs, and with the command's own exit code and response once it ends
- Repeating the original invocation while its job runs prints that job's `job_id` and starts no second job
- `kill -9` on the job's worker makes the next `job wait` exit `1` with `error.code: "JOB_LOST"` instead of waiting
- A job whose handler stops reporting progress ends after `idle_timeout_ms` with exit `10` and `error.code: "STALLED"`
- `tool job cancel <id>` exits `0`, the job stops, and the identical invocation then starts from the beginning

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md) · [`exit-code.md`](../schemas/exit-code.md)

`CommandEntry.interruption` carries `detach`, `idle_timeout_ms`, and `max_lifetime_ms`. The responses of `job wait` and `job status` for a running job are the `INCOMPLETE` response of [REQ-F-082](f-082-incomplete-work-response.md).

---

## Wire Format

```bash
$ tool job wait analyze-7f3a
```

The job ended while `job wait` held the call, which returns the job's stored final response; `duration_ms` is the work's, not the wait's:

```json
{
  "ok": true,
  "data": { "rows": 9437184, "mean": 41.9 },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 214380, "timeout_ms": 3600000 }
}
```

The job's worker died:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "JOB_LOST",
    "message": "Job analyze-7f3a ended without a result; its worker exited",
    "detail": "MemoryError at chunk 412",
    "retryable": false
  },
  "warnings": [],
  "meta": { "exit_code": 1, "duration_ms": 12 }
}
```

---

## Example

Framework-Automatic: the command author declares `interruption.detach`; nothing in the handler changes.

```
front process (the call):
  job = job_directory.create(key(command, args, cwd, version, stdin_digest, idempotency_key))
  if job.already_running: return job_wait(job)
  spool stdin to job.dir/stdin
  worker = spawn(tool, "--job-worker", job.id,
                 new_session=true, stdin=null, stdout=job.log, stderr=job.log)
  wait for worker up to budget
  if worker ended: write job.result; exit with its code
  else: write INCOMPLETE {state: "running", job_id, progress, continue_command: "tool job wait <id>"}; exit 14

worker process (the job):
  run the handler; every ctx.progress() updates job.status and feeds the idle watchdog
  write job.result atomically; mark job terminal
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-080](f-080-sync-call-budget.md) | F | Consumes: the budget whose end triggers the handoff, and that bounds each `job wait` |
| [REQ-C-033](c-033-commands-declare-interruption.md) | C | Consumes: `interruption.detach` and the job's idle and lifetime limits |
| [REQ-C-034](c-034-long-running-commands-report-progress.md) | C | Consumes: progress reports that feed `data.progress` and the idle watchdog |
| [REQ-F-082](f-082-incomplete-work-response.md) | F | Provides: the `running` state of the incomplete-work response |
| [REQ-C-022](c-022-async-commands-declare-job-descriptor-schema.md) | C | Extends: the generated `job` subcommands serve jobs started by the budget too |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM before the budget hands the work off instead of killing it |
| [REQ-F-070](f-070-atomic-write-via-rename.md) | F | Composes: job status and results are written by rename |
| [REQ-C-010](c-010-background-process-commands-declare-metadata.md) | C | Specializes: a background process the framework starts and tracks itself, with its own lifetime bound |
