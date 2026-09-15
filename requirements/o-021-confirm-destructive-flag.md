# REQ-O-021: --confirm-destructive Flag

**Tier:** Opt-In | **Priority:** P0

**Source:** [§23 Side Effects & Destructive Operations](../challenges/03-critical-security/23-critical-destructive-ops.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: High / Context: Medium

---

## Description

The framework MUST provide `--confirm-destructive` as a standard flag on all commands with `danger_level: "destructive"`. Without this flag, a destructive command MUST exit with a structured error (exit `2`) explaining that the flag is required and showing what would be affected (equivalent to an implicit `--dry-run` output). With this flag, the command proceeds. This is distinct from `--yes` (which auto-confirms interactive prompts) and specifically guards destructive operations in automated contexts.

## Acceptance Criteria

- A destructive command invoked without `--confirm-destructive` exits `2` with a JSON error listing what would be affected
- A destructive command invoked with `--confirm-destructive` proceeds normally
- The `--schema` output for destructive commands includes `requires_confirmation: true`
- `--confirm-destructive` is absent on non-destructive commands

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When `--confirm-destructive` is supplied, the response `meta` object includes `confirmed: true`. When absent, the command exits `2` with a structured error showing the implicit dry-run summary:

```json
{
  "meta": {
    "confirmed": true
  }
}
```

---

## Wire Format

Without the flag (implicit dry-run error):

```bash
$ tool delete --resource my-db
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "CONFIRMATION_REQUIRED",
    "message": "Pass --confirm-destructive to proceed",
    "context": {
      "would_affect": ["my-db"],
      "danger_level": "destructive"
    }
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 3 }
}
```

With the flag:

```bash
$ tool delete --resource my-db --confirm-destructive
```

```json
{
  "ok": true,
  "data": { "deleted": "my-db" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "confirmed": true, "duration_ms": 241 }
}
```

---

## Example

Opt-in at command registration — the framework injects `--confirm-destructive` automatically for any command tagged `danger_level: "destructive"`:

```
register command "delete":
  danger_level: destructive
  # framework auto-adds --confirm-destructive flag
  # no flag declaration needed in command code
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: "destructive"` declaration that triggers this flag |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Composes: implicit dry-run output mirrors the `--dry-run` contract |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: confirmation error and success both use `ResponseEnvelope` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Extends: `meta.confirmed` field added to standard envelope meta |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Consumes: destructive confirmation is recorded in the audit log |
