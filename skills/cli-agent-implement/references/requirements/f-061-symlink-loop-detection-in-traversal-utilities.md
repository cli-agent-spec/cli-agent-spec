# REQ-F-061: Symlink Loop Detection in Traversal Utilities

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§66 Symlink Loop and Recursive Traversal Exhaustion](../challenges/01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Critical / Context: Low

---

## Description

The framework's filesystem traversal utilities (used by commands that copy, delete, archive, or search recursively) MUST track visited directory inodes and exit with a structured error immediately upon detecting a revisited inode (circular symlink). The framework MUST additionally enforce a maximum traversal depth (default: 50, configurable via `--max-depth`). Both checks MUST apply to the framework's built-in traversal API; commands using the framework's API get this protection automatically.

## Acceptance Criteria

- A recursive delete on a directory containing a circular symlink exits with code 4 and `error.code: "SYMLINK_LOOP"` before exhausting memory
- The error includes `path` (where the loop was detected) and `loop_target` (the directory it points back to)
- `--max-depth 10` limits traversal to 10 directory levels
- A directory without circular symlinks traverses normally to full depth

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

The framework emits a `PRECONDITION (4)` error response with `error.code: "SYMLINK_LOOP"` and structured fields for the detected loop.

---

## Wire Format

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "SYMLINK_LOOP",
    "message": "Circular symlink detected during traversal",
    "retryable": false,
    "phase": "execution",
    "path": "/project/a/b/link",
    "loop_target": "/project/a",
    "completed_count": 142
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 80 }
}
```

---

## Example

Framework-Automatic: no command author action needed. Commands using the framework's traversal API get loop detection automatically.

```
# Directory tree contains a → b → c → a symlink loop
$ mytool archive /project --json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "SYMLINK_LOOP",
    "message": "Circular symlink detected during traversal",
    "retryable": false,
    "phase": "execution",
    "path": "/project/c/link_back",
    "loop_target": "/project/a",
    "completed_count": 142
  },
  ...
}
→ exits 4 before exhausting memory; agent knows where the loop is
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` shape for the `SYMLINK_LOOP` error |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `PRECONDITION (4)` exit code used for symlink loop errors |
| [REQ-F-040](f-040-absolute-path-output-enforcement.md) | F | Composes: `path` and `loop_target` fields in the error are always absolute paths |
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Composes: max-depth and timeout together bound traversal resource use |
