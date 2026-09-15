# REQ-O-031: Dependency Version Matrix Declaration

**Tier:** Opt-In | **Priority:** P1

**Source:** [§38 Runtime Dependency Version Mismatch](../challenges/01-critical-ecosystem-runtime-agent-specific/38-high-dependency-version-mismatch.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST provide a mechanism for declaring all required runtime dependencies (external binaries, runtimes, and system libraries) with their minimum and maximum compatible version constraints. Each declared dependency MUST include: `name`, `check_command` (exact shell command to verify presence), `version_regex` (regex to extract the version string from check_command output), `min_version`, `max_version` (optional), and `fix_command` (exact shell command to install or upgrade). These declarations are automatically consumed by `tool doctor` (REQ-O-026) and emitted in `--schema` output.

## Acceptance Criteria

- A declared dependency with a version below `min_version` appears as a failed check in `tool doctor`
- A declared dependency with a version above `max_version` appears as a compatibility warning in `tool doctor`
- `tool doctor --output json` includes a `dependencies` array with all declared dependencies and their check results
- The `fix_command` for each failed dependency is an executable shell command

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Declared dependencies appear in the manifest's `dependencies` field and in `tool doctor` output.

---

## Wire Format

`tool doctor --output json` (dependencies section):

```json
{
  "ok": false,
  "data": {
    "checks": [],
    "dependencies": [
      { "name": "node", "check_command": "node --version", "version_regex": "v(\\d+\\.\\d+)", "min_version": "18.0.0", "found_version": "20.11.0", "ok": true },
      { "name": "terraform", "check_command": "terraform version", "version_regex": "Terraform v(\\d+\\.\\d+)", "min_version": "1.5.0", "found_version": null, "ok": false, "fix_command": "brew install terraform" }
    ]
  },
  "error": {
    "code": "DOCTOR_CHECKS_FAILED",
    "message": "1 of 2 declared dependencies failed",
    "retryable": false,
    "fix_required": "Apply the fix listed for each failed check in data.dependencies"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 412 }
}
```

---

## Example

Opt-in: the framework provides a `declare_dependency()` registration API.

```
app = Framework("tool")

app.declare_dependency(
  name="terraform",
  check_command="terraform version",
  version_regex=r"Terraform v(\d+\.\d+)",
  min_version="1.5.0",
  fix_command="brew install terraform",
)

# Dependency checks run automatically in tool doctor:
$ tool doctor
→ FAIL terraform: not found (fix: brew install terraform)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-026](o-026-tool-doctor-built-in-command.md) | O | Consumes: declared dependencies as checks run by `tool doctor` |
| [REQ-C-018](c-018-commands-declare-platform-requirements.md) | C | Composes: per-command platform requirements augment the global dependency matrix |
