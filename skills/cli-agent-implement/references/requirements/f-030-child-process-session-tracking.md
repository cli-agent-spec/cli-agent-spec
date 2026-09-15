# REQ-F-030: Child Process Session Tracking

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§17 Child Process Leakage](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

When a command spawns any child process using the framework's process-spawning API, the framework MUST record the child PID in a session-scoped tracking file. On parent process exit (normal, error, or signal), the framework MUST attempt to terminate all tracked children. The tracking file path MUST be included in the command's response as `meta.session_pid_file` when any children were spawned.

## Acceptance Criteria

- After a command that spawns a child process exits, no orphaned child processes remain in the process table
- The session tracking file exists and is readable while children are running
- `SIGTERM` to the parent causes the framework to send `SIGTERM` to all tracked children before the parent exits

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.session_pid_file` is a framework-injected extension to `ResponseMeta`, present when children were spawned

---

## Wire Format

`meta` in the response envelope when child processes were spawned:

```json
{
  "ok": true,
  "data": { "build_id": "bld_42" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 5210,
    "request_id": "req_01HZ",
    "session_pid_file": "/tmp/mytool/sessions/req_01HZ.pids"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. When a command uses the framework's process-spawning API, the framework writes each child PID to the session tracking file and registers a cleanup hook to terminate them on exit.

```
$ tool build --target all &
[1] 9001
→ /tmp/mytool/sessions/req_01HZ.pids created, contains: 9002 9003

$ kill -TERM 9001
→ framework forwards SIGTERM to PIDs 9002 and 9003
→ session tracking file removed
→ parent exits with code 143

$ tool build --target all   (command completes normally)
→ children exited normally
→ session tracking file removed
→ meta.session_pid_file absent (no orphan risk)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | F | Extends: uses the tracking file created here to forward SIGTERM to children |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM handler invokes child cleanup registered by this requirement |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries `meta.session_pid_file` |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Composes: session tracking file is stored within the session-scoped temp directory |
