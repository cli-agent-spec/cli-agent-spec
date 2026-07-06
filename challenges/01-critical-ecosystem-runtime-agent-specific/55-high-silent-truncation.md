> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §55

## 55. Silent Data Truncation

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

CLI tools that write to remote APIs often silently truncate field values that exceed API limits: descriptions > 255 chars, names > 64 chars, tag arrays > 10 items. The tool reports `exit 0` and `"ok": true`, but the resource was created with silently truncated data. The agent has no way to know the intended values weren't fully stored.

```bash
$ tool create-issue \
  --title "This is a very long title that definitely exceeds the 64 character limit"

{"ok": true, "data": {"id": 123, "title": "This is a very long title that definitely"}}
# Exit 0. Title was truncated silently. Agent proceeds with wrong assumption.
```

Array truncation is worse — items are silently dropped:
```bash
$ tool tag-resource --id res_1 --tags a,b,c,d,e,f,g,h,i,j,k  # 11 tags, limit is 10
# k was dropped. Agent thinks all 11 tags were applied.
```

### Impact

- Data integrity violations completely invisible to the agent at operation time
- Agent reasoning built on "confirmed" values that were actually altered
- Downstream operations reference data that doesn't exist as expected

### Solutions

**Truncated fields MUST appear in `warnings[]`:**
```json
{
  "ok": true,
  "warnings": [
    {
      "code": "FIELD_TRUNCATED",
      "field": "title",
      "original_length": 71,
      "truncated_to": 41
    }
  ]
}
```

**Better: reject at Phase 1 validation with field constraints from schema:**
```json
{ "name": "title", "type": "string", "max_length": 64 }
{ "name": "tags",  "type": "array",  "max_items": 10 }
```

**For framework design:**
- Schema MUST declare `max_length`, `max_items`, `max_bytes` for all bounded fields; Phase 1 rejects inputs exceeding these limits
- If backend silently truncates anyway, framework MUST compare returned vs sent value and inject `FIELD_TRUNCATED` warning automatically

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Values silently truncated with `ok: true` and no warning; agent cannot detect the data loss |
| 1 | Some truncation warnings emitted as prose; not in `warnings[]` array; `FIELD_TRUNCATED` code absent |
| 2 | `warnings[]` includes `FIELD_TRUNCATED` entries with `field`, `original_length`, and `truncated_to` |
| 3 | Schema declares `max_length`/`max_items` for bounded fields; Phase 1 rejects inputs exceeding limits before execution |

**Check:** Pass a value that exceeds the documented field length limit — verify the response includes a `FIELD_TRUNCATED` warning or a `VALIDATION_ERROR` rejection, never silent truncation.

---

### Agent Workaround

**Signature:** `exit 0` with `"ok": true` but the returned field value is shorter than the value sent; array items missing from the created resource

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** After each write returning `ok: true`, compare every returned field value in `data` to the value sent and treat any shortened value as truncation; if that fails, escalate with the command, exit code, stdout, and stderr

**Check `warnings[]` after every write operation; validate field lengths against schema before sending:**

```python
import subprocess, json

def run_and_check_truncation(cmd: list[str], sent_values: dict) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = json.loads(result.stdout)

    if not parsed.get("ok"):
        return parsed

    # Check for truncation warnings
    warnings = parsed.get("warnings", [])
    truncated = [w for w in warnings if w.get("code") == "FIELD_TRUNCATED"]
    if truncated:
        for t in truncated:
            field = t.get("field")
            original = t.get("original_length")
            truncated_to = t.get("truncated_to")
            print(
                f"WARNING: Field '{field}' was truncated from {original} to {truncated_to} chars. "
                "The stored value differs from what was sent."
            )

    # Compare returned values to sent values for fields we care about
    data = parsed.get("data", {})
    for field, sent_val in sent_values.items():
        returned_val = data.get(field)
        if isinstance(sent_val, str) and isinstance(returned_val, str):
            if sent_val != returned_val and len(returned_val) < len(sent_val):
                print(
                    f"POSSIBLE SILENT TRUNCATION: '{field}' sent {len(sent_val)} chars, "
                    f"got back {len(returned_val)} chars — check API field limits."
                )

    return parsed
```

**Pre-validate lengths from schema constraints before sending:**
```python
def validate_lengths(schema_cmd: dict, args: dict) -> None:
    for param in schema_cmd.get("parameters", []):
        name = param.get("name")
        max_len = param.get("max_length")
        if max_len and name in args:
            value = args[name]
            if isinstance(value, str) and len(value) > max_len:
                raise ValueError(
                    f"--{name} exceeds max_length {max_len}: {len(value)} chars"
                )
```

**Limitation:** If the tool silently truncates with no `warnings[]` and returns the truncated value as `ok: true`, the only detection is to compare the returned field value against the sent value — build this comparison into every write operation for fields known to have length limits
