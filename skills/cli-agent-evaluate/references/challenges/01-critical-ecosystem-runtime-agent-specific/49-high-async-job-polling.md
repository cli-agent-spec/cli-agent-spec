> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §49

## 49. Async Job / Polling Protocol Absence

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

Many CLI operations are inherently asynchronous — deployments, builds, data migrations, batch exports. Tools handle this in two broken ways: (a) block synchronously until completion, consuming the agent's entire timeout budget with no progress signal, or (b) return a job ID immediately with no documented machine-readable protocol for status polling, interpreting completion states, or cancellation.

```bash
# Pattern A: blocks silently until done (or forever)
$ tool deploy --env prod
# ... hangs for 8 minutes with no output ...
# Agent's timeout fires; tool killed mid-deploy; partial state

# Pattern B: returns job ID but protocol is undocumented
$ tool deploy --env prod --async
Job started: dep_abc123
$ echo $?
0   # exit 0 means... "job submitted" or "job done"?

$ tool job status dep_abc123
Running... (60%)
$ echo $?
0   # exit 0 means "query succeeded" or "job completed"?
# Agent cannot distinguish "still running" from "done"
```

Compound failure: agent must guess the polling interval, doesn't know the maximum wait time, and has no way to cancel a runaway job once started.

### Impact

- Agent burns entire timeout budget on synchronous jobs
- Agent misreads `exit 0` from a status query as job completion, proceeds prematurely
- Agent has no cancellation path for a runaway job
- Job IDs may not be valid across sessions; no way to resume a disrupted poll loop

### Solutions

**Async commands MUST return a typed job descriptor:**
```json
{
  "ok": true,
  "data": {
    "job_id": "dep_abc123",
    "status": "running",
    "terminal": false,
    "status_command": "tool job status dep_abc123",
    "cancel_command": "tool job cancel dep_abc123",
    "poll_interval_ms": 5000,
    "timeout_ms": 600000,
    "started_at": "2024-03-11T14:00:00Z"
  }
}
```

**Status command uses distinct exit codes:**
```
exit 0  = job complete (terminal, success)
exit 3  = job still running (non-terminal, poll again)
exit 4  = job failed (terminal, failure)
exit 7  = job timed out (terminal)
exit 5  = job ID not found / expired
```

**Terminal vs non-terminal distinction in response:**
```json
{ "status": "running", "terminal": false, "progress_pct": 60 }
{ "status": "complete", "terminal": true, "result": {...} }
```

**For framework design:**
- Provide a first-class `AsyncJob` return type; framework automatically generates `job status <id>` and `job cancel <id>` subcommands
- The job descriptor schema (status_command, cancel_command, poll_interval_ms, timeout_ms) must be part of the standard response envelope for any async operation
- Document the exit code contract for status commands prominently as part of the framework's standard

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Async commands either block synchronously or return a job ID with no status protocol; exit codes from status commands undocumented |
| 1 | `--async` flag returns a job ID; status command exists but exit code is always 0 regardless of job state |
| 2 | Async response includes `job_id`, `status_command`, `poll_interval_ms`; status command uses distinct exit codes (0=done, 3=running, 4=failed) |
| 3 | Full job descriptor with `cancel_command`, `timeout_ms`, `terminal` field; `job status` and `job cancel` framework-generated; `status` field uses machine-readable enum |

**Check:** Start an async job and immediately call the status command — verify exit code is 3 (not 0) while running, and exit code changes to 0 when complete.

---

### Agent Workaround

**Signature:** long-running command blocks silently until timeout; or returns a job ID with `exit 0` and the status query also exits `0` while the job still runs

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** `timeout 600 tool <args> </dev/null` run synchronously without `--async`; if that fails, escalate with the command, exit code, stdout, and stderr

**Use the `status_command` from the job descriptor; poll with `terminal` field; respect `poll_interval_ms`:**

```python
import subprocess, json, time

def run_async_job(cmd: list[str], max_wait_s: int = 600) -> dict:
    # Start the async job
    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = json.loads(result.stdout)
    if not parsed.get("ok"):
        raise RuntimeError(f"Job start failed: {parsed}")

    job = parsed["data"]
    job_id = job["job_id"]
    status_cmd = job.get("status_command", f"tool job status {job_id}").split()
    cancel_cmd = job.get("cancel_command", f"tool job cancel {job_id}").split()
    poll_ms = job.get("poll_interval_ms", 5000)
    timeout_ms = job.get("timeout_ms", max_wait_s * 1000)

    deadline = time.monotonic() + timeout_ms / 1000

    while True:
        if time.monotonic() > deadline:
            subprocess.run(cancel_cmd, capture_output=True)
            raise TimeoutError(f"Job {job_id} exceeded {timeout_ms}ms timeout; cancelled")

        time.sleep(poll_ms / 1000)

        status_result = subprocess.run(status_cmd, capture_output=True, text=True)
        status_parsed = json.loads(status_result.stdout)
        status_data = status_parsed.get("data", {})

        # Prefer "terminal" field; fall back to exit code
        if status_data.get("terminal") or status_result.returncode == 0:
            if status_data.get("status") == "failed" or status_result.returncode == 4:
                raise RuntimeError(f"Job {job_id} failed: {status_data}")
            return status_parsed  # job complete

        if status_result.returncode == 4:
            raise RuntimeError(f"Job {job_id} failed: {status_data}")

return {}
```

**Limitation:** If the tool provides no `status_command` or `terminal` field, the agent must guess whether exit 0 means "status query succeeded" or "job completed" — use the presence of a `result` field in the response as a proxy for completion, but this is fragile and tool-specific
