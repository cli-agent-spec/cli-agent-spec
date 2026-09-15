# REQ-O-026: tool doctor Built-In Command

**Tier:** Opt-In | **Priority:** P1

**Source:** [§20 Environment & Dependency Discovery](../challenges/06-high-errors-and-discoverability/20-medium-dependency-discovery.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide a built-in `tool doctor` command that runs all registered `preflight()` hooks and reports results. Each check MUST include: `name`, `ok` (boolean), `version` found (if applicable), `required` version (if applicable), `error` message (if failed), and `fix` (exact shell command to resolve the issue). The command MUST exit `0` if all checks pass, exit `1` if any check fails. The `doctor` command MUST also test network connectivity and proxy settings for all registered network endpoints.

## Acceptance Criteria

- `tool doctor --output json` returns a structured JSON object with a `checks` array
- Each failed check includes a `fix` field with an executable shell command
- A missing required dependency appears as a failed check with `ok: false`
- `tool doctor` exit code is `0` iff all checks pass; otherwise it exits `4` (`PRECONDITION`) with `error.code: "DOCTOR_CHECKS_FAILED"` and the full report in `data`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.checks` is an array of check result objects with `name`, `ok`, `version`, `required`, `error`, and `fix` fields.

---

## Wire Format

```bash
$ tool doctor --output json
```

```json
{
  "ok": false,
  "data": {
    "checks": [
      { "name": "node", "ok": true, "version": "20.11.0", "required": ">=18.0.0" },
      { "name": "aws-cli", "ok": false, "version": null, "required": ">=2.0.0", "error": "not found in PATH", "fix": "brew install awscli" }
    ]
  },
  "error": {
    "code": "DOCTOR_CHECKS_FAILED",
    "message": "1 of 2 environment checks failed",
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
    - check_network("https://api.example.com/health")

$ tool doctor --output json
→ data.checks: [{...ok...}, {...failed with fix...}]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-031](o-031-dependency-version-matrix-declaration.md) | O | Provides: declared dependency constraints that `tool doctor` checks |
| [REQ-F-036](f-036-http-client-proxy-environment-variable-compliance.md) | F | Composes: proxy settings are tested as part of network connectivity checks |
| [REQ-F-037](f-037-network-error-context-block.md) | F | Composes: failed network checks use the network error context block |
