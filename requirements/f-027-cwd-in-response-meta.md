# REQ-F-027: CWD in Response Meta

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§29 Working Directory Sensitivity](../challenges/05-high-environment-and-state/29-medium-working-directory.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST automatically inject `meta.cwd` (the process working directory at the time of invocation) into every response. For commands that discover a project root (walking up the directory tree), the framework MUST also inject `meta.project_root` when the command declares a root-resolution behavior.

## Acceptance Criteria

- Every response includes `meta.cwd` as an absolute path string
- `meta.cwd` matches the result of `pwd` in the shell that invoked the command
- Commands that resolve a project root include `meta.project_root` as an absolute path

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.cwd` and `meta.project_root` are framework-injected extensions to `ResponseMeta`

---

## Wire Format

`meta` in the response envelope:

```json
{
  "ok": true,
  "data": { "files": ["src/index.ts"] },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 38,
    "request_id": "req_01HZ",
    "cwd": "/home/user/myproject/packages/core",
    "project_root": "/home/user/myproject"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework captures `os.getcwd()` (or equivalent) immediately at dispatch time and injects it into `meta.cwd` on every response.

```
$ cd /home/user/myproject/packages/core
$ tool lint --json
→ meta.cwd: "/home/user/myproject/packages/core"
→ meta.project_root: "/home/user/myproject"   (if command declared root-resolution)

$ cd /tmp
$ tool lint --json
→ meta.cwd: "/tmp"
→ meta.project_root: absent                   (no .git or package.json found)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-040](f-040-absolute-path-output-enforcement.md) | F | Composes: absolute paths in `data` are resolved against `meta.cwd` captured here |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries `meta.cwd` |
| [REQ-F-041](f-041-process-cwd-immutability.md) | F | Enforces: `meta.cwd` is stable because the framework prevents `chdir()` during execution |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Provides: `meta` separation that keeps `cwd` out of `data` |
