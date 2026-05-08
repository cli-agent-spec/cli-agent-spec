# REQ-O-047: tool check-permissions Built-In Command

**Tier:** Opt-In | **Priority:** P0

**Source:** [§74 Credential Scope Declaration Absence](../challenges/03-critical-security/74-critical-credential-scope-declaration.md)

**Addresses:** Severity: Critical / Token Spend: Low / Time: Medium / Context: Low

---

## Description

The framework MUST provide a `check-permissions` built-in command. When invoked with `--for <command>`, it resolves the active credential's scopes, compares them against the target command's `required_scopes` (REQ-C-029), and returns a machine-readable report. Without `--for`, it returns a full coverage table across all registered commands.

The command MUST always exit 0 — over-privilege is a warning, not a blocking error. Insufficient scopes cause exit `8` (`AUTH_ERROR`) with the missing scopes listed in `error.detail.missing_scopes`.

The framework MUST also emit a structured `warnings[]` entry whenever a command is invoked and the active credential's scopes exceed the command's `required_scopes`. This runtime warning fires automatically — no per-invocation flag needed — once the opt-in is activated.

## Acceptance Criteria

- `tool check-permissions --for <command>` exits 0 and returns `required_scopes`, `active_scopes`, and `over_privileged`
- `tool check-permissions` (no `--for`) returns `data.commands` — a map of command name → scope coverage
- Over-privilege (`active_scopes ⊃ required_scopes`) exits 0 with `over_privileged: true` and a warning in `warnings[]`
- Insufficient scopes (`active_scopes ⊄ required_scopes`) exits 8 with `error.detail.missing_scopes`
- When any registered command is invoked and active scopes exceed `required_scopes`, a warning entry appears in `warnings[]` of the response envelope
- Credentials with zero declared scopes (unauthenticated calls) are not flagged as over-privileged

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md)

The `check-permissions` response uses the standard `ResponseEnvelope` with a `data` object carrying the scope report. `warnings[]` entries use the standard warning string format.

```json
{
  "required_scopes": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Scopes the command declared at registration"
  },
  "active_scopes": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Scopes the active credential actually holds"
  },
  "over_privileged": {
    "type": "boolean",
    "description": "True when active_scopes is a strict superset of required_scopes"
  },
  "missing_scopes": {
    "type": "array",
    "items": { "type": "string" },
    "description": "Scopes in required_scopes absent from active_scopes; present only on AUTH_ERROR"
  }
}
```

---

## Wire Format

Sufficient and exactly-scoped credential:

```bash
$ tool check-permissions --for "issue list"
```

```json
{
  "ok": true,
  "data": {
    "command": "issue list",
    "required_scopes": ["repo:read"],
    "active_scopes": ["repo:read"],
    "over_privileged": false
  },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 42 }
}
```

Over-privileged credential (still exits 0):

```bash
$ tool check-permissions --for "issue list"
```

```json
{
  "ok": true,
  "data": {
    "command": "issue list",
    "required_scopes": ["repo:read"],
    "active_scopes": ["repo:read", "repo:write", "admin:org"],
    "over_privileged": true
  },
  "error": null,
  "warnings": [
    "Credential has scopes beyond what 'issue list' requires — consider a token scoped to [repo:read] only"
  ],
  "meta": { "duration_ms": 38 }
}
```

Insufficient credential (exits 8):

```bash
$ tool check-permissions --for "repo delete"
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "AUTH_ERROR",
    "message": "Active credential is missing required scopes",
    "detail": {
      "command": "repo delete",
      "required_scopes": ["delete_repo"],
      "active_scopes": ["repo:read"],
      "missing_scopes": ["delete_repo"]
    }
  },
  "warnings": [],
  "meta": { "duration_ms": 29 }
}
```

Full coverage table (no `--for`):

```bash
$ tool check-permissions
```

```json
{
  "ok": true,
  "data": {
    "commands": {
      "issue list":  { "required_scopes": ["repo:read"],   "covered": true,  "over_privileged": true  },
      "issue create":{ "required_scopes": ["issues:write"],"covered": true,  "over_privileged": true  },
      "repo delete": { "required_scopes": ["delete_repo"], "covered": false, "over_privileged": false }
    }
  },
  "error": null,
  "warnings": [
    "Credential is over-privileged for: issue list, issue create"
  ],
  "meta": { "duration_ms": 91 }
}
```

Runtime warning on normal command invocation (over-privileged credential):

```bash
$ tool issue list --repo my-org/my-repo
```

```json
{
  "ok": true,
  "data": [ ... ],
  "error": null,
  "warnings": [
    "Credential has scopes beyond what 'issue list' requires — consider a token scoped to [repo:read] only"
  ],
  "meta": { "duration_ms": 203 }
}
```

---

## Example

Opt-in at framework configuration — the framework activates the `check-permissions` built-in and enables runtime over-privilege warnings:

```
configure framework:
  builtins:
    check-permissions: enabled    # activates tool check-permissions command
    scope-warnings: enabled       # activates runtime warnings[] on over-privilege
```

Agent pre-flight pattern:

```python
result = run(["tool", "check-permissions", "--for", "repo delete"])
parsed = json.loads(result.stdout)

if not parsed["ok"]:
    missing = parsed["error"]["detail"]["missing_scopes"]
    raise RuntimeError(f"Credential missing scopes: {missing}")

if parsed["data"]["over_privileged"]:
    log.warning("Over-privileged credential — blast radius exceeds workflow needs")
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-029](c-029-command-declares-required-scopes.md) | C | Provides: `required_scopes` declarations that `check-permissions` reads |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Composes: `danger_level` and `required_scopes` form the complete command security profile |
| [REQ-F-063](f-063-credential-expiry-structured-error.md) | F | Extends: `AUTH_ERROR` exit code used for both expiry and missing-scope failures |
| [REQ-O-026](o-026-tool-doctor-built-in-command.md) | O | Composes: `doctor` may invoke `check-permissions` as one of its environment health checks |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Consumes: over-privilege warnings are recorded in the append-only audit log |
