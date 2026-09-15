# REQ-C-004: Destructive Commands Must Support --dry-run

**Tier:** Command Contract | **Priority:** P0

**Source:** [§23 Side Effects & Destructive Operations](../challenges/03-critical-security/23-critical-destructive-ops.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: High / Context: Medium

---

## Description

Every command with `danger_level: "destructive"` MUST implement a `--dry-run` mode. In dry-run mode, the command MUST perform all validation and computation but MUST NOT commit any irreversible change. The dry-run response MUST include `effect: "would_delete"` (or analogous `would_*` prefix), and MUST include a `would_affect` object describing what would be changed. The framework MUST register `--dry-run` as a standard flag for all destructive commands and MUST enforce that dry-run responses contain no actual mutations.

## Acceptance Criteria

- A destructive command with `--dry-run` never modifies any external state
- The dry-run response includes `effect` with a `"would_"` prefix
- The dry-run response includes a `would_affect` object with human-readable and machine-readable impact description
- The framework raises a registration error if a destructive command does not implement `--dry-run`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md)

Dry-run responses use a `would_*`-prefixed `effect` value and a `would_affect` object. The `--dry-run` flag is declared in the command's flag schema.

```json
{
  "effect": {
    "type": "string",
    "pattern": "^would_",
    "description": "Dry-run effect; always prefixed with 'would_' to distinguish from live execution"
  },
  "would_affect": {
    "type": "object",
    "description": "Machine-readable and human-readable description of what a live run would change"
  }
}
```

---

## Wire Format

```bash
$ tool delete-account --user 42 --dry-run
```

```json
{
  "ok": true,
  "data": {
    "effect": "would_delete",
    "would_affect": {
      "user": { "id": 42, "name": "Alice" },
      "related_records": 234,
      "reversible": false
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 31 }
}
```

The `--dry-run` flag appears in `--schema`:

```json
{
  "flags": {
    "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Validate and preview impact without executing" }
  }
}
```

---

## Example

A destructive command must implement a `dry_run` path that returns affected scope without mutating state.

```
register command "delete-account":
  danger_level: destructive
  dry_run: supported
  exit_codes:
    SUCCESS(0): description: "Account deleted or dry-run completed", retryable: false, side_effects: complete

  execute(args, dry_run=False):
    user = fetch_user(args.user)
    related = count_related_records(args.user)
    if dry_run:
      return response(
        effect="would_delete",
        would_affect={"user": user, "related_records": related, "reversible": False}
      )
    delete_user(args.user)
    return response(effect="deleted")
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: destructive` triggers `--dry-run` enforcement |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Extends: dry-run `would_*` effect values are the preview counterpart to live `effect` values |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Composes: `--confirm-destructive` is the companion flag that enables the live run after a dry-run preview |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: dry-run response uses `ResponseEnvelope` with `ok: true` |
