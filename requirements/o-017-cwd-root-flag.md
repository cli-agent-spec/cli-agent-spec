# REQ-O-017: --cwd / --root Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§29 Working Directory Sensitivity](../challenges/05-high-environment-and-state/29-medium-working-directory.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST provide `--cwd <path>` as a standard flag on all commands that interact with the filesystem. When `--cwd` is passed, the framework resolves all relative paths against the given path instead of the process CWD. The framework MUST validate that the path exists and is a directory before execution (exit `2` if not). The effective CWD used MUST be recorded in `meta.cwd`.

## Acceptance Criteria

- `--cwd /project` causes all relative path resolution to be based on `/project`
- `meta.cwd` reflects the value of `--cwd` when passed
- A non-existent `--cwd` path causes exit `2` with a validation error before any side effects
- `--cwd` does not change the process's actual working directory (REQ-F-041)

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.cwd` reflects the effective working directory used for path resolution — either the value of `--cwd` or the process's actual CWD.

---

## Wire Format

```bash
$ tool lint --cwd /project --format json
```

```json
{
  "ok": true,
  "data": {
    "issues": [],
    "checked_paths": ["/project/src/index.ts", "/project/src/utils.ts"]
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "cwd": "/project", "duration_ms": 312 }
}
```

Non-existent `--cwd` value:

```json
{
  "ok": false,
  "data": null,
  "error": { "code": "ARG_ERROR", "message": "--cwd path does not exist: /nonexistent" },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 12, "phase": "validation" }
}
```

---

## Example

Opt-in at the framework level; automatically available on filesystem-interacting commands.

```
app = Framework("tool")
app.enable_cwd_flag()   # registers --cwd on all commands with filesystem I/O

# Agent specifies absolute path to avoid CWD sensitivity:
$ tool lint --cwd /project/src --format json
→ meta.cwd: "/project/src"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-027](f-027-cwd-in-response-meta.md) | F | Provides: `meta.cwd` field that reflects the effective CWD |
| [REQ-F-041](f-041-process-cwd-immutability.md) | F | Enforces: `--cwd` does not change the process's actual working directory |
| [REQ-F-040](f-040-absolute-path-output-enforcement.md) | F | Composes: output paths are resolved against the effective `--cwd` value |
