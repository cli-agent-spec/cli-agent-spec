# REQ-C-034: Long-Running Commands Report Progress

**Tier:** Command Contract | **Priority:** P1

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md) · [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

A command that declares `interruption` ([REQ-C-033](c-033-commands-declare-interruption.md)) MUST report its progress through the framework's `ctx.progress(done, total?, unit?)` API as the work advances, at least once every 10 seconds of work. `done` is a count of completed work units (bytes, rows, items, steps) and MUST never decrease within one run or across its continuations; `total` is the expected count when known; `unit` names the units.

Progress is what tells working from hung. A timer that ticks while a worker thread is deadlocked proves only that the process is alive; a growing `done` proves that the work advances. The framework uses each report three ways:

- `data.progress` of the `INCOMPLETE` response ([REQ-F-082](f-082-incomplete-work-response.md)), which the agent compares between continuations
- the idle watchdog of a background job ([REQ-F-081](f-081-detached-job-runtime.md)): a job whose `done` stops changing ends as stalled
- the status text of the heartbeat when one is enabled ([REQ-O-012](o-012-heartbeat-interval-flag.md))

A report is cheap: the framework records the latest values and throttles writes to the job's status; a handler may call it on every chunk.

## Acceptance Criteria

- A command declaring `interruption` calls `ctx.progress()` at least once every 10 s of work in its test suite's longest fixture
- `data.progress.done` in successive `INCOMPLETE` responses of one job never decreases, including after a resume from a checkpoint
- A handler that stops calling `ctx.progress()` while its process stays alive is ended by the idle watchdog of REQ-F-081
- Calling `ctx.progress()` with a `done` lower than the previous report raises a framework error in test mode

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The values reach the wire only as `data.progress` of the `INCOMPLETE` response: `{done, total?, unit?}`.

---

## Wire Format

```json
{ "done": 120000000, "total": 980000000, "unit": "bytes" }
```

---

## Example

```
execute(args, ctx):
  total = file_size(args.file)
  for chunk in read_chunks(args.file):
    stats.add(chunk)
    ctx.progress(done=chunk.end, total=total, unit="bytes")
  return stats.summary()
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-033](c-033-commands-declare-interruption.md) | C | Consumes: every command declaring `interruption` reports progress |
| [REQ-F-082](f-082-incomplete-work-response.md) | F | Provides: `data.progress` of the incomplete-work response |
| [REQ-F-081](f-081-detached-job-runtime.md) | F | Provides: the signal the idle watchdog watches |
| [REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md) | C | Composes: a checkpoint carries the `done` a resumed run continues from |
| [REQ-O-012](o-012-heartbeat-interval-flag.md) | O | Provides: the status text of a heartbeat line |
