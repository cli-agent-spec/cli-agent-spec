# REQ-F-043: Temp File Session-Scoped Auto-Cleanup

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Medium

---

## Description

The framework MUST automatically clean up the session-scoped temp directory (REQ-F-032) on normal command exit. For commands that produce output files intended for the caller to consume, the framework MUST include a `cleanup` object in the response containing `command` (the exact shell command to delete the file) and `auto_cleanup_after_seconds` (time after which the framework will delete the file if cleanup was not called). Background cleanup MUST NOT be implemented via a daemon; instead it MUST occur on next framework invocation.

The framework MUST create all temp files and directories with restrictive permissions: mode `0600` for files, mode `0700` for directories. World-readable temp files containing credentials, tokens, or intermediate command output are a credential exposure vector on shared systems.

## Acceptance Criteria

- After a command exits normally, its session temp directory no longer exists
- A response that includes a caller-facing output file includes a `cleanup` object
- `cleanup.command` is a valid, directly executable shell command
- Files older than `auto_cleanup_after_seconds` are pruned when any framework command next runs
- All temp files are created with mode `0600` (verified with `stat` or equivalent)
- All temp directories are created with mode `0700`
- `umask` does not widen permissions — framework uses explicit mode arguments, not umask-relative defaults

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The `meta` object carries `session_tmp_dir` when a command produces caller-facing output files. A `cleanup` object in `data` describes how the caller should remove those files.

---

## Wire Format

`tool <cmd>` → response envelope with `meta.session_tmp_dir` and `data.cleanup`:

```json
{
  "ok": true,
  "data": {
    "output_file": "/tmp/mycli/session-a1b2c3/report.json",
    "cleanup": {
      "command": "rm -f /tmp/mycli/session-a1b2c3/report.json",
      "auto_cleanup_after_seconds": 300
    }
  },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "session_tmp_dir": "/tmp/mycli/session-a1b2c3"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework creates and registers the session temp directory, injects `meta.session_tmp_dir`, and deletes it on exit.

```
# Framework bootstrap (transparent to command author)
session_tmp_dir = mkdtemp("/tmp/mycli/session-{run_id}")
atexit.register(shutil.rmtree, session_tmp_dir)

# On command exit:
→ /tmp/mycli/session-a1b2c3/ removed automatically

# On next framework invocation, stale dirs older than auto_cleanup_after_seconds
# that were not cleaned (e.g. after kill -9) are pruned:
→ /tmp/mycli/session-old123/ removed (age > 300 s)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Provides: session-scoped temp directory that this requirement cleans up |
| [REQ-F-042](f-042-log-rotation-in-framework-logger.md) | F | Composes: log rotation similarly bounds disk usage from framework-managed files |
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | F | Composes: SIGTERM handler triggers cleanup of session temp dir on signal exit |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `session_tmp_dir` appears in `meta`, not `data` |
