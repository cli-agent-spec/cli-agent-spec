# REQ-C-010: Background-Process Commands Declare Metadata

**Tier:** Command Contract | **Priority:** P2

**Source:** [§17 Child Process Leakage](../challenges/02-critical-execution-and-reliability/17-medium-child-process-leakage.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

Any command that intentionally spawns a long-running background process MUST declare `spawns_background_process: true` in its registration metadata, and MUST declare `cleanup_command` (the framework command to stop the background process) and `max_lifetime_seconds` (after which the framework may kill it). The command MUST include `background_pid` and `cleanup_command` in its response `data`.

## Acceptance Criteria

- The `--schema` output for commands that spawn background processes includes `spawns_background_process: true`
- The response `data` includes `background_pid` (integer) and `cleanup_command` (string)
- The framework refuses to register a command that spawns a background process without declaring this metadata

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Background-process metadata is declared at registration and also appears in the response `data`.

```json
{
  "spawns_background_process": {
    "type": "boolean",
    "description": "True if the command intentionally starts a long-running child process that outlives the CLI invocation"
  },
  "cleanup_command": {
    "type": "string",
    "description": "Framework command to stop the background process"
  },
  "max_lifetime_seconds": {
    "type": "integer",
    "description": "Maximum seconds the background process should run before the framework may terminate it"
  }
}
```

---

## Wire Format

Schema output:

```bash
$ tool start-watcher --schema
```

```json
{
  "command": "start-watcher",
  "spawns_background_process": true,
  "cleanup_command": "tool stop-watcher",
  "max_lifetime_seconds": 3600
}
```

Runtime response:

```bash
$ tool start-watcher --dir /project
```

```json
{
  "ok": true,
  "data": {
    "background_pid": 5678,
    "cleanup_command": "tool stop-watcher --session 42",
    "pid_file": "/tmp/tool-session-42/children.pids"
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 18 }
}
```

---

## Example

A command that spawns a watcher declares all background-process metadata at registration. The framework uses this to set up session tracking and a maximum lifetime.

```
register command "start-watcher":
  danger_level: safe
  spawns_background_process: true
  cleanup_command: "stop-watcher"
  max_lifetime_seconds: 3600
  exit_codes:
    SUCCESS(0): description: "Watcher started", retryable: false, side_effects: complete

  execute(args):
    pid = spawn_watcher(args.dir)
    session = current_session_id()
    return response(
      background_pid=pid,
      cleanup_command="tool stop-watcher --session {}".format(session),
      pid_file="/tmp/tool-session-{}/children.pids".format(session)
    )
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Provides: framework session tracking that stores and manages declared child PIDs |
| [REQ-F-031](f-031-sigterm-forwarding-to-tracked-children.md) | F | Enforces: SIGTERM is forwarded to all background children tracked by the session |
| [REQ-O-027](o-027-tool-cleanup-built-in-command.md) | O | Consumes: `cleanup_command` declared here is invocable via `tool cleanup` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest exposes `spawns_background_process` and `cleanup_command` per command |
