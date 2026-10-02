# REQ-O-048: High-Stakes Commands Default to Dry-Run Mode

**Tier:** Opt-In | **Priority:** P0

**Source:** [§75 Safe-Default Execution Mode Absent](../challenges/03-critical-security/75-critical-safe-default-execution.md)

**Addresses:** Severity: Critical / Token Spend: Low / Time: Critical / Context: Low

---

## Description

A command makes the dry-run path its zero-argument default in one of two ways: `safe_default: true`, where the framework injects `--live`, or `confirm_flag: "<name>"`, where the command's own boolean flag (such as `--yes`) confirms execution. Either way, a call without the confirming flag previews and a call with it runs.

**`safe_default`.** Commands that declare `safe_default: true` MUST execute in dry-run mode when invoked without `--live`. The framework MUST inject a `--live` flag on all `safe_default: true` commands, route execution through the dry-run path when `--live` is absent, and include `meta.dry_run: true` in every response envelope for that path. A live invocation MUST include `meta.dry_run: false` and `meta.confirmed: true`. The `safe_default` field MUST be present in the manifest response so agents can detect and adjust their invocation strategy.

**`confirm_flag`.** A command with `danger_level` `mutating` or `destructive` MAY declare `confirm_flag` with the name, without `--`, of a boolean flag it accepts: one of its own `flags` or a root flag. The framework does not inject that flag; it MUST refuse the registration when the named flag is not a declared boolean flag of the command or root, when the command's `danger_level` is `safe`, when the same command declares `safe_default: true` (two confirmation mechanisms on one command), when the command is a passthrough command (REQ-C-031), or when the command implements no dry-run path. At run time:

- Without the confirm flag, the command runs the dry-run path under the dry-run contract (REQ-C-004): a `would_*` effect, a `would_affect` object, `meta.dry_run: true`, exit `0`, and no side effects. It does not prompt for the confirmation the flag stands for, with or without a TTY; the preview takes the prompt's place
- With the confirm flag, the command executes and the envelope carries `meta.dry_run: false` and `meta.confirmed: true`
- `--dry-run` wins: when the command accepts `--dry-run` and it is given, the command previews even when the confirm flag is given too. REQ-O-050's `exec --dry-run`, which forwards `dry_run: true` to every dispatched mutating or destructive command, therefore previews a `confirm_flag` command even when its dispatched line passes the confirm flag
- When REQ-O-021 is enabled, a destructive command's `confirm_flag` MUST be `confirm-destructive`, so the command keeps one confirmation flag. Without it the command previews and exits `0` instead of exiting `2` with `CONFIRMATION_REQUIRED`
- When the confirm flag is `yes` on an `interactive: true` command (REQ-C-005), `--yes` still auto-confirms every other prompt; `--non-interactive` never turns the missing confirmation into exit `4`, since the command previews instead of prompting

The manifest MUST expose `confirm_flag` on every command that declares it, so an agent knows before the first call that a bare call only previews and which flag runs it.

This requirement is distinct from REQ-C-004 (`--dry-run` availability) and REQ-O-021 (`--confirm-destructive` gate). Safe-default mode makes the dry-run path the zero-argument default (not a flag the caller must remember) and uses `--live` or the declared confirm flag as the explicit opt-in to execution.

## Acceptance Criteria

