> **Part II: Execution & Reliability** | Challenge §17

## 17. Child Process Leakage

**Severity:** Medium | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Low | **Time:** Low | **Context:** Low

### The Problem

CLI tools frequently spawn background processes — log forwarders, file watchers, health monitors, connection pools. When the main CLI process exits, these children are often orphaned, accumulating over time and consuming resources.

**Orphaned children from normal exit:**
```bash
$ tool start-watcher --dir /project
# Spawns: inotify daemon (PID 5678)
# Main process exits: 0
# inotify daemon: still running, never cleaned up

# After 100 agent calls: 100 inotify daemons running
```

**Children that hold locks:**
```bash
$ tool sync
# Spawns background sync process that holds /var/lock/tool.lock
# Main process exits
# Lock never released
# Next `tool sync` call: "Error: lock held by PID 5678 (defunct)"
```

**Children that write to stdout after parent exits:**
```bash
$ tool deploy
# Spawns background health-check process
# Main process exits, prints JSON result
# 2 seconds later: background process prints "health: ok" to stdout
# Agent's JSON parse of captured output now fails (extra text after valid JSON)
```

**Signal not forwarded to children:**
```bash
$ kill -TERM $TOOL_PID
# Tool exits cleanly
# But spawned children never received SIGTERM
# They run forever as orphans owned by init/PID1
```

### Impact

- Resource exhaustion: file descriptors, memory, CPU from accumulated orphans
- Lock files held by dead-parent children block all future invocations
- Stdout corruption from children writing after parent exits
- Containers/VMs accumulate ghost processes that survive restarts

### Solutions

**Process group management:**
```python
import os, signal, atexit

# Start child in its own process group
child = subprocess.Popen(
    ["child-process"],
    start_new_session=True,   # new process group
    preexec_fn=os.setsid
)

# On exit, kill the entire process group
def cleanup():
    try:
        os.killpg(os.getpgid(child.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass  # already dead

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda *_: (cleanup(), sys.exit(143)))
```

**PID file tracking:**
```bash
$ tool start-watcher --dir /project
# Writes child PIDs to: /tmp/tool-session-42/children.pids
# Provides cleanup command:
{
  "ok": true,
  "background_pid": 5678,
  "cleanup_command": "tool stop-watcher --session 42",
  "pid_file": "/tmp/tool-session-42/children.pids"
}
```

**Mandatory child tracking in schema:**
```json
{
  "command": "start-watcher",
  "spawns_background_process": true,
  "cleanup_command": "stop-watcher",
  "max_lifetime_seconds": 3600
}
```

**Stdout close before spawning detached children:**
```python
# If spawning a truly detached daemon:
# 1. Complete all stdout writes and flush
# 2. Close stdout
# 3. Only then fork the background process
sys.stdout.flush()
sys.stdout.close()
child = subprocess.Popen(["daemon"], close_fds=True, stdin=DEVNULL,
                          stdout=DEVNULL, stderr=DEVNULL)
```

**For framework design:**
- Framework tracks all child PIDs in a session file automatically
- `tool session cleanup --id $SESSION` kills all tracked children
- Commands that spawn background processes must declare `spawns_background_process: true`
- Framework installs a SIGTERM handler that forwards to all tracked children before exit

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Background children orphaned on exit; stdout receives child output after parent exits; locks held by orphans |
| 1 | Cleanup command documented but not declared in output; SIGTERM not forwarded to children |
| 2 | Cleanup command returned in JSON output; SIGTERM forwarded to tracked children |
| 3 | All children tracked in session-scoped PID file; `tool session cleanup` kills all; `spawns_background_process` declared in manifest |

**Check:** Invoke a command that spawns background processes, note the child PIDs from the output, let the parent exit, then verify child PIDs are no longer running.

---

### Agent Workaround

**Signature:** stray processes remain after the CLI exits `0`, accumulating per call; next run fails with `lock held by PID`; extra lines appear on stdout after the final JSON

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** run the `cleanup_command` reported in the previous JSON output; if that fails, escalate with the command, exit code, stdout, and stderr

**Track background PIDs from command output and clean them up before the next invocation:**

```python
result = run(["tool", "start-watcher", "--dir", "/project"])
parsed = json.loads(result.stdout)

background_pid = parsed.get("background_pid")
cleanup_cmd = parsed.get("cleanup_command")
pid_file = parsed.get("pid_file")

# Register cleanup to run before next invocation or on agent exit
import atexit, os, signal

def cleanup_children():
    if cleanup_cmd:
        run(cleanup_cmd.split())  # use declared cleanup command
    elif background_pid:
        try:
            os.kill(background_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass  # already dead

atexit.register(cleanup_children)
```

**Kill the entire process group to catch all descendants:**
```python
import os, signal
# If you know the child's PID, kill its entire process group
try:
    os.killpg(os.getpgid(background_pid), signal.SIGTERM)
except (ProcessLookupError, PermissionError):
    pass
```

**Limitation:** If the tool does not declare `background_pid` or `cleanup_command` in its JSON output, the agent has no reliable way to track orphaned children — check for lingering lock files before the next invocation and alert if they exist
