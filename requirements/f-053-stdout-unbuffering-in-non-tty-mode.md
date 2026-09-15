# REQ-F-053: Stdout Unbuffering in Non-TTY Mode

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§60 OS Output Buffer Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST disable OS-level stdout buffering when stdout is not a TTY. In Python this means calling `sys.stdout.reconfigure(line_buffering=True)` and setting `PYTHONUNBUFFERED=1` before any output. In Node.js this means calling `process.stdout.cork()` / `uncork()` appropriately or using unbuffered streams. This MUST be performed in the framework's bootstrap, before any command code runs. For long-running commands (>5s), the framework MUST additionally emit a JSON heartbeat object to stdout every configurable interval (default: 10000ms) via the `--heartbeat-ms` flag (REQ-O-038).

## Acceptance Criteria

- A command that emits one log line per second is received by the agent one line at a time, not in a single flush after the process exits
- `PYTHONUNBUFFERED=1` is set in the process environment before the first `output()` call
- A 30-second command with heartbeats enabled emits at least 2 heartbeat JSON objects to stdout before completing
- Heartbeat objects are valid JSON matching `{"status": "running", "heartbeat": true, "elapsed_ms": N}`

---

## Schema

No dedicated schema type — this requirement governs OS-level buffering behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only. The effect is observable: output bytes reach the caller immediately as emitted rather than in a single post-exit flush.

Heartbeat lines (emitted via REQ-O-038) are JSON objects on stdout when enabled:

```json
{"status": "running", "heartbeat": true, "elapsed_ms": 10012}
{"status": "running", "heartbeat": true, "elapsed_ms": 20031}
{"ok": true, "data": {"result": "done"}, "error": null, "warnings": [], "meta": { "exit_code": 0,"duration_ms": 22418}}
```

---

## Example

Framework-Automatic: no command author action needed. The framework calls `sys.stdout.reconfigure(line_buffering=True)` (Python) or equivalent at bootstrap, before any command runs.

```
# Framework bootstrap — runs before any command code:
export PYTHONUNBUFFERED=1
sys.stdout.reconfigure(line_buffering=True)

# Command output is flushed immediately; no block-buffering on pipes
$ tool long-job --output json | python -c "import sys; print(sys.stdin.readline())"
# → first JSON line received without waiting for process exit
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: all command output flows through the framework's output stream |
| [REQ-F-049](f-049-async-command-handler-enforcement.md) | F | Composes: async commands rely on unbuffered stdout for heartbeat delivery |
| [REQ-O-038](o-038-heartbeat-ms-flag-for-long-running-commands.md) | O | Extends: heartbeat-ms opt-in sends periodic JSON lines via unbuffered stdout |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Composes: the final flushed output is a response envelope |
