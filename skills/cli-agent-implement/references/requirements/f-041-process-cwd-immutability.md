# REQ-F-041: Process CWD Immutability

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§29 Working Directory Sensitivity](../challenges/05-high-environment-and-state/29-medium-working-directory.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: Low

---

## Description

The framework MUST prohibit commands from changing the process working directory (`os.chdir()` or equivalent) during execution. If a command's implementation requires operating in a different directory, it MUST do so by constructing absolute paths, not by changing the process CWD. The framework SHOULD detect and warn at registration time if a command registers a hook that calls `chdir`.

## Acceptance Criteria

- The process CWD after any command invocation is identical to the CWD before invocation.
- A command that internally calls `os.chdir()` is flagged by the framework's linter/registration check.
- Operations on files in other directories work correctly using absolute paths constructed from `--cwd` (REQ-O-017)

---

## Schema

No dedicated schema type — this requirement governs process CWD immutability without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework detects `chdir` calls at registration and raises an error.

```
# Rejected at registration — chdir not permitted
def handler(args):
    os.chdir(args.target_dir)
    ...
→ FrameworkError: commands must not call chdir(); construct absolute paths instead

# Correct — absolute path construction
def handler(args):
    target = os.path.join(args.cwd, args.target_dir)
    ...
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-027](f-027-cwd-in-response-meta.md) | F | Provides: `meta.cwd` records the process CWD at invocation time |
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Composes: config resolution uses absolute paths, not CWD-relative paths |
| [REQ-O-017](o-017-cwd-root-flag.md) | O | Extends: `--cwd` flag supplies the working directory as an explicit argument |
