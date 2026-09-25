# REQ-F-040: Absolute Path Output Enforcement

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§29 Working Directory Sensitivity](../challenges/05-high-environment-and-state/29-medium-working-directory.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST provide a path output type that commands declare for any field containing a filesystem path. When a command outputs a path using this type, the framework MUST automatically resolve it to an absolute path before serialization. The framework MUST document this behavior so command authors know to use the path type rather than raw strings for paths.

## Acceptance Criteria

- A command that returns `"./src/index.ts"` as a path field has it resolved to `"/project/src/index.ts"` in the output
- The resolved path is absolute regardless of the CWD from which the command was invoked
- A relative path returned through the path type is always expanded against the effective CWD at invocation time

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Path fields in `data` that use the framework's path output type are resolved to absolute paths before serialization. No new schema fields are added; the constraint applies to field values.

---

## Wire Format

Command invoked from `/project`:

```bash
$ cd /project && tool find-config --format json
```

```json
{
  "ok": true,
  "data": {
    "config_path": "/project/src/.toolrc",
    "output_dir": "/project/dist"
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 12, "cwd": "/project" }
}
```

---

## Example

Framework-Automatic: no command author action needed beyond using the framework's `PathField` type in the output schema declaration.

```
register command "find-config":
  output_schema:
    config_path: PathField   # framework resolves to absolute before serialization
    output_dir:  PathField   # framework resolves to absolute before serialization

# Even if command returns "./src/.toolrc", framework outputs "/project/src/.toolrc"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-027](f-027-cwd-in-response-meta.md) | F | Composes: `meta.cwd` records the base against which relative paths are resolved |
| [REQ-F-041](f-041-process-cwd-immutability.md) | F | Enforces: immutable CWD ensures path resolution is deterministic |
| [REQ-O-017](o-017-cwd-root-flag.md) | O | Extends: `--cwd` changes the base used for path resolution |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Consumes: commands declare path fields using the framework's `PathField` type |
