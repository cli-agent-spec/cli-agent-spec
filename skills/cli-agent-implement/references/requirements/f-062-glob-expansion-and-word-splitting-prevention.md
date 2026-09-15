# REQ-F-062: Glob Expansion and Word-Splitting Prevention

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§51 Shell Word Splitting and Glob Expansion Interference](../challenges/01-critical-ecosystem-runtime-agent-specific/51-high-glob-expansion.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework's subprocess API MUST always invoke external processes using array-form argument lists, never via shell string interpolation. The framework MUST raise a registration error if a command handler passes a shell-string (single joined string) to the subprocess API instead of an argument array. This prevents the shell from performing word-splitting on arguments containing spaces and glob expansion on arguments containing `*`, `?`, or `[`. When the framework logs subprocess invocations (in debug mode), it MUST display the array form to make quoting visible.

## Acceptance Criteria

- An argument containing spaces (e.g., `"hello world"`) is received by the subprocess as a single argument, not split into two
- An argument containing `*` (e.g., `"*.json"`) is passed literally to the subprocess, not expanded by the shell
- Passing a shell-string to the subprocess API raises a framework `SHELL_STRING_PROHIBITED` error at registration time
- In debug mode, subprocess invocations are logged as JSON arrays: `["git", "commit", "-m", "hello world"]`

---

## Schema

No dedicated schema type — this requirement governs subprocess invocation behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework's exec API only accepts argument arrays; shell-string invocations are rejected at registration time.

```
# Correct — array form
framework.exec(["git", "commit", "-m", "hello world"])
→ git receives one argument: "hello world"

# Rejected — shell string
framework.exec("git commit -m hello world")
→ FrameworkError: SHELL_STRING_PROHIBITED — pass an argument array, not a shell string

# Argument with glob — passed literally
framework.exec(["find", ".", "-name", "*.json"])
→ find receives literal "*.json"; shell does not expand it
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-044](f-044-shell-argument-escaping-enforcement.md) | F | Composes: argument escaping enforcement complements array-form prevention |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: child process tracking applies to all subprocesses spawned via the array API |
| [REQ-F-065](f-065-pipeline-exit-code-propagation.md) | F | Composes: pipeline exit propagation depends on the framework controlling subprocess invocation |
| [REQ-F-066](f-066-subprocess-locale-normalization.md) | F | Composes: locale normalization is injected into the same subprocess environment |
