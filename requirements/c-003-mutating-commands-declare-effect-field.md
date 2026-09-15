# REQ-C-003: Mutating Commands Declare effect Field

**Tier:** Command Contract | **Priority:** P0

**Source:** [§12 Idempotency & Safe Retries](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Every command with `danger_level` of `mutating` or `destructive` MUST include an `effect` field in its success response. The `effect` value MUST be one of: `"created"`, `"updated"`, `"deleted"`, `"noop"`. Command authors MUST determine and set the correct value based on what actually occurred. The framework MUST validate that the `effect` field is present and has a valid value for all non-safe commands.

## Acceptance Criteria

- A mutating command response always includes `"effect"` at the top level of the envelope
- `effect: "noop"` is returned when the operation was a no-op (e.g., already at desired state)
- `effect: "created"` vs `effect: "updated"` is accurate (not always one or the other)
- The framework raises a registration or runtime error if a mutating command omits `effect`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

The `effect` field is required at the top level of the response envelope `data` for all non-safe commands. Allowed values: `"created"` · `"updated"` · `"deleted"` · `"noop"`.

```json
{
  "effect": {
    "type": "string",
    "enum": ["created", "updated", "deleted", "noop"],
    "description": "Describes what the command actually did; present on all mutating and destructive command responses"
  }
}
```

---

## Wire Format

```bash
$ tool create-order --amount 100 --idempotency-key abc123
```

```json
{
  "ok": true,
  "data": {
    "effect": "created",
    "id": 42,
    "amount": 100
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 84 }
}
```

Second call with same key:

```json
{
  "ok": true,
  "data": {
    "effect": "noop",
    "id": 42,
    "amount": 100
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 12 }
}
```

---

## Example

A mutating command sets `effect` based on what actually occurred at runtime. The command author determines the correct value.

```
register command "deploy":
  danger_level: mutating
  exit_codes:
    SUCCESS(0): description: "Deployment completed", retryable: false, side_effects: complete

  execute(args):
    current = get_current_version(args.target)
    if current == args.version:
      return response(effect="noop", current_version=current)
    deploy(args.target, args.version)
    return response(effect="updated", previous=current, current=args.version)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: mutating/destructive` triggers `effect` field obligation |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Composes: `effect: "noop"` is the canonical response for a deduplicated idempotency-key hit |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Extends: dry-run responses use `would_*` effect prefixes, not the values defined here |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `effect` is carried inside the `ResponseEnvelope` |
