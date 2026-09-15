> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §59

## 59. High-Entropy String Token Poisoning

**Source:** Gemini `02_output_context.md` (RA)

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** High | **Time:** Low | **Context:** High

### The Problem

JWTs, API keys, UUIDs, base64 blobs, and cryptographic hashes in tool output consume hundreds of LLM tokens each — yet provide zero useful signal to the agent. A single `Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...` in a debug dump wastes 200–400 tokens on an opaque string the agent cannot interpret. Over a session with dozens of tool calls, high-entropy fields silently consume a significant fraction of the context budget.

```bash
$ tool auth token --show
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImlhdCI6MTcxMDAwMDAwMCwiZXhwIjoxNzEwMDAzNjAwfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "expires_at": "2024-03-11T15:00:00Z"
}
# The JWT consumes ~300 tokens. The agent only needed "expires_at".
```

Worse: the same high-entropy strings appear across multiple tool responses (resource IDs, session tokens, correlation IDs), each adding wasteful repetition to the context window.

### Impact

- Context budget eroded silently by opaque strings the agent cannot reason about
- Long tokens increase per-call API cost directly
- Repeated high-entropy fields across multiple calls fill context with noise
- Agents may attempt to reason about or pattern-match JWT segments, wasting reasoning tokens

### Solutions

**Auto-mask high-entropy fields in structured output:**
```json
{
  "token": "[JWT: expires 2024-03-11T15:00:00Z, sub=user_123]",
  "token_raw": "<available via: tool auth token --show --unmask>"
}
```

**Schema marks fields as `high_entropy: true`:**
```json
{ "name": "token", "type": "string", "high_entropy": true, "mask_in_output": true }
```

**Framework detects high-entropy strings automatically:**
- Strings matching `^[A-Za-z0-9+/]{40,}={0,2}$` (base64) or JWT pattern (`xxx.yyy.zzz`) are masked unless `--unmask` is passed
- Instead of the raw value, output: entropy type, meaningful metadata extracted from the payload (expiry, subject), and the flag to retrieve the raw value

**For framework design:**
- Framework MUST provide a `high_entropy` field type with automatic masking in non-`--unmask` mode
- The mask replacement MUST include the semantic metadata from the string (JWT: expiry + claims summary; UUID: just the ID truncated; API key: first 8 chars + `...`)
- `--unmask` flag explicitly opts into showing raw high-entropy values

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | JWTs, API keys, and base64 blobs returned verbatim in all output; no masking; high token cost per call |
| 1 | Some fields marked sensitive and omitted; no semantic replacement showing expiry or subject |
| 2 | High-entropy fields replaced with semantic summaries (e.g., `[JWT: expires 2024-03-11, sub=user_123]`); `--unmask` available |
| 3 | `high_entropy: true` declared in schema; automatic detection of base64/JWT patterns; masking applied by default without explicit declaration |

**Check:** Run `tool auth token --show --output json` and verify the `token` field contains a semantic summary (not the full JWT), with the full value accessible via `--unmask`.

---

### Agent Workaround

**Signature:** stdout contains long opaque strings: JWT segments starting `eyJ`, base64 blobs, hex hashes; hundreds of tokens per field with no readable content

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Extract only the needed field, e.g. `tool auth token --show --output json | jq '.data.expires_at'`, and discard the raw token; if that fails, escalate with the command, exit code, stdout, and stderr

**Extract only the semantic metadata the agent needs; request `--unmask` only when the raw value is operationally required:**

```python
import subprocess, json, base64, re

def decode_jwt_claims(token: str) -> dict:
    """Extract claims from a JWT without verification — for metadata only."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        # Pad base64 to multiple of 4
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        return {"sub": claims.get("sub"), "exp": claims.get("exp")}
    except Exception:
        return {}

# When the tool returns a raw JWT, extract only what the agent needs
result = subprocess.run(
    ["tool", "auth", "token", "--show", "--output", "json"],
    capture_output=True, text=True,
)
parsed = json.loads(result.stdout)
token = parsed.get("data", {}).get("token", "")

if token.startswith("eyJ"):
    # It's a raw JWT — extract only the expiry
    claims = decode_jwt_claims(token)
    expiry = claims.get("exp")
    print(f"Token expiry: {expiry} (not storing full JWT in context)")
    # Store only the expiry and whether we have a token; not the token itself
    parsed["data"]["token"] = f"[JWT: exp={expiry}]"
    parsed["data"]["token_available"] = True
```

**Limitation:** If the tool returns raw JWTs or API keys without masking and there is no `--unmask` flag (meaning they are always returned in full), extract only the fields the agent needs and discard the high-entropy value immediately after use — do not store it in variables that persist across many tool calls
