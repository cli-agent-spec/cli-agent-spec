# REQ-C-030: Error Responses Include Executable fix_command

**Tier:** Command Contract | **Priority:** P1

**Source:** [§18 Error Message Quality](../challenges/06-high-errors-and-discoverability/18-high-error-quality.md) · [§19 Retry Hints in Error Responses](../challenges/06-high-errors-and-discoverability/19-high-retry-hints.md) · [§53 Credential Expiry Mid-Session](../challenges/01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: High

---

## Description

When a failure is caller-correctable (`retryable: false` with `fix_required` present) and the correction is achievable by running a single command, the error response MUST include `error.fix_command`: the exact, complete invocation that resolves the `fix_required` condition. The field exists because prose suggestions require the caller to synthesize a command; an agent that can only copy a string and compare a boolean can still recover when the command is given verbatim.

`fix_command` values are declared per error code in the command's error registry at registration time. The framework MUST enforce the safety constraints below at registration, not at runtime:

- **Verbatim-executable**: no placeholders (`<your-token>`, `$PROJECT_ID`), no editing required. If the remediation needs caller-specific input, omit `fix_command` and state the condition in `fix_required` instead
- **Safe by construction**: read-only or idempotent; running it twice is harmless
- **Never destructive**: the framework MUST reject a `fix_command` whose target command is declared `danger_level: "destructive"` (REQ-C-002)
- **Self-contained**: invokes the same tool or a declared companion; never a shell pipeline, never interpolated external data

Existing specialized fields are instances of this pattern: `error.refresh_command` (REQ-F-063) and `error.reauth_command` (§53) carry auth remediation; `fix_command` in `tool doctor` checks (REQ-O-031) carries dependency remediation. Generic agent consumers read `error.fix_command`; commands SHOULD emit it alongside any specialized variant.

## Acceptance Criteria

- A caller-correctable error whose remediation is a single safe command includes `error.fix_command`
- `error.fix_command` runs successfully as-is, with no edits, in the environment that produced the error
- Running `error.fix_command` twice in a row produces no additional side effects
- Registering a `fix_command` that invokes a command declared `danger_level: "destructive"` raises a framework error
- Registering a `fix_command` containing `<`, `>`, or `$`-placeholder patterns raises a framework error
- After `error.fix_command` exits `0`, reissuing the original invocation does not fail with the same `error.code`
- When no safe single-command remediation exists, `fix_command` is absent and `fix_required` carries the condition as prose

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

This requirement extends `ResponseEnvelope.ErrorDetail` with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.fix_command` | string | when the remediation is a single safe command | Exact invocation resolving `fix_required`; verbatim-executable, read-only or idempotent, never destructive |

---

## Wire Format

Expired credentials (remediation is a safe command):

```bash
$ tool deploy --target prod
```
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "CREDENTIALS_EXPIRED",
    "message": "Access token expired at 2026-07-01T00:00:00Z",
    "retryable": false,
    "fix_required": "Refresh credentials, then reissue",
    "fix_command": "tool auth refresh"
  },
  "warnings": [],
  "meta": { "duration_ms": 120 }
}
```

Validation error (remediation needs caller input, so `fix_command` is absent):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_ENVIRONMENT",
    "message": "Unknown target 'prodution'",
    "retryable": false,
    "fix_required": "Correct the target environment argument",
    "phase": "validation",
    "suggestion": "Valid values: prod, staging, dev"
  },
  "warnings": [],
  "meta": { "duration_ms": 3 }
}
```

---

## Example

The command author declares remediation per error code in the error registry; the framework validates safety at registration:

```
register command "deploy":
  error_registry:
    CREDENTIALS_EXPIRED: fix_required: "Refresh credentials, then reissue",
                         fix_command:  "tool auth refresh"
    CONFIG_MISSING:      fix_required: "Initialize project config",
                         fix_command:  "tool init --defaults"
    INVALID_ENVIRONMENT: fix_required: "Correct the target environment argument"
                         # no fix_command: correction needs caller input

register command "bad-remediation":
  error_registry:
    STATE_CONFLICT: fix_command: "tool reset --hard"
  → framework error: fix_command targets a destructive command (REQ-C-002)

register command "bad-placeholder":
  error_registry:
    TOKEN_MISSING: fix_command: "tool auth login --token <your-token>"
  → framework error: fix_command contains a placeholder; use fix_required prose instead
```

Agent consumption (the whole recovery loop a minimal agent needs):

```
run original command
if error.fix_command present:
    run error.fix_command
    if exit 0: reissue original command once
stop on any second failure
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Extends: adds `fix_command` to the error object defined there |
| [REQ-C-014](c-014-error-responses-include-retryable-and-retry-after-.md) | C | Composes: `fix_command` is the executable counterpart of `fix_required` |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Consumes: danger levels used to reject destructive remediation at registration |
| [REQ-F-063](f-063-credential-expiry-structured-error.md) | F | Specializes: `refresh_command` is the auth-specific instance of this field |
| [REQ-O-031](o-031-dependency-version-matrix-declaration.md) | O | Specializes: dependency `fix_command` in `tool doctor` checks follows the same safety contract |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `fix_command` is a field within `ResponseEnvelope.ErrorDetail` |
