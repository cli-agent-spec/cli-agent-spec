# REQ-F-031: SIGTERM Forwarding to Tracked Children

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§17 Child Process Leakage](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

The framework's SIGTERM handler (REQ-F-013) MUST forward `SIGTERM` to all children tracked in the session before emitting the cancellation JSON and exiting. The framework MUST wait up to a configurable grace period for children to exit before sending `SIGKILL`.

## Acceptance Criteria

- A child process registered with the framework receives `SIGTERM` when the parent receives `SIGTERM`
- If a child does not exit within the grace period, the framework sends `SIGKILL` to that child
- The parent's cancellation JSON output is emitted after children have been signaled

---

## Schema

No dedicated schema type — this requirement governs SIGTERM forwarding behavior without adding new wire-format fields beyond what `response-envelope.md` already defines

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework's SIGTERM handler (REQ-F-013) reads the session PID file populated by REQ-F-030, forwards `SIGTERM` to each tracked child, waits for the configurable grace period, sends `SIGKILL` to any survivors, then emits the cancellation JSON.

```
$ tool build --target all &
[1] 9001
→ children tracked: PIDs 9002, 9003

$ kill -TERM 9001
→ framework sends SIGTERM to 9002 and 9003
→ grace period: 5s
→ PID 9002 exited normally within grace period
→ PID 9003 did not exit → framework sends SIGKILL to 9003
→ parent emits cancellation JSON and exits with code 143
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Extends: the SIGTERM handler installed here forwards to children before emitting cancellation JSON |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Provides: session PID file that this requirement reads to find children to signal |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: cancellation JSON envelope emitted after children are signaled |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Composes: session temp directory is cleaned up after child processes are terminated |
