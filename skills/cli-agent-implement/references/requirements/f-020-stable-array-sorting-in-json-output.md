# REQ-F-020: Stable Array Sorting in JSON Output

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§7 Output Non-Determinism](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

In JSON output mode, the framework MUST sort all array fields in a stable, deterministic order before serialization. Arrays of objects MUST be sorted by a stable primary key (declared by the command author). Arrays of strings MUST be sorted lexicographically. Arrays of numbers MUST be sorted numerically ascending. The sort MUST be consistent across runs with identical inputs.

## Acceptance Criteria

- Two invocations of the same command with the same arguments produce byte-identical JSON output (excluding `meta` volatile fields)
- A string array output field is always in lexicographic order
- An object array output field is always sorted by the declared primary key

---

## Schema

No dedicated schema type — this requirement governs serialization behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed beyond declaring a primary sort key for object arrays. The framework sorts arrays deterministically before serialization.

```
# String array — always lexicographic
"tags": ["alpha", "beta", "gamma"]   ✓ stable
"tags": ["gamma", "alpha", "beta"]   ✗ framework re-sorts

# Object array — sorted by declared primary key "id"
"users": [
  {"id": "alice", "joined": "2024-01-01"},
  {"id": "bob",   "joined": "2023-06-15"}
]
# Two runs with identical state → byte-identical "users" array

# Excludes volatile meta fields from stability guarantee
"meta": {"request_id": "req_01", "timestamp": "..."}  ← volatile, excluded
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Composes: stable `data` arrays depend on volatile fields being isolated in `meta` |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope whose `data` field benefits from stable array ordering |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: output schema declaration used to specify the primary sort key for object arrays |
