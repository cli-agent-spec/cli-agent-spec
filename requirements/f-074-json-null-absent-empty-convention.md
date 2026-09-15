# REQ-F-074: JSON Null/Absent/Empty Convention

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents branch on field presence/value; tools that use null, absent, and empty string interchangeably cause agents to take wrong code paths silently

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Medium

---

## Description

The framework MUST enforce a consistent three-way distinction in all JSON output:

- **Absent field** (key not present): the feature or field is not supported by this command or this version of the tool
- **`null`**: the feature is supported; the value is explicitly unset or unknown
- **`""`** (empty string) or `[]` (empty array): the feature is supported; the value is explicitly empty

The framework MUST never substitute one for another. A field that was present in a previous response MUST remain present (possibly as `null`) in subsequent responses for the same command — disappearing fields break agent parsers that check for key presence.

## Acceptance Criteria

- A field documented as optional in the schema is either always present (as `null` when unset) or always absent — never alternates between the two
- `""` is never used where `null` is semantically correct (unset vs empty are different states)
- `[]` is returned for empty collections, never `null` or absent
- Schema documentation explicitly marks each field as: required (never null/absent), nullable (present but may be null), or optional (may be absent if feature unsupported)
- Two calls to the same command under the same conditions produce the same set of keys

---

## Schema

`response-envelope` — the `data` field and all nested objects must follow this convention

---

## Wire Format

Correct:
```jsonc
{
  "name": "my-resource",
  "description": null,      ← supported, currently unset
  "tags": [],               ← supported, currently empty
  "deprecated_at": null     ← supported, not deprecated yet
}
```

Incorrect:
```jsonc
{
  "name": "my-resource",
  "description": "",        ← wrong: empty string ≠ unset
                            ← tags absent: wrong, should be []
  "deprecated_at": ""       ← wrong: empty string ≠ null
}
```

---

## Example

Agent checking if a resource is deprecated:

```python
if "deprecated_at" not in response["data"]:
    # Tool version doesn't support deprecation tracking — skip
elif response["data"]["deprecated_at"] is None:
    # Feature supported, resource not deprecated
else:
    # Resource deprecated at response["data"]["deprecated_at"]
```

This three-way check only works correctly when the convention is consistently applied.

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: envelope structure within which this convention applies |
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Composes: schema version lets agents know which fields to expect in which version |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: per-command schema that must document each field's nullability |
