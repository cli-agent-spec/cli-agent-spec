# REQ-C-035: Resumable Commands Checkpoint at Safe Points

**Tier:** Command Contract | **Priority:** P2

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md) · [§13 Partial Failure & Atomicity](../challenges/02-critical-execution-and-reliability/13-critical-partial-failure.md) · [§16 Signal Handling & Graceful Cancellation](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

A command declaring `interruption.resume: true` ([REQ-C-033](c-033-commands-declare-interruption.md)) MUST save its state continuously, not at the moment it is interrupted. A process killed with SIGKILL, by the OOM killer, or with its host gets no chance to save anything, so a checkpoint written only on SIGTERM ([§16](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md)) protects nothing in the cases that matter most.

The command MUST:

- call `ctx.restore(fingerprint)` before any work, where `fingerprint` identifies the inputs the state depends on (a file's size and modification time, a query's parameters); it returns the last saved state, or nothing when there is none or the fingerprint differs
- call `ctx.checkpoint(state)` at each safe point (a boundary between chunks, rows, or steps), at least once every 10 seconds of work; `state` is JSON-serializable and holds everything needed to continue, including the progress `done` ([REQ-C-034](c-034-long-running-commands-report-progress.md))
- for writing work, record in `state` which units are committed, so that a continuation skips them and never writes a unit twice

The framework MUST:

- key checkpoints like jobs ([REQ-F-081](f-081-detached-job-runtime.md)): command path, normalized arguments, working directory, tool version, stdin digest, and `--idempotency-key`, so that the identical invocation finds its checkpoint without being told
- write each checkpoint atomically ([REQ-F-070](f-070-atomic-write-via-rename.md)), so a kill during the write leaves the previous one intact
- honour a stop request (the budget of [REQ-F-080](f-080-sync-call-budget.md), SIGTERM, `job cancel`) inside `ctx.checkpoint()`, after the state is saved, so the work stops only at a safe point
- discard a checkpoint whose fingerprint no longer matches, start over, and add a `CHECKPOINT_DISCARDED` warning naming the reason
- remove the checkpoint when the work completes or is cancelled

Work done after the last checkpoint is lost on a kill and redone on the next run; for writing work this is safe only because committed units are recorded and skipped. [REQ-O-010](o-010-resume-from-flag-for-multi-step-commands.md)'s `--resume-from <step>` stays the explicit form for multi-step commands; a checkpoint makes the plain re-run resume.

## Acceptance Criteria

- `kill -9` on a `resume: true` command midway, then the identical invocation, ends with the same result as an uninterrupted run, and its first `data.progress.done` is not below the last checkpoint's
- The resumed run of a writing command commits no unit twice
- Changing the input file between runs produces a `CHECKPOINT_DISCARDED` warning and a run from the start
- A stop requested by the budget, SIGTERM, or `job cancel` takes effect at the next `ctx.checkpoint()` call, never between a write and the checkpoint that records it
- After a completed run, the identical invocation starts fresh, with no checkpoint left behind

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

No dedicated schema type: checkpoints live in the framework's job directory and never reach the wire. A discarded checkpoint surfaces as a `CHECKPOINT_DISCARDED` entry in `warnings`.

---

## Wire Format

The identical invocation after the input changed:

```json
{
  "ok": true,
  "data": { "rows": 1048577, "mean": 41.6 },
  "error": null,
  "warnings": [
    { "code": "CHECKPOINT_DISCARDED", "message": "Input changed since the checkpoint; started over", "context": { "job_id": "analyze-7f3a" } }
  ],
  "meta": { "exit_code": 0, "duration_ms": 9310, "budget_ms": 30000 }
}
```

---

## Example

```
register command "analyze":
  interruption: { detach: true, resume: true }

  execute(args, ctx):
    state = ctx.restore(fingerprint=[file_size(args.file), file_mtime(args.file)])
            or { offset: 0, stats: Stats() }
    total = file_size(args.file)
    for chunk in read_chunks(args.file, start=state.offset):
      state.stats.add(chunk)
      state.offset = chunk.end
      ctx.progress(done=state.offset, total=total, unit="bytes")
      ctx.checkpoint(state)   # safe point: the framework may stop or hand off here
    return state.stats.summary()
```

The analysis logic is unchanged; the declaration, `restore`, `progress`, and `checkpoint` are the author's whole share.

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-033](c-033-commands-declare-interruption.md) | C | Consumes: `resume: true` is the promise this requirement keeps |
| [REQ-F-082](f-082-incomplete-work-response.md) | F | Provides: the checkpoint behind the `paused` state |
| [REQ-F-080](f-080-sync-call-budget.md) | F | Consumes: the budget's stop request, honoured at the next checkpoint |
| [REQ-F-081](f-081-detached-job-runtime.md) | F | Composes: a lost job resumes from the last checkpoint |
| [REQ-C-034](c-034-long-running-commands-report-progress.md) | C | Composes: the checkpoint carries the progress a resumed run reports |
| [REQ-F-070](f-070-atomic-write-via-rename.md) | F | Composes: checkpoints are written by rename |
| [REQ-O-010](o-010-resume-from-flag-for-multi-step-commands.md) | O | Extends: the plain re-run resumes, where `--resume-from` needs a step name |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Consumes: the key that ties a writer's continuation to its checkpoint |
