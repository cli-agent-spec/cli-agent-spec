# REQ-C-007: Mutating Commands Accept --idempotency-key

**Tier:** Command Contract | **Priority:** P1

**Source:** [§12 Idempotency & Safe Retries](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Every command with `danger_level: "mutating"` or `"destructive"` MUST accept an `--idempotency-key <string>` argument. The command MUST use this key to detect and short-circuit duplicate invocations, returning the original result with `effect: "noop"` and the original response data. When no key is supplied, the framework MAY auto-generate one (deterministic, based on command + args + session) or MUST document that the operation is not deduplication-safe.

## Acceptance Criteria

- Invoking a mutating command twice with the same `--idempotency-key` returns `effect: "noop"` on the second call
- The second call's response `data` matches the first call's response `data`
- An auto-generated idempotency key is deterministic for the same command arguments within a session

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

The `--idempotency-key` flag appears in the schema for all mutating and destructive commands.

```json
{
  "flags": {
    "idempotency-key": {
      "type": "string",
      "required": false,
      "description": "Caller-supplied key; duplicate calls with the same key return the original result without re-executing"
    }
  }
}
```

---

## Wire Format

First call:

```bash
$ tool create-order --amount 100 --idempotency-key order-abc123
```

```json
{
  "ok": true,
  "data": { "effect": "created", "id": 42, "amount": 100 },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 91 }
}
```

Second call with the same key:

```bash
$ tool create-order --amount 100 --idempotency-key order-abc123
```

```json
{
  "ok": true,
  "data": { "effect": "noop", "id": 42, "amount": 100 },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 9, "idempotency_hit": true }
}
```

---

## Example

A mutating command stores the result keyed by the idempotency key and returns it on subsequent calls without re-executing.

```
register command "create-order":
  danger_level: mutating
  exit_codes:
    SUCCESS  (0): description: "Order created or already existed", retryable: false, side_effects: complete
    ARG_ERROR(2): description: "Invalid amount",                   retryable: false, side_effects: none

  execute(args):
    cached = idempotency_store.get(args.idempotency_key)
    if cached:
      return response(effect="noop", **cached, meta={idempotency_hit: True})
    order = create_order(amount=args.amount)
    idempotency_store.set(args.idempotency_key, {id: order.id, amount: order.amount})
    return response(effect="created", id=order.id, amount=order.amount)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: mutating/destructive` triggers `--idempotency-key` requirement |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Composes: `effect: "noop"` is the canonical response value for an idempotency-key hit |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: idempotency response uses `ResponseEnvelope` |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `SUCCESS (0)` covers both the live execution and the noop case |
