# REQ-O-026: tool doctor Built-In Command

**Tier:** Opt-In | **Priority:** P1

**Source:** [§20 Environment & Dependency Discovery](../challenges/06-high-errors-and-discoverability/20-medium-dependency-discovery.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide a built-in `tool doctor` command that runs all registered `preflight()` hooks and reports results. Each check MUST include: `name`, `ok` (boolean), `version` found (if applicable), `required` version (if applicable), `error` message (if failed), and `fix` (exact shell command to resolve the issue). The command MUST exit `0` if all checks pass, and exit `4` (`PRECONDITION`) with `error.code: "DOCTOR_CHECKS_FAILED"` if any check fails. The `doctor` command MUST also test network connectivity and proxy settings for all registered network endpoints. For each command's `required_tools` (REQ-C-018), a minimum version is checked against the version found; a `"*"` value means any version, so `doctor` checks only that the program resolves on `PATH`, MUST NOT run it, and reports `required: "*"` with no `version`. A declared dependency (REQ-O-031) follows the same rule through its own `check_command`: a `min_version` of `"*"` means any version, so `doctor` runs `check_command` and passes when it exits `0`, skipping `version_regex` and the version comparison, and reports `min_version: "*"` with no `found_version` in `data.dependencies`. Either way `"*"` is a presence check: `PATH` lookup for a `required_tools` entry, which declares no command, and the declared `check_command` for a dependency.

## Acceptance Criteria

- `tool doctor --format json` returns a structured JSON object with a `checks` array
- Each failed check includes a `fix` field with an executable shell command
- A missing required dependency appears as a failed check with `ok: false`
- A `required_tools` entry declared as `"*"` passes when the program resolves on `PATH`, without `doctor` running it, and its check carries `required: "*"` and no `version`
- A declared dependency with `min_version: "*"` passes when its `check_command` exits `0`, with no `version_regex` or version comparison, and is reported with `min_version: "*"` and no `found_version`
- `tool doctor` exit code is `0` iff all checks pass; otherwise it exits `4` (`PRECONDITION`) with `error.code: "DOCTOR_CHECKS_FAILED"` and the full report in `data`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.checks` is an array of check result objects with `name`, `ok`, `version`, `required`, `error`, and `fix` fields.

---

## Wire Format

```bash
$ tool doctor --format json
```

```json
{
  "ok": false,
  "data": {
    "checks": [
      { "name": "node", "ok": true, "version": "20.11.0", "required": ">=18.0.0" },
      { "name": "bean-format", "ok": true, "required": "*" },
      { "name": "aws-cli", "ok": false, "version": null, "required": ">=2.0.0", "error": "not found in PATH", "fix": "brew install awscli" }
    ]
  },
  "error": {
    "code": "DOCTOR_CHECKS_FAILED",
    "message": "1 of 3 environment checks failed",
    "retryable": false,
    "fix_required": "Apply the fix listed for each failed check in data.checks"
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 412 }
}
```

---

## Example

Opt-in at the framework level; command authors register preflight hooks.

```
app = Framework("tool")
app.enable_doctor()

register command "deploy":
  preflight:
    - check_binary("aws", min_version="2.0.0", fix="brew install awscli")
    - check_binary("bean-format", min_version="*", fix="pip install beancount")   # PATH lookup only, never run
    - check_network("https://api.example.com/health")

$ tool doctor --format json
→ data.checks: [{...ok...}, {...failed with fix...}]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-031](o-031-dependency-version-matrix-declaration.md) | O | Provides: declared dependency constraints that `tool doctor` checks, where `"*"` means `check_command` exits `0` |
| [REQ-C-018](c-018-commands-declare-platform-requirements.md) | C | Provides: each command's `required_tools`, where `"*"` means a `PATH` check only |
| [REQ-F-036](f-036-http-client-proxy-environment-variable-compliance.md) | F | Composes: proxy settings are tested as part of network connectivity checks |
| [REQ-F-037](f-037-network-error-context-block.md) | F | Composes: failed network checks use the network error context block |
