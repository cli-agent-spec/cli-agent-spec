# REQ-O-002: --fields Selector

**Tier:** Opt-In | **Priority:** P2

**Source:** [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Low / Context: High

---

## Description

The framework MUST provide a `--fields <comma-separated-names>` flag on all commands. When specified, the JSON `data` object MUST contain only the listed top-level fields. Framework-level fields (`ok`, `error`, `meta`, `warnings`, `pagination`) MUST always be present regardless of `--fields`. This filtering MUST occur at the serialization layer, not requiring per-command implementation.

## Acceptance Criteria

- `--fields id,name` returns a `data` object with only `id` and `name` keys
- `ok`, `error`, `meta` are always present even with `--fields`
- An unknown field name in `--fields` is silently ignored (not an error)
- `--fields` is available on every command

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

The `data` field is projected to contain only the requested fields. The envelope shape (`ok`, `error`, `warnings`, `meta`) is unaffected.

---

## Wire Format

```bash
$ tool list-users --fields id,name --output json
```

```json
{
  "ok": true,
  "data": [
    { "id": "u1", "name": "alice" },
    { "id": "u2", "name": "bob" }
  ],
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 42 }
}
```

---

## Example

The framework registers `--fields` globally at opt-in time. Projection is applied at the serialization layer.

```
app = Framework("tool")
app.enable_fields_flag()

# tool list-users --fields id,name  →  data projected to id and name only
# tool get-user --id 1 --fields email  →  data contains only email
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-001](o-001-output-format-flag.md) | O | Composes: `--fields` filters within the `--output json` envelope |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: envelope shape that `--fields` projects into |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `meta` is never filtered by `--fields` |
