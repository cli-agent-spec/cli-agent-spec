# REQ-O-032: --raw-payload Flag for Mutating Commands

**Tier:** Opt-In | **Priority:** P1

**Source:** [§46 API Schema to CLI Flag Translation Loss](../challenges/01-critical-ecosystem-runtime-agent-specific/46-high-api-translation-loss.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Medium

---

## Description

Mutating commands (those with `danger_level: "mutating"` or `"destructive"`) SHOULD support a `--raw-payload <json>` flag that accepts a raw JSON object mapped directly to the command's underlying API schema. When `--raw-payload` is used, the framework bypasses individual flag parsing and passes the payload directly to the command handler, enabling agents to pass API-native payloads with zero translation loss. The framework MUST validate `--raw-payload` content against the command's Pydantic or JSON Schema before execution. When `--raw-payload` and individual flags are both supplied, the framework MUST reject the invocation with exit code 2.

## Acceptance Criteria

- `command create --raw-payload '{"name": "foo", "count": 3}'` is equivalent to `command create --name foo --count 3`
- Invalid `--raw-payload` JSON exits with code 2 and a structured field-level error
- Supplying both `--raw-payload` and individual flags exits with code 2
- The `--schema` output for mutating commands includes a `raw_payload_schema` section

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

`--schema` output for mutating commands includes a `raw_payload_schema` field containing the JSON Schema for the `--raw-payload` argument.

---

## Wire Format

```bash
$ tool create --raw-payload '{"name":"prod","region":"us-east-1"}' --format json
```

```json
{
  "ok": true,
  "data": { "id": "env-abc123", "name": "prod", "region": "us-east-1" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "effect": "created", "duration_ms": 241 }
}
```

Conflict when `--raw-payload` and individual flags are both supplied:

```json
{
  "ok": false,
  "data": null,
  "error": { "code": "ARG_ERROR", "message": "Cannot combine --raw-payload with individual flags" },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 12, "phase": "validation" }
}
```

---

## Example

Opt-in per command by declaring `supports_raw_payload: true`.

```
register command "create":
  danger_level: mutating
  supports_raw_payload: true   # enables --raw-payload flag

# Agent passes API-native payload with zero translation:
$ tool create --raw-payload '{"name":"prod","region":"us-east-1"}'
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Provides: `danger_level` determines which commands support `--raw-payload` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: `raw_payload_schema` is derived from the command's registered input schema |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Composes: `meta.effect` in the response reflects the action taken via raw payload |
