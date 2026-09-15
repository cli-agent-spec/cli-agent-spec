> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §60

## 60. OS Output Buffer Deadlock

**Source:** Antigravity `01_io_and_formatting.md` (RA)

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

When a CLI tool's stdout is connected to a pipe rather than a TTY, the OS switches from line-buffered to fully-buffered mode (typically 4KB or 8KB blocks). A tool that emits incremental progress logs one line at a time appears completely silent to the agent — output accumulates in the kernel buffer and is released only when the buffer fills or the process exits. The agent sees no output for minutes, then receives everything at once (or nothing if the tool crashes mid-way and the buffer is lost).

```bash
# Tool emits one log line per second to stdout:
$ my-tool migrate --env prod | agent-receiver
# Agent sees... nothing for 4 minutes
# Then receives all 240 log lines simultaneously when buffer flushes
# Agent cannot tell: is the tool running? stuck? crashed?

# The OS buffer behavior is invisible to both the tool and the agent:
$ strace -e write my-tool migrate 2>/dev/null
write(1, "Step 1/10: validating...\n", 25) = 25  # buffered by OS, not sent yet
write(1, "Step 2/10: connecting...\n", 25) = 25   # still buffered
# ...240 more writes... buffer fills at 4KB → flush → agent receives everything
```

This is the **pipe buffering problem**: standard C library `stdio` and Python's `sys.stdout` switch to block-buffered mode when output is not a TTY.

### Impact

- Agent receives no output for the entire duration of a long-running command
- No heartbeat, no progress — agent cannot distinguish "running" from "hung"
- Agent's timeout fires before buffer flushes; all output lost
- Error output (if on stdout) arrives only at the end, too late for the agent to react

### Solutions

**Unbuffer stdout explicitly in non-TTY mode:**
```python
# Python: disable buffering
import sys, os
if not sys.stdout.isatty():
    sys.stdout.reconfigure(line_buffering=True)
    # or: os.environ['PYTHONUNBUFFERED'] = '1'
```

```bash
# Wrapper: force unbuffered output
$ stdbuf -o0 my-tool migrate
$ unbuffer my-tool migrate   # via expect package
```

**Emit JSON heartbeats every N seconds for long operations:**
```json
{"status": "running", "step": "migrating table users", "elapsed_ms": 5000, "heartbeat": true}
```

**For framework design:**
- Framework MUST call `sys.stdout.reconfigure(line_buffering=True)` (Python) or `setvbuf(stdout, NULL, _IOLBF, 0)` (C) on startup when stdout is not a TTY
- Long-running commands MUST emit a JSON heartbeat object to stdout every configurable interval (default: 10s) so the agent has proof of life
- `PYTHONUNBUFFERED=1` and equivalent env vars MUST be set in the framework's bootstrap before any output

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Output fully buffered in non-TTY mode; agent receives no output until process exits (or buffer fills); no heartbeat |
| 1 | `PYTHONUNBUFFERED=1` respected; output released in 4KB blocks; no heartbeat for long-running commands |
| 2 | Line-buffered in non-TTY mode; long-running commands emit JSON heartbeats every ≤30s |
| 3 | Framework explicitly configures line buffering on startup; heartbeat interval configurable; heartbeat includes `elapsed_ms` and `step` |

**Check:** Run a long-running command and monitor stdout in real time — verify JSON lines appear incrementally (not all at once at the end).

---

### Agent Workaround

**Signature:** no output for minutes on a long-running command, then all lines arrive at once; killed by timeout with empty or truncated stdout

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** `PYTHONUNBUFFERED=1 stdbuf -o0 timeout 300 tool <args> </dev/null`; if that fails, escalate with the command, exit code, stdout, and stderr

**Set `PYTHONUNBUFFERED=1`; use `stdbuf` wrapper; implement a heartbeat-based liveness check:**

```python
import subprocess, json, threading, time, os

env = {
    **os.environ,
    "PYTHONUNBUFFERED": "1",    # Python: line-buffer stdout
    "FORCE_TTY_OUTPUT": "1",    # some tools check this
}

def run_with_heartbeat_check(
    cmd: list[str],
    timeout: int = 300,
    heartbeat_interval: int = 30,
) -> dict:
    last_output_time = [time.monotonic()]
    output_lines = []

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL,
    )

    def read_stdout():
        for line in proc.stdout:
            last_output_time[0] = time.monotonic()
            output_lines.append(line)

    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()

    start = time.monotonic()
    while proc.poll() is None:
        elapsed = time.monotonic() - start
        since_last = time.monotonic() - last_output_time[0]

        if elapsed > timeout:
            proc.kill()
            raise TimeoutError(f"Command exceeded {timeout}s total timeout")

        if since_last > heartbeat_interval and elapsed > heartbeat_interval:
            print(f"WARNING: No output for {since_last:.0f}s — possible buffer deadlock")

        time.sleep(1)

    reader.join(timeout=5)
    stdout = "".join(output_lines)
    return json.loads(stdout)
```

**Limitation:** If the tool uses fully-buffered stdout and ignores `PYTHONUNBUFFERED`, `stdbuf -o0 <cmd>` can force unbuffering at the OS level — but this requires `stdbuf` (from GNU coreutils) to be available in the execution environment
