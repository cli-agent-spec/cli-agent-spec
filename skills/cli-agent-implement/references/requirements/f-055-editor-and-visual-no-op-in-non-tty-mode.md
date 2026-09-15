# REQ-F-055: $EDITOR and $VISUAL No-Op in Non-TTY Mode

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§62 $EDITOR and $VISUAL Trap](../challenges/01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST set `EDITOR=true` and `VISUAL=true` (or equivalent no-op commands) in the environment of all spawned subprocesses when stdin/stdout are not a TTY. This prevents any subprocess from launching an interactive text editor. Additionally, if the framework detects that a command has invoked `$EDITOR` or `$VISUAL` in non-TTY mode (via the subprocess API), it MUST intercept the invocation, exit with code 4, and emit a structured error listing the non-interactive alternative flag (e.g., `--message`, `--from-file`).

## Acceptance Criteria

- In non-TTY mode, `git commit` invoked via the framework's subprocess API does not open vim
- A command that calls `os.environ['EDITOR']` to launch an editor exits with code 4 in non-TTY mode
- The exit 4 error includes `alternatives[]` listing non-interactive flags for the same operation
- In TTY mode, `$EDITOR` is unmodified and interactive editing works normally

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When an editor invocation is intercepted in non-TTY mode, the framework exits with code 4 (`PRECONDITION`) and emits a structured error with `code: "EDITOR_REQUIRED"` and an `alternatives[]` field.

---

## Wire Format

Editor invocation intercepted in non-TTY mode:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "EDITOR_REQUIRED",
    "message": "Command requires an interactive editor but stdin is not a TTY",
    "alternatives": [
      { "flag": "--message", "description": "Provide commit message inline" },
      { "flag": "--from-file", "description": "Read message from a file" }
    ],
    "hint": "Use --message or --from-file to avoid launching an editor",
    "phase": "execution"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 12 }
}
```

---

## Example

Framework-Automatic: no command author action needed for subprocess env injection. Commands that may open an editor MUST declare alternatives via REQ-C-023.

```
# Framework bootstrap in non-TTY mode — runs before spawning any subprocess:
env["EDITOR"] = "true"
env["VISUAL"] = "true"
env["GIT_EDITOR"] = "true"

# git commit in non-TTY mode — editor is a no-op (exit 0 immediately):
$ tool commit --message "fix: correct validation"  # → works
$ tool commit                                        # → EDITOR_REQUIRED in non-TTY
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-TTY detection that triggers this requirement's enforcement |
| [REQ-C-023](c-023-editor-requiring-commands-declare-non-interactive-.md) | C | Consumes: command declarations supply the `alternatives[]` list in the error |
| [REQ-F-044](f-044-shell-argument-escaping-enforcement.md) | F | Composes: subprocess spawning uses the same exec-array API that injects the env |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: the interception error uses the standard response envelope |
