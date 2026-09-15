# REQ-O-007: --stable-output Flag

**Tier:** Opt-In | **Priority:** P3

**Source:** [§7 Output Non-Determinism](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide a `--stable-output` flag that explicitly requests deterministic output: all arrays sorted, all volatile `meta` fields omitted from comparison, and any remaining non-deterministic content replaced with stable alternatives. Commands that declare non-deterministic fields MUST omit those fields when `--stable-output` is passed. This flag is intended for caching and change-detection use cases.

## Acceptance Criteria

- Two invocations of the same command with `--stable-output` and identical arguments produce byte-identical stdout
- `meta.request_id` and `meta.timestamp` are omitted when `--stable-output` is passed
- `--stable-output` implies all arrays are sorted (REQ-F-020 behavior is always-on, but this flag is a caller signal for caching intent)

---

## Schema

No dedicated schema type — this requirement governs output determinism. `--stable-output` causes certain `meta` fields (`request_id`, `timestamp`) to be omitted from the standard `ResponseEnvelope`.

---

## Wire Format

```bash
$ tool list-users --stable-output --output json
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
  "meta": { "exit_code": 0, "duration_ms": 44 }
}
```

Note: `meta.request_id` and `meta.timestamp` are absent. Arrays are lexicographically sorted.

---

## Example

The framework registers `--stable-output` globally at opt-in time.

```
app = Framework("tool")
app.enable_stable_output_flag()

# tool list-users --stable-output  →  byte-identical across invocations with same args
# Useful for caching: hash(stdout) is a reliable content fingerprint
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-020](f-020-stable-array-sorting-in-json-output.md) | F | Provides: array sorting behavior activated by `--stable-output` signal |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` whose volatile `meta` fields are suppressed |
| [REQ-F-024](f-024-request-id-and-trace-id-in-every-response.md) | F | Provides: `request_id` field omitted when `--stable-output` is active |
