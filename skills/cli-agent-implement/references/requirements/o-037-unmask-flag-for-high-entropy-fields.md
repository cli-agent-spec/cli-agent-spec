# REQ-O-037: --unmask Flag for High-Entropy Fields

**Tier:** Opt-In | **Priority:** P2

**Source:** [§59 High-Entropy String Token Poisoning](../challenges/01-critical-ecosystem-runtime-agent-specific/59-high-high-entropy-tokens.md)

**Addresses:** Severity: High / Token Spend: High / Time: Low / Context: High

---

## Description

The framework MUST provide `--unmask` as a global flag that disables the high-entropy masking from REQ-F-058. When `--unmask` is passed, all fields are returned with their raw values. This flag SHOULD require explicit invocation and MUST NOT be activated by any environment variable. The `--unmask` flag is intended for debugging and human inspection; agents should not pass it except when they specifically need the raw high-entropy value for a subsequent operation.

## Acceptance Criteria

- Without `--unmask`, a JWT field is returned as `[JWT: sub=..., exp=...]`
- With `--unmask`, the same field returns the full raw JWT string
- `--unmask` cannot be activated via environment variable
- `--schema` documents `--unmask` and notes that it exposes sensitive values

---

## Schema

No dedicated schema type — `--unmask` disables the masking applied by REQ-F-058 without adding new fields.

---

## Wire Format

Without `--unmask` (masked):

```json
{ "data": { "token": "[JWT: sub=alice, exp=1742000000, masked]" } }
```

With `--unmask`:

```json
{ "data": { "token": "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9..." } }
```

---

## Example

Opt-in at the framework level; works together with REQ-F-058.

```
app = Framework("tool")
app.enable_unmask()   # registers --unmask globally; requires f-058 masking enabled

# Default — token is masked to prevent leakage into logs/context:
$ tool get-token --output json
→ data.token: "[JWT: sub=alice, exp=1742000000, masked]"

# Explicit unmask for a subsequent API call:
$ tool get-token --unmask --output json
→ data.token: "eyJhbGci..."
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-058](f-058-high-entropy-field-masking.md) | F | Provides: the masking behavior that `--unmask` disables |
| [REQ-C-016](c-016-secrets-accepted-only-via-env-var-or-file.md) | C | Composes: high-entropy outputs should be treated with the same care as secret inputs |
