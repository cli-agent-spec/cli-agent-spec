> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §67

## 67. Agent-Generated Input Syntax Rejection

**Source:** Antigravity `07_schema_and_discoverability.md` (RA)

**Severity:** High | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** Low

### The Problem

LLMs frequently generate near-valid structured input that strict parsers reject: JSON with trailing commas, inline comments, unquoted keys, or minor whitespace variations that are valid in JSON5 or YAML but invalid in strict JSON. A tool that accepts `--config '{"key": "value"}'` but rejects `--config '{"key": "value",}'` (trailing comma) fails immediately. The agent must then debug a parse error in its own generated content — spending reasoning tokens on a meta-level failure rather than the actual task.

```bash
# LLM generates JSON with trailing comma (very common LLM output pattern):
$ tool create --config '{"name": "prod", "region": "us-east-1",}'
Error: Invalid JSON: Unexpected token } at position 38
# Agent must now reason about JSON syntax, not the task

# LLM includes a comment (natural for LLM to explain its reasoning):
$ tool create --config '{"name": "prod" /* production environment */}'
Error: Invalid JSON: Unexpected token / at position 16

# LLM generates unquoted keys (also common):
$ tool create --config '{name: "prod", region: "us-east-1"}'
Error: Invalid JSON: Unexpected token n at position 1

# Each error requires a round trip: agent must reformat and retry
```

The pattern repeats across configuration flags, filter expressions, template strings, and any structured input the agent must generate.

### Impact

- Round trip cost: agent must diagnose parse error, reformat input, retry
- Reasoning tokens wasted on JSON syntax rather than the actual task
- High frequency: LLMs naturally produce JSON5-ish output, especially when generating longer JSON objects
- Cascading: multiple retries before the agent produces perfectly strict JSON

### Solutions

**Accept JSON5 / forgiving JSON for all structured inputs:**
```python
import json5  # pip install json5
config = json5.loads(user_input)
# Accepts: trailing commas, comments, unquoted keys, single quotes
```

**Normalize before parsing:**
```python
import re
def normalize_json(s):
    s = re.sub(r',\s*([}\]])', r'\1', s)   # remove trailing commas
    s = re.sub(r'//.*?$', '', s, flags=re.M)  # remove line comments
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)  # remove block comments
    return json.loads(s)
```

**Surface clear correction in error:**
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "Trailing comma at line 1, position 38.",
    "corrected_input": "{\"name\": \"prod\", \"region\": \"us-east-1\"}",
    "hint": "Remove trailing comma after last key-value pair."
  }
}
```

**For framework design:**
- Framework MUST use a forgiving JSON parser (JSON5 or equivalent) for all `--config`, `--filter`, `--data`, and `--raw-payload` flag inputs
- When strict JSON is required (e.g., for schema validation), the framework normalizes the input before validation and emits the corrected form in the error if validation fails
- The `corrected_input` field in parse errors enables agents to retry with minimal reasoning

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Strict JSON only; trailing commas, comments, and unquoted keys all rejected with non-structured parse errors |
| 1 | Parse errors include line/position info but no `corrected_input`; agent must fix JSON manually |
| 2 | `INVALID_JSON` structured error includes `corrected_input` and `hint` for common LLM patterns |
| 3 | Framework uses JSON5 or forgiving parser for all structured input flags; normalization applied before validation |

**Check:** Pass `--config '{"key": "value",}'` (trailing comma) — verify the tool either accepts it or returns `{"code": "INVALID_JSON", "corrected_input": "{\"key\": \"value\"}"}`.

---

### Agent Workaround

**Signature:** immediate rejection with `Invalid JSON` or `Unexpected token` at a position matching a trailing comma, comment, or unquoted key in generated input

**Tier:** B (one observable check, then one command)

**Normalize LLM-generated JSON before passing to the tool; use `corrected_input` from parse errors on retry:**

```python
import subprocess, json, re

def normalize_json_input(s: str) -> str:
    """Remove common LLM-generated JSON5 patterns that strict parsers reject."""
    # Remove trailing commas before closing braces/brackets
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    # Remove line comments
    s = re.sub(r'//[^\n]*', '', s)
    # Remove block comments
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)
    # Validate the result is actually JSON
    json.loads(s)   # raises JSONDecodeError if still invalid
    return s

def run_with_json_input(cmd: list[str], json_flag: str, payload: str) -> dict:
    # Normalize before sending
    try:
        normalized = normalize_json_input(payload)
    except json.JSONDecodeError:
        normalized = payload  # send as-is, let tool give error with corrected_input

    result = subprocess.run(
        [*cmd, json_flag, normalized],
        capture_output=True, text=True,
    )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Non-JSON response: {result.stdout[:200]}")

    if not parsed.get("ok"):
        error = parsed.get("error", {})
        if error.get("code") == "INVALID_JSON":
            corrected = error.get("corrected_input")
            if corrected:
                # Retry once with the tool's corrected form
                retry = subprocess.run(
                    [*cmd, json_flag, corrected],
                    capture_output=True, text=True,
                )
                return json.loads(retry.stdout)

    return parsed
```

**Limitation:** JSON normalization removes trailing commas and comments but cannot fix structural errors (unbalanced braces, wrong types) — when `corrected_input` is absent in the error, the agent must regenerate the JSON payload from scratch rather than attempting to patch the malformed input
