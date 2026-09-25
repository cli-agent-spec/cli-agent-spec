# REQ-O-006: Stdin as ID Source (-)

**Tier:** Opt-In | **Priority:** P3

**Source:** [§6 Command Composition & Piping](../challenges/04-critical-output-and-parsing/06-medium-command-composition.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST support the convention that any argument accepting an identifier value also accepts `-` to mean "read the value from stdin". Command authors declare arguments as `pipe_compatible: true`; the framework handles stdin reading transparently. This enables shell composition: `tool get-user --name Alice --format id | tool delete-user --id -`.

## Acceptance Criteria

- `echo 42 | tool delete-user --id -` is equivalent to `tool delete-user --id 42`
- Reading from `-` works when stdin is a pipe and when stdin is a file redirect
- An error is raised if `-` is passed but stdin has no data (empty stdin)

---

## Schema

No dedicated schema type — this requirement governs argument reading behavior. The value read from stdin is treated identically to a value provided on the command line.

---

## Wire Format

```bash
$ tool list-users --format id | tool delete-user --id -
```

```json
{
  "ok": true,
  "data": { "deleted_count": 3 },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 120 }
}
```

Empty stdin error:

```bash
$ echo -n | tool delete-user --id -
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "EMPTY_STDIN",
    "message": "Expected id from stdin but stdin was empty",
    "retryable": false,
    "phase": "validation"
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 2 }
}
```

---

## Example

Command authors declare pipe-compatible arguments at registration time. The framework handles stdin reading transparently.

```
app = Framework("tool")
app.enable_stdin_pipe()

register command "delete-user":
  args:
    id: { type: string, pipe_compatible: true }

# tool get-user --name alice --format id | tool delete-user --id -
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-005](o-005-output-id-extraction-mode.md) | O | Provides: `--format id` produces the single-id lines consumed here |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: empty stdin raises `ARG_ERROR` with `phase: "validation"` |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Provides: stdout/stderr separation required for clean pipe composition |
