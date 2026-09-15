# REQ-C-017: Commands Register cleanup() Hook

**Tier:** Command Contract | **Priority:** P1

**Source:** [§16 Signal Handling & Graceful Cancellation](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Every command that acquires resources (locks, temp files, network connections, child processes) MUST register a `cleanup()` hook with the framework. The framework invokes this hook on normal exit, SIGTERM, and timeout. The `cleanup()` hook MUST be idempotent (safe to call multiple times). Command authors MUST use the framework's resource acquisition APIs, which automatically register cleanup handlers.

## Acceptance Criteria

- A command that acquires a lock has the lock released on normal exit, SIGTERM, and timeout
- A `cleanup()` hook called twice produces the same end state as calling it once
- A command that does not acquire any resources MAY register a no-op cleanup hook
- The framework warns at development time if a command acquires a tracked resource without a cleanup hook

---

## Schema

No dedicated schema type — this requirement governs cleanup hook registration behavior without adding new wire-format fields

---

## Wire Format

Cleanup hook declarations appear in the command's registration metadata. No additional `--schema` fields are exposed, but the `side_effects` field in `exit_codes` reflects whether cleanup has been completed:

```bash
$ tool deploy --schema
```
```json
{
  "exit_codes": {
    "0":  { "name": "SUCCESS", "description": "Deployment completed and all resources released", "retryable": false, "side_effects": "complete" },
    "10": { "name": "TIMEOUT", "description": "Deployment timed out — cleanup attempted",        "retryable": false, "side_effects": "partial"  }
  }
}
```

---

## Example

Command authors register cleanup hooks via the framework's resource acquisition APIs:

```
register command "deploy":
  on_execute: |
    lock = framework.acquire_lock("deploy-lock")
    # framework automatically registers: cleanup() { lock.release() }

    tmp = framework.temp_file("deploy-payload")
    # framework automatically registers: cleanup() { tmp.delete() }

    child = framework.subprocess("kubectl apply ...")
    # framework automatically registers: cleanup() { child.terminate() }

    # cleanup() is called on: normal exit, SIGTERM, timeout
    # cleanup() is idempotent: safe to call multiple times
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Enforces: SIGTERM handler invokes registered `cleanup()` hooks |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Enforces: timeout handler invokes registered `cleanup()` hooks before exiting |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: child process tracking is one category of resource that `cleanup()` must release |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Composes: temp files are framework-tracked resources cleaned up via the hook mechanism |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `side_effects` in exit code declarations reflects whether cleanup was completed |
