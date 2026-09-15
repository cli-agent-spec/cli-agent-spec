> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §35

## 35. Agent Hallucination Input Patterns

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

AI agents make systematically different input errors than human operators. Human typos are random character substitutions; agent hallucinations follow predictable patterns rooted in training data. A CLI designed to be robust against human error (spelling corrections, range checks) will nonetheless accept agent hallucinations silently.

The jpoehnelt rubric uniquely identifies these agent-specific hallucination patterns:
- **Path traversal segments**: agents sometimes generate `../` prefixes when constructing file paths, especially when combining a base directory variable with a relative sub-path
- **Percent-encoded segments**: agents trained on URL handling may percent-encode resource identifiers (e.g., passing `my%2Fresource` as a resource ID where `/` is a literal part of the expected format)
- **Embedded query parameters**: agents confuse REST URL patterns with CLI argument patterns, generating arguments like `users?active=true` or `repos/main#readme`
- **Embedded newlines and null bytes**: agents sometimes include `\n`, `\r\n`, or `\x00` in string arguments when generating multi-line values
- **Overly-literal type coercion**: agents pass `"null"`, `"undefined"`, `"None"`, `"NaN"`, `"Infinity"` as string values where they intend empty/absent/numeric-overflow semantics

These patterns pass standard type validation (`type=str` accepts all of them) but produce semantically invalid operations that may execute partially before failing obscurely.

```bash
# Agent hallucination: percent-encoded project name
my-tool get-project --name "acme%2Fwidgets"
# Tool happily looks up "acme%2Fwidgets" (literal), finds nothing, returns 404-equivalent
# Agent doesn't understand why — the entity clearly exists in its context

# Agent hallucination: path traversal in output path
my-tool export --output "../../etc/cron.d/backdoor"
# Passes Path validation (it's a valid path); writes to unintended location
```

### Impact

- Silent mis-execution: the command runs, returns exit 0 or a non-obvious error, and the agent reasons incorrectly about the result
- Security: path traversal + write operations can escape sandboxed working directories
- Retry waste: agent retries with the same hallucinated input pattern, consuming tokens and time before a human notices
- Different failure modes than human-facing errors — existing error messages ("file not found") do not help the agent self-correct because the underlying cause is the encoding mismatch, not a missing file
- Validation designed for human typos (e.g., Levenshtein "did you mean?") is irrelevant for these patterns

### Solutions

**Rejecting traversal patterns:**
```python
import re, urllib.parse

def validate_resource_id(value: str) -> str:
    # Reject path traversal
    if '..' in value.split('/'):
        raise ValueError(f"Path traversal detected in resource ID: {value!r}")
    # Reject percent-encoding (when not expected)
    decoded = urllib.parse.unquote(value)
    if decoded != value:
        raise ValueError(f"Percent-encoded characters in resource ID: {value!r} (decoded: {decoded!r})")
    # Reject embedded query params
    if '?' in value or '#' in value:
        raise ValueError(f"Embedded URL metacharacters in: {value!r}")
    return value
```

**Error message for agent self-correction:**
```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "field": "name",
    "message": "Resource ID contains percent-encoded characters. Pass the literal value without URL-encoding.",
    "input": "acme%2Fwidgets",
    "suggestion": "acme/widgets"
  }
}
```

**For framework design:**
- Implement an `agent_hardening=True` flag on `Argument` / `Option` declarations that enables the full Axis 5 level 2 check set by default
- For string arguments representing names, IDs, or paths: reject `../`, `./`, `%XX` sequences, `?`, `#`, null bytes, and the string literals `"null"`, `"undefined"`, `"None"` by default (override with `allow_unsafe=True`)
- Error messages for these rejections must explain *why* the value was rejected in terms an LLM can act on — not just "invalid value."
- Include the decoded/normalized form in the error `suggestion` field so the agent can self-correct without a retry
- Consider jpoehnelt's "agent is not a trusted operator" as a default security posture: apply stricter validation to agent-invoked CLIs than to human-interactive ones

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Standard type validation only; path traversal, percent-encoding, and embedded query params accepted silently |
| 1 | Some rejection of `../`; no handling of `%XX`, `?`/`#`, or literal null values; errors say "invalid value" with no actionable context |
| 2 | Rejects path traversal and percent-encoding with structured error; `input` and `suggestion` fields in error response |
| 3 | Full Axis 5 level 2 check set enabled; `agent_hardening` flag on argument declarations; `corrected_input` in every rejection error |

**Check:** Pass `--name "acme%2Fwidgets"` to any command that accepts a resource name — verify the response includes `"code": "VALIDATION_ERROR"`, the original input, and a `suggestion` showing the decoded form.

---

### Agent Workaround

**Signature:** not-found or invalid-value error for a resource that exists; the passed value contains `%2F`, `?`, `#`, `../`, or literal `null`/`undefined`

**Tier:** B (one observable check, then one command)

**Normalize LLM-generated values before passing to the CLI; retry once with the tool's `suggestion` on rejection:**

```python
import subprocess, json, urllib.parse

def normalize_agent_value(value: str) -> str:
    """Normalize common LLM hallucination patterns."""
    # Decode percent-encoding (most common LLM mistake)
    decoded = urllib.parse.unquote(value)
    # Remove embedded query params
    decoded = decoded.split("?")[0].split("#")[0]
    # Replace literal nulls with empty string
    if decoded in ("null", "undefined", "None", "NaN"):
        decoded = ""
    return decoded

def call_with_normalization(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = json.loads(result.stdout)
    if parsed.get("ok"):
        return parsed

    error = parsed.get("error", {})
    if error.get("code") == "VALIDATION_ERROR":
        suggestion = error.get("suggestion")
        if suggestion:
            # Retry once with the tool's suggested correction
            corrected_cmd = [
                suggestion if arg == error.get("input") else arg
                for arg in cmd
            ]
            retry = subprocess.run(corrected_cmd, capture_output=True, text=True)
            return json.loads(retry.stdout)

    return parsed
```

**Limitation:** Normalization handles the most common patterns but cannot know every tool's ID format rules — always check for a `suggestion` in `VALIDATION_ERROR` responses and use it as the authoritative correction before generating a new value
