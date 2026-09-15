# REQ-F-032: Session-Scoped Temp Directory

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§15 Race Conditions & Concurrency](../challenges/02-critical-execution-and-reliability/15-high-race-conditions.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide each command invocation with a unique, session-scoped temporary directory. All temp files created by the command through the framework's file API MUST be placed within this directory. The directory path MUST incorporate a session or run identifier. The framework MUST clean up this directory on normal exit and on SIGTERM.

## Acceptance Criteria

- Two parallel invocations of the same command never write to the same temp file path
- After a command exits (normally or via signal), its session temp directory is removed
- The temp directory path is exposed to the command as an environment variable or framework API call

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.session_tmp_dir` is a framework-injected extension to `ResponseMeta`

---

## Wire Format

`meta` in the response envelope:

```json
{
  "ok": true,
  "data": { "output_file": "/project/dist/bundle.js" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 3102,
    "request_id": "req_01HZ",
    "session_tmp_dir": "/tmp/mytool/req_01HZ"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework creates a unique session temp directory before dispatching the command and removes it on exit or SIGTERM.

```
$ tool build --target all &   (PID 9001, request req_01HZ)
→ session_tmp_dir: /tmp/mytool/req_01HZ  (created)

$ tool build --target all &   (PID 9002, request req_01HC)
→ session_tmp_dir: /tmp/mytool/req_01HC  (different directory — no collision)

$ wait 9001
→ /tmp/mytool/req_01HZ removed on normal exit

$ kill -TERM 9002
→ /tmp/mytool/req_01HC removed by SIGTERM cleanup handler
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: session PID file is stored inside the temp directory created here |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM handler cleans up the session temp directory created here |
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | F | Specializes: all temp files created via the framework API are placed in this directory |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries `meta.session_tmp_dir` |
