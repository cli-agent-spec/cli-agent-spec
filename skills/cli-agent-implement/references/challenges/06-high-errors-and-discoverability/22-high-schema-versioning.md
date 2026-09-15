> **Part III: Errors & Discoverability** | Challenge §22

## 22. Schema Versioning & Output Stability

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

Agents built against a tool's output schema break silently when that schema changes. A field renamed, a type changed, or a new required field added can corrupt downstream logic with no warning.

**Silent breaking change:**
```bash
# Tool v1.x:
$ tool get-user --id 42
{"id": 42, "name": "Alice", "email": "alice@example.com"}

# Tool v2.x (field renamed):
$ tool get-user --id 42
{"id": 42, "full_name": "Alice", "email_address": "alice@example.com"}

# Agent code: user["name"]  → KeyError, silent None, or wrong value
# Agent was never told the schema changed
```

**Type change without notice:**
```bash
# v1: "status" was a string
{"status": "active"}

# v2: "status" is now an object
{"status": {"value": "active", "since": "2024-01-01"}}

# Agent: if result["status"] == "active" → always False now
```

**New required output field breaks agent parsing:**
```bash
# Agent extracts specific fields; new mandatory fields are ignored
# But if agent does strict schema validation, it rejects the response
```

### Impact

- Silent wrong behavior (agent reads stale field, gets None/wrong value)
- Hard to debug: agent works fine until tool is upgraded
- No way to detect the mismatch without version checking

### Solutions

**Schema version in every response:**
```json
{
  "ok": true,
  "meta": {
    "schema_version": "2.1.0",
    "tool_version": "2.4.1"
  },
  "data": {...}
}
```

**Deprecation warnings before removal:**
```json
{
  "ok": true,
  "data": {
    "name": "Alice",        // deprecated, use full_name
    "full_name": "Alice"    // new field
  },
  "warnings": [
    {
      "code": "FIELD_DEPRECATED",
      "message": "Field 'name' is deprecated. Use 'full_name' instead.",
      "removed_in": "3.0.0"
    }
  ]
}
```

**Stability tiers declared in schema:**
```json
{
  "fields": {
    "id":         {"stability": "stable"},
    "full_name":  {"stability": "stable"},
    "score":      {"stability": "experimental", "may_change": true},
    "_internal":  {"stability": "private", "do_not_depend_on": true}
  }
}
```

**Version negotiation:**
```bash
tool get-user --id 42 --schema-version 1
# Returns v1-compatible output even from v2 tool
# Allows gradual migration
```

**For framework design:**
- `meta.schema_version` in every response (semver)
- `--schema-version` flag to request compatible output
- Deprecation warnings 2 major versions before removal
- `tool changelog --output json` lists all schema changes by version

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No `schema_version` in responses; breaking changes are silent; agent has no way to detect schema drift |
| 1 | `meta.tool_version` present but no `schema_version`; no deprecation warnings before removal |
| 2 | `meta.schema_version` in every response; `warnings` array emitted for deprecated fields with `removed_in` |
| 3 | `--schema-version` flag for compatible output; stability tiers declared in schema; `tool changelog --output json` available |

**Check:** Run any command and verify `meta.schema_version` is present as a semver string — then check that deprecated fields in the response include a `warnings[].code == "FIELD_DEPRECATED"` entry.

---

### Agent Workaround

**Signature:** previously working field lookups fail after a tool upgrade; responses lack `meta.schema_version`; JSON shape differs across versions

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Run `tool --version` and confirm it matches the version the integration was built against; if that fails, escalate with the command, exit code, stdout, and stderr

**Track `meta.schema_version` across calls; fail fast when version changes mid-session:**

```python
import subprocess, json

SESSION_SCHEMA_VERSION = None

def run_versioned(cmd: list[str]) -> dict:
    global SESSION_SCHEMA_VERSION

    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = json.loads(result.stdout)

    meta = parsed.get("meta", {})
    version = meta.get("schema_version")

    if version:
        if SESSION_SCHEMA_VERSION is None:
            SESSION_SCHEMA_VERSION = version
        elif version != SESSION_SCHEMA_VERSION:
            raise RuntimeError(
                f"Schema version changed mid-session: "
                f"{SESSION_SCHEMA_VERSION} → {version} — "
                "agent skill may be incompatible with new output"
            )

    # Log deprecation warnings to help flag needed updates
    for w in parsed.get("warnings", []):
        if w.get("code") == "FIELD_DEPRECATED":
            print(
                f"[DEPRECATION] {w['message']} (removed in {w.get('removed_in')})"
            )

    return parsed
```

**Request a pinned schema version when `--schema-version` is supported:**
```python
result = subprocess.run(
    ["tool", "get-user", "--id", "42",
     "--schema-version", "1",   # pin to v1-compatible output
     "--output", "json"],
    capture_output=True, text=True,
)
```

**Limitation:** If the tool provides no `meta.schema_version`, the agent cannot detect schema changes — use a fixed set of known-good fields and access all response fields via `.get()` with defaults rather than direct key access, so that renamed fields fail gracefully rather than raising exceptions