- A `safe_default: true` command invoked without `--live` returns a `would_*` effect, exits 0, and causes no side effects
- A `safe_default: true` command invoked with `--live` executes and returns an effect without a `would_` prefix
- The response envelope always includes `meta.dry_run` (boolean) for `safe_default: true` commands and for commands that declare `confirm_flag`
- The manifest exposes `safe_default: true` on commands that declare it
- The framework raises a registration error if a `safe_default: true` command does not implement a dry-run path
- A command that declares `confirm_flag` and is invoked without that flag returns a `would_*` effect, carries `meta.dry_run: true`, exits 0, and causes no side effects, in a TTY and outside one
- A command that declares `confirm_flag` and is invoked with that flag executes, returns an effect without a `would_` prefix, and carries `meta.dry_run: false` and `meta.confirmed: true`
- A command that declares `confirm_flag` and is invoked with both `--dry-run` and that flag previews, carries `meta.dry_run: true`, and causes no side effects
- `tool exec --dry-run` previews a dispatched `confirm_flag` command whose line passes the confirm flag
- The framework raises a registration error for a `confirm_flag` that names no declared boolean flag of the command or root, on a `safe` command, on a command that also declares `safe_default: true`, on a passthrough command, and on a command without a dry-run path
- With REQ-O-021 enabled, the framework raises a registration error for a destructive command whose `confirm_flag` is not `confirm-destructive`
- The manifest exposes `confirm_flag` on every command that declares it

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.md`](../schemas/manifest-response.md) · [`manifest-response.json`](../schemas/manifest-response.json)

The `meta` object is extended with `dry_run`:

```json
{
  "meta": {
    "dry_run": {
      "type": "boolean",
      "description": "True when the command ran in preview mode; false when --live or the confirm flag was passed and side effects occurred"
    }
  }
}
```

The manifest command entry is extended with `safe_default` and `confirm_flag`:

```json
{
  "safe_default": {
    "type": "boolean",
    "description": "True when the command defaults to dry-run mode; --live is required to execute for real"
  },
  "confirm_flag": {
    "type": "string",
    "description": "Boolean flag, without leading --, that confirms execution; without it the command previews"
  }
}
```

The manifest schema rejects `confirm_flag` on a `safe` command, next to `safe_default: true`, and on a passthrough command. That the name refers to a declared boolean flag is checked at registration.

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
  "meta": { "exit_code": 0, "dry_run": true, "duration_ms": 42 }
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
  "meta": { "exit_code": 0, "dry_run": false, "confirmed": true, "duration_ms": 381 }
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

A mutating command that runs only with `--yes` declares it in the manifest:

```json
{
  "description": "Apply pending schema migrations",
  "danger_level": "mutating",
  "required_scopes": [],
  "confirm_flag": "yes",
  "flags": {
    "yes":     { "type": "boolean", "required": false, "default": false, "description": "Apply the migrations; omit to preview them" },
    "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Preview the migrations even when --yes is given" }
  },
  "exit_codes": {}
}
```

Without `--yes`, and with `--dry-run --yes`, the call previews:

```bash
$ db migrate
$ db migrate --dry-run --yes
```

```json
{
  "ok": true,
  "data": {
    "effect": "would_migrate",
    "would_affect": { "migrations": ["0042_add_index", "0043_drop_legacy"], "reversible": false }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "dry_run": true, "duration_ms": 18 }
}
```

With `--yes` alone, it runs:

```bash
$ db migrate --yes
```

```json
{
  "ok": true,
  "data": { "effect": "migrated", "applied": ["0042_add_index", "0043_drop_legacy"] },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "dry_run": false, "confirmed": true, "duration_ms": 912 }
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

register command "migrate":
  danger_level: mutating
  flags: yes (boolean), dry-run (boolean)
  confirm_flag: yes    # framework checks --yes is a declared boolean flag

  # framework: run = args.yes and not args.dry_run
  migrate(args, run):
    pending = pending_migrations()
    if not run:
      return response(effect="would_migrate", would_affect={"migrations": pending},
                      meta={"dry_run": True})
    applied = apply(pending)
    return response(effect="migrated", applied=applied,
                    meta={"dry_run": False, "confirmed": True})

register command "reset":
  danger_level: safe
  confirm_flag: yes
  → framework error: confirm_flag requires danger_level mutating or destructive
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level: "destructive"` is a prerequisite for `safe_default: true`, and `mutating` or `destructive` for `confirm_flag` |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Extends: safe-default mode is the next level above opt-in `--dry-run` availability; `--dry-run` wins over a confirm flag |
| [REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md) | C | Composes: a `confirm_flag` of `yes` confirms execution as well as every prompt |
| [REQ-C-031](c-031-passthrough-commands-delegate-to-another-parser.md) | C | Composes: a passthrough command cannot preview, so it declares no `confirm_flag` |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Composes: `--confirm-destructive` and `--live` serve different patterns; safe-default replaces the gate with a natural preview → commit workflow, and a destructive `confirm_flag` names `confirm-destructive` when the gate is enabled |
| [REQ-O-050](o-050-tool-exec-built-in-command.md) | O | Composes: `exec --dry-run` previews a `confirm_flag` command even when its line passes the confirm flag |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `safe_default` and `confirm_flag` appear in the manifest |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: both dry-run and live responses use `ResponseEnvelope` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Extends: `meta.dry_run` field added to standard envelope meta |
