> **Part II: Execution & Reliability** | Challenge §79

## 79. Work Outlives the Caller's Budget

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Medium

### The Problem

How long a command runs often depends on what it is given: the size of a file, the load of a remote service, the shape of the data. The caller cannot know it in advance, and the command cannot know the caller's limit. An agent's harness gives every tool call a fixed per-call budget, and a command that has not finished within it is killed. Nothing tells the agent, before or during the call, that this run needs longer.

**The work is killed, and the time is lost:**
```bash
$ tool analyze big.csv
# ... no output for 120 s ...
# the harness kills the call: exit 143, empty stdout
# 120 s of computation discarded; the agent knows nothing about how far it got
```

**The tool's own timeout tells the agent to retry into the same wall:**
```json
{
  "ok": false,
  "data": null,
  "error": { "code": "TIMEOUT", "message": "Command exceeded timeout of 60000ms", "retryable": true },
  "warnings": [],
  "meta": { "exit_code": 10, "duration_ms": 60004, "timeout_ms": 60000 }
}
```
A read-only command declares its timeout retryable because it wrote nothing. But its run length depends on its input, so the identical re-run times out again, at the same point, every time.

**Raising the limit only moves the wall:**
```bash
$ tool analyze big.csv --timeout 0
# the tool no longer stops itself, so the harness's own budget kills it instead
```

**Liveness signals do not reach a blocked caller.** Heartbeats and progress lines on stderr help a caller that reads the stream as it arrives. A harness that runs the command in the foreground sees its output only after exit, so a working command and a hung one look the same until the call is killed. The one moment the agent reliably reads is the process exit, and it comes too late.

Pieces of a fix exist elsewhere and do not cover this: an async command ([§49](../01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md)) returns a job at once, but only when its author knew in advance that it is always slow; `--resume-from` ([§13](13-critical-partial-failure.md)) needs a step name and an explicit flag; a SIGTERM handler ([§16](16-high-signal-handling.md)) saves state only when the signal arrives, and SIGKILL never does.

### Impact

- Minutes of completed work are discarded on every killed call, and repeated on every retry
- A retryable `TIMEOUT` on input-dependent work loops the agent into the same timeout until its budget is gone
- The agent cannot tell a long run from a hung one, so it either kills working commands or waits on dead ones
- Raising or removing the tool's timeout trades the tool's guard for the harness's kill, with no result either way
- After a kill, partial writes leave an unknown state, and the agent cannot resume what it cannot see

### Solutions

The rule: **a synchronous call is bounded, and work is never lost to a budget**. The command, not the agent, guarantees that every call returns within a known time, and that what it did is kept.

**Bounded calls (REQ-F-080):** in non-interactive mode, a call returns within a sync call budget (default `30000` ms, set by the harness through `AGENT_CALL_BUDGET_MS`, or by `--budget`), with either the result or an `INCOMPLETE` response.

**Hand off, do not kill (REQ-F-081):** work that can run unattended continues in a background job when the budget runs out; the call returns at once, the caller's pipes are released, and `tool job wait <id>` picks the work up again.

**Checkpoint continuously (REQ-C-035):** work made of chunks saves its state at every safe point, so an interruption from inside (the budget) or outside (SIGTERM, SIGKILL, OOM) loses at most one chunk, and the **identical invocation continues** from the last checkpoint. The agent's most natural recovery, "run it again", becomes correct even when the response was lost.

**One incomplete-work response (REQ-F-082):** exit `14` (`INCOMPLETE`), with `data.state` (`running` or `paused`), `data.progress`, and an exact `data.continue_command`:

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
  "error": { "code": "INCOMPLETE", "message": "Call budget of 30000ms reached at 12%; the work continues in the background", "retryable": true },
  "warnings": [],
  "meta": { "exit_code": 14, "duration_ms": 30004, "budget_ms": 30000 }
}
```

**Progress, not pulses (REQ-C-034):** growing `progress.done` between continuations is what tells working from hung; a background job whose progress stops ends as stalled.

**For CLI authors:**
- Declare `interruption: {detach, resume}` on every command whose run length you cannot bound (REQ-C-033); `detach` when the work can run unattended, `resume` when it is made of chunks
- Report progress on every chunk and checkpoint at every safe point; record committed units so a continuation never writes one twice
- Keep an honest `TIMEOUT` with `retryable: false` for work that is neither detachable nor resumable

**For framework design:**
- Own the process model: worker in its own session, the caller's descriptors closed, stdin spooled, state in a per-user job directory written by rename
- Key jobs and checkpoints by command, arguments, working directory, version, stdin, and idempotency key, so the identical invocation attaches or resumes
- Generate `job wait`, `job status`, and `job cancel`; detect a dead worker; end a stalled job; clean finished ones

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | A long command blocks until the tool's timeout or the caller's kill; the work is lost, and a `TIMEOUT` marked retryable sends the identical call into the same limit |
| 1 | The limit can be raised (`--timeout`, a per-command default), but every call still blocks for the whole run, past any caller's budget |
| 2 | The call returns within a bounded time with a structured response, but continuing needs a different command or flag, and the identical re-run starts over |
| 3 | Calls are bounded by the budget; `INCOMPLETE (14)` carries `progress` and `continue_command`; the identical invocation attaches to the running job or resumes from the last checkpoint, also after `kill -9` |

**Check:** Run a command whose work takes 20 s with `AGENT_CALL_BUDGET_MS=3000` under an outer 10 s timeout — verify exit `14` within about 4 s and a `continue_command`; run it until exit `0`. Repeat, `kill -9` the process group midway, rerun the identical invocation, and verify that `progress.done` does not restart from zero.

---

### Agent Workaround

**Signature:** a call killed by the harness's timeout (`exit 124`, `137`, or `143`) with little or no stdout, or `exit 10` with `"code": "TIMEOUT"` again on the identical rerun at about the same `duration_ms`

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** rerun once in the background with output to a file, then read the file in bounded checks; if it fails again, escalate with the command, exit code, stdout, and stderr

**Run the command outside the call's budget and poll it:**

```python
import json, os, subprocess, time

def run_long(cmd: list[str], log_dir: str, check_every_s: int = 20, max_checks: int = 30) -> dict:
    out_path = os.path.join(log_dir, "out.json")
    err_path = os.path.join(log_dir, "err.log")
    with open(out_path, "w") as out, open(err_path, "w") as err:
        proc = subprocess.Popen(
            cmd + ["--timeout", "0"],          # only when the tool has the flag
            stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            start_new_session=True,           # survives the call that started it
        )
    for _ in range(max_checks):               # in a harness, each check is its own short tool call
        if proc.poll() is not None:
            return json.loads(open(out_path).read().strip().splitlines()[-1])
        time.sleep(check_every_s)             # stderr growth between checks is the only liveness hint
    os.killpg(proc.pid, 15)
    return {"ok": False, "error": {"code": "TIMEOUT", "message": f"no result after {max_checks} checks"}}
```

**Limitation:** The work is not checkpointed, so a kill or a lost session still discards it and the next run starts over; a tool that reports no progress gives no way to tell a slow run from a hung one, and a harness that kills orphaned processes at the end of a call or session defeats the background run
