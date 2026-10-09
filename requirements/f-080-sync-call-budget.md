# REQ-F-080: Sync Call Budget

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§79 Work Outlives the Caller's Budget](../challenges/02-critical-execution-and-reliability/79-critical-work-outlives-budget.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Medium

---

## Description

The framework MUST bound the time a call to a command that declares `interruption` ([REQ-C-033](c-033-commands-declare-interruption.md)) holds its caller. In non-interactive mode ([REQ-F-009](f-009-non-interactive-mode-auto-detection.md)) such a call MUST return within the **sync call budget**: either with the command's result, or with an `INCOMPLETE (14)` response ([REQ-F-082](f-082-incomplete-work-response.md)) once the budget runs out. Running out of budget never discards work. A command declaring `detach: true` hands the work to a background job ([REQ-F-081](f-081-detached-job-runtime.md)); a command declaring only `resume: true` stops at its next checkpoint ([REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md)) and saves it.

The budget resolves in this order: the `--budget <duration>` flag, then the `AGENT_CALL_BUDGET_MS` environment variable, then the framework default of `30000` ms. `--budget 0` turns the budget off: the call holds its caller until the work ends, bounded only by the wall-clock limit. The environment variable carries no tool prefix because the caller's harness sets it once for every tool it runs; a framework MUST read it under this exact name. In a TTY the budget applies only when `--budget` is passed, so a person keeps the ordinary synchronous run.

The budget bounds one call; it is not the wall-clock limit of [REQ-F-011](f-011-default-timeout-per-command.md). `--timeout` keeps bounding the whole work across every continuation. A command that knows from a cheap estimate (input size, item count) that the work cannot finish within the budget MAY hand it off or checkpoint before the budget runs out.

The framework MUST record the budget in force in `meta.budget_ms` on every response of a command that declares `interruption`.

## Acceptance Criteria

- With `AGENT_CALL_BUDGET_MS=2000`, a `detach: true` command whose work takes 10 s exits `14` within 3 s, and its work completes in the background
- With `AGENT_CALL_BUDGET_MS=2000`, a `resume: true, detach: false` command exits `14` after the first checkpoint past 2 s, and the identical invocation continues from that checkpoint
- `--budget 5s` takes precedence over `AGENT_CALL_BUDGET_MS`; with neither, the budget is `30000` ms
- `--budget 0` returns only when the work ends or `--timeout` fires; `meta.budget_ms` is `0`
- Work that finishes within the budget returns its ordinary response with its own exit code and `meta.budget_ms`
- In a TTY without `--budget`, the command runs synchronously and `meta.budget_ms` is absent
- A command that does not declare `interruption` has no `--budget` flag and ignores `AGENT_CALL_BUDGET_MS`; it keeps the wall-clock limit of REQ-F-011

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md)

`ResponseMeta.budget_ms` records the budget in force. The framework registers `--budget` on every command whose `CommandEntry` carries `interruption`.

---

## Wire Format

```bash
$ AGENT_CALL_BUDGET_MS=30000 tool analyze big.csv
```

The work finished within the budget:

```json
{
  "ok": true,
  "data": { "rows": 1048576, "mean": 41.7 },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 8120, "budget_ms": 30000, "timeout_ms": 3600000 }
}
```

The budget ran out first: see the `INCOMPLETE` response in [REQ-F-082](f-082-incomplete-work-response.md).

---

## Example

Framework-Automatic: the command author declares `interruption`; the framework resolves the budget and enforces it.

```
budget = flag("--budget") ?? env("AGENT_CALL_BUDGET_MS") ?? 30000
if is_tty() and not flag_given("--budget"):
  budget = none

run command:
  if budget is none or budget == 0:
    wait for the work to end (bounded by --timeout)
  else if work ends within budget:
    write the command's response
  else if command.interruption.detach:
    hand the work to a background job (REQ-F-081); write INCOMPLETE with state "running"
  else:
    request a stop at the next checkpoint (REQ-C-035); write INCOMPLETE with state "paused"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-033](c-033-commands-declare-interruption.md) | C | Consumes: the `interruption` declaration that opts a command into the budget |
| [REQ-F-081](f-081-detached-job-runtime.md) | F | Composes: a `detach` command's work continues there when the budget runs out |
| [REQ-C-035](c-035-resumable-commands-checkpoint-at-safe-points.md) | C | Composes: a `resume` command stops at its next checkpoint when the budget runs out |
| [REQ-F-082](f-082-incomplete-work-response.md) | F | Provides: the response written when the budget runs out |
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Composes: the wall-clock limit bounds the whole work; the budget bounds one call |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Consumes: non-interactive detection decides whether the default budget applies |
