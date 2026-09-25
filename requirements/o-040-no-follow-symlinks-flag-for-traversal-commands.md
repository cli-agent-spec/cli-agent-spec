# REQ-O-040: --no-follow-symlinks Flag for Traversal Commands

**Tier:** Opt-In | **Priority:** P1

**Source:** [§66 Symlink Loop and Recursive Traversal Exhaustion](../challenges/01-critical-ecosystem-runtime-agent-specific/66-high-symlink-loop.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Critical / Context: Low

---

## Description

The framework MUST auto-register `--no-follow-symlinks` and `--max-depth <n>` (default: 50) for all commands declared with `recursive_traversal: true`. When `--no-follow-symlinks` is passed, the framework's traversal utility skips all symlinks, preventing loop detection from being needed. When `--max-depth` is exceeded, the command exits with code 4 and a structured error listing the depth limit and suggesting `--max-depth` adjustment.

## Acceptance Criteria

- `tool delete --recursive --no-follow-symlinks /tmp/a` skips symlinks and completes without following circular references
- `tool delete --recursive --max-depth 3 /deep/tree` exits 4 with `DEPTH_EXCEEDED` if the tree is deeper than 3 levels
- Without `--no-follow-symlinks`, the inode tracking from REQ-F-061 provides the loop protection
- `--schema` for recursive commands lists `no-follow-symlinks` and `max-depth` flags

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When `--max-depth` is exceeded, the error uses `code: "DEPTH_EXCEEDED"` with `max_depth` and `path` context. When `--no-follow-symlinks` is in effect, no `SYMLINK_LOOP` error can occur.

---

## Wire Format

```bash
$ tool delete --recursive --no-follow-symlinks /tmp/a --format json
```

```json
{
  "ok": true,
  "data": { "deleted_count": 42, "symlinks_skipped": 3 },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 18 }
}
```

`--max-depth` exceeded:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "DEPTH_EXCEEDED",
    "message": "Traversal depth limit of 50 exceeded at /deep/a/b/c/.../z",
    "max_depth": 50,
    "path": "/deep/a/b/c/.../z",
    "hint": "Use --max-depth to adjust the limit"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 12 }
}
```

---

## Example

Opt-in: automatically registered for commands that declare `recursive_traversal: true`.

```
register command "delete":
  recursive_traversal: true
  # --no-follow-symlinks and --max-depth are auto-registered

# Agent always passes --no-follow-symlinks for safety:
$ tool delete --recursive --no-follow-symlinks /target/path
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-061](f-061-symlink-loop-detection-in-traversal-utilities.md) | F | Provides: inode-based loop detection when `--no-follow-symlinks` is not used |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Composes: `recursive_traversal: true` is declared alongside other filesystem side effects |
