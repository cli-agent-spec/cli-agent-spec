# REQ-O-048: Destructive Commands Default to Dry-Run Mode

**Tier:** Opt-In | **Priority:** P0

**Source:** [§75 Safe-Default Execution Mode Absent](../challenges/03-critical-security/75-critical-safe-default-execution.md)

**Addresses:** Severity: Critical / Token Spend: Low / Time: Critical / Context: Low

---

## Description

Commands that declare `safe_default: true` MUST execute in dry-run mode when invoked without `--live`. The framework MUST inject a `--live` flag on all `safe_default: true` commands, route execution through the dry-run path when `--live` is absent, and include `meta.dry_run: true` in every response envelope for that path. A live invocation MUST include `meta.dry_run: false` and `meta.confirmed: true`. The `safe_default` field MUST be present in the manifest response so agents can detect and adjust their invocation strategy.

This requirement is distinct from REQ-C-004 (`--dry-run` availability) and REQ-O-021 (`--confirm-destructive` gate). Safe-default mode makes the dry-run path the zero-argument default — not a flag the caller must remember — and uses `--live` as the explicit opt-in to execution.

## Acceptance Criteria

- A `safe_default: true` command invoked without `--live` returns a `would_*` effect, exits 0, and causes no side effects
- A `safe_default: true` command invoked with `--live` executes and returns an effect without a `would_` prefix
- The response envelope always includes `meta.dry_run` (boolean) for `safe_default: true` commands
- The manifest exposes `safe_default: true` on commands that declare it
- The framework raises a registration error if a `safe_default: true` command does not implement a dry-run path

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md)

The `meta` object is extended with `dry_run`:

```json
{
  "meta": {
    "dry_run": {
      "type": "boolean",
      "description": "True when the command ran in preview mode; false when --live was passed and side effects occurred"
    }
  }
}
```

The manifest command entry is extended with `safe_default`:

```json
{
  "safe_default": {
    "type": "boolean",
    "description": "True when the command defaults to dry-run mode; --live is required to execute for real"
  }
}
```

---

## Wire Format

Without `--live` (dry-run by default):

```bash
$ trade execute --symbol BTC --amount 10000
```

```json
{
  "ok": true,
  "data": {
    "effect": "would_execute",
    "would_affect": {
      "order": { "symbol": "BTC", "side": "buy", "amount": 10000 },
      "estimated_cost_usd": 847230.00,
      "reversible": false
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "dry_run": true, "duration_ms": 42 }
}
```

With `--live`:

```bash
$ trade execute --symbol BTC --amount 10000 --live
```

```json
{
  "ok": true,
  "data": { "effect": "executed", "order_id": "ord_abc123" },
  "error": null,
  "warnings": [],
  "meta": { "dry_run": false, "confirmed": true, "duration_ms": 381 }
}
```

The `--live` flag appears in `--schema`:

```json
{
  "flags": {
    "live": {
      "type": "boolean",
      "required": false,
      "default": false,
      "description": "Execute for real; omit to preview scope without side effects"
    }
  }
}
```

---

## Example

```
register command "execute":
  danger_level: destructive
  safe_default: true   # framework injects --live; dry-run is the zero-arg default

  execute(args, live=False):
    order = build_order(args.symbol, args.amount)
    cost  = estimate_cost(order)
    if not live:
      return response(
        effect="would_execute",
        would_affect={"order": order, "estimated_cost_usd": cost, "reversible": False},
        meta={"dry_run": True}
      )
    result = submit_order(order)
    return response(
      effect="executed",
      order_id=result.id,
      meta={"dry_run": False, "confirmed": True}
    )
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: "destructive"` is a prerequisite for `safe_default: true` |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Extends: safe-default mode is the next level above opt-in `--dry-run` availability |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Composes: `--confirm-destructive` and `--live` serve different patterns; safe-default replaces the gate with a natural preview → commit workflow |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: both dry-run and live responses use `ResponseEnvelope` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Extends: `meta.dry_run` field added to standard envelope meta |
