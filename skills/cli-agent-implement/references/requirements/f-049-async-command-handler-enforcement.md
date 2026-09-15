# REQ-F-049: Async Command Handler Enforcement

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§40 `parse()` vs `parseAsync()` Silent Race Condition](../challenges/01-critical-ecosystem-runtime-agent-specific/40-high-async-race-condition.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST execute all command handlers as async functions within a managed async event loop. The framework MUST reject synchronous command handlers at registration time (or emit a deprecation error). The framework MUST ensure that async operations within command handlers are fully awaited before the process exits. The framework MUST NOT call `process.exit()` (Node.js) or `sys.exit()` (Python) until all async command handlers and their registered cleanup hooks have resolved. Partial async execution that leads to silent data loss is a framework-level defect.

## Acceptance Criteria

- A command handler defined as a sync function produces a framework registration warning/error
- An async operation started but not awaited within a command handler is detected by the framework's async completion check
- `process.exit(0)` is called only after all async command teardown hooks have resolved
- A command that performs async I/O completes all writes before exiting

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When a command starts a long-running async job and returns immediately, `data.job` carries the job identifier and polling instructions.

---

## Wire Format

`tool <cmd>` → async job response (exit 0, job still in progress):

```json
{
  "ok": true,
  "data": {
    "job": {
      "job_id": "job-a1b2c3d4",
      "status_command": "tool jobs status --id job-a1b2c3d4",
      "poll_interval_ms": 2000
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 12 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework wraps all handlers in an async event loop and ensures cleanup hooks are awaited before exit.

```
# Command registration — async handler
async def deploy_handler(args):
    await upload_artifacts(args.target)
    await notify_slack(args.channel)

register command "deploy": handler=deploy_handler

# Framework guarantees:
# 1. handler is invoked inside managed async event loop
# 2. process.exit() is deferred until all awaited operations complete
# 3. cleanup hooks registered via framework.on_teardown() are awaited

# Sync handler — rejected at registration
def deploy_sync(args):
    ...
register command "deploy-sync": handler=deploy_sync
→ FrameworkWarning: synchronous command handlers are deprecated; use async def
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM handler must also await async teardown hooks before exit |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: child process cleanup is an async teardown operation awaited by this requirement |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Composes: `meta.duration_ms` measures wall time including async operations |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: async failures emit structured JSON error responses |
