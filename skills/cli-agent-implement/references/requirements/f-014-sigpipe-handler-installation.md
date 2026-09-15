# REQ-F-014: SIGPIPE Handler Installation

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§16 Signal Handling & Graceful Cancellation](../challenges/02-critical-execution-and-reliability/16-high-signal-handling.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST install a SIGPIPE handler that suppresses the default behavior (which raises an error or produces a traceback in some runtimes). When SIGPIPE is received, the command MUST exit silently and cleanly with exit code `0` (broken pipe is not an error — the consumer simply stopped reading). No stack trace or error message MUST be emitted.

## Acceptance Criteria

- `tool list-large | head -1` exits cleanly with no error output on stderr
- Exit code after SIGPIPE from a pipe consumer closing early is `0`
- No `BrokenPipeError` traceback appears on stderr

---

## Schema

No dedicated schema type — this requirement governs signal handler installation and process exit behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework sets SIGPIPE to `SIG_IGN` (or installs an equivalent handler) at startup, before any command is dispatched.

```
$ tool list-large | head -1
first-item
→ exit code: 0
→ stderr: (empty)

# Without this requirement:
$ tool list-large | head -1
first-item
BrokenPipeError: [Errno 32] Broken pipe
→ exit code: 1
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: both requirements together form the complete signal handling setup |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Provides: stdout/stderr stream separation that SIGPIPE handler must not violate |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `SUCCESS (0)` used as the exit code after SIGPIPE |
