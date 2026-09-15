> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §43

## 43. Tool Output Result Size Unboundedness

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Critical | **Time:** High | **Context:** Critical

### The Problem

Challenge #5 (Pagination & Large Output) addresses paginated *list* commands that return many items. This challenge addresses a different problem: a single tool invocation or command that returns one item but that item itself is arbitrarily large — for example, a file's contents, a log excerpt, a search result body, or a database record with large text fields.

Unlike list pagination (where the fix is clear: add `--limit` and `cursor`), single-result unboundedness has no standard solution. The agent cannot know in advance how large the result will be, and many commands have no way to truncate a single result meaningfully (you cannot return half a file, for example).

In MCP specifically, a single `tools/call` response can contain a text body of arbitrary size. There is no `max_output_bytes` field in the call, no `Content-Length`, and no `Content-Range` equivalent. A command that reads a 10MB log file returns all 10MB in a single JSON response, filling (or overflowing) the agent's context window entirely.

```python
# Agent invokes a file-reading tool, not knowing the file size
result = await mcp_client.call_tool("read_file", {"path": "/var/log/app.log"})
# result.content[0].text might be 50,000 lines = 400,000 tokens
# Entire context window consumed; agent cannot reason about anything else
```

```bash
# CLI equivalent: no output limit
$ my-tool get-record --id 12345 --format json
# Returns a record with a "description" field containing 200KB of text
# Agent receives all 200KB as stdout; must include it all in context for parsing
```

Pydantic's weakness note identifies this as "no standard paginated response model" — but the problem is deeper: there is no standard way to express *output size constraints* at the schema level, so agents cannot even request a truncated form before invocation.

### Impact

- Context window overflow: a single large result can consume the entire remaining context window, preventing further reasoning
- Forced truncation: agents that truncate large outputs mid-stream may corrupt structured data (e.g., cutting JSON in the middle)
- Token spend: even if the context window is large, reading 400K tokens of log output at token prices is expensive
- No recovery path: unlike list pagination (where the agent can request the next page), there is no "next chunk" for a single large result
- Agents cannot pre-flight the size before calling the tool

### Solutions

**For CLI/tool authors:**
```bash
# Provide a --max-length or --truncate flag
my-tool get-record --id 12345 --max-length 10000 --truncate-mode head

# Output envelope should signal truncation
{
  "ok": true,
  "data": {"id": "12345", "description": "First 10000 chars..."},
  "meta": {"truncated": true, "total_bytes": 204800, "returned_bytes": 10000,
           "truncation_hint": "Use --offset and --max-length for subsequent chunks"}
}
```

**For framework design:**
- Implement a default output size limit per command (e.g., 50KB of text content) with the excess truncated and `meta.truncated: true` set
- Provide a `--max-output` flag (injected automatically on all commands) that the agent can set to control output size
- For large string fields in responses, automatically truncate at a configurable `max_field_length` (default: 10,000 chars) and add a `"_truncated": true` marker on the field
- In MCP tool definitions, expose `maxOutputBytes` as a tool annotation so clients can pre-negotiate output size
- Schema should declare `"max_output_bytes": 51200` as a tool property, allowing agents to assess expected output size before calling

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Single-result commands return unbounded output; no `meta.truncated`; no `--max-output` flag; agent has no pre-flight size check |
| 1 | `--max-length` flag exists on some commands; no `meta.truncated` signal when truncation occurs |
| 2 | `meta.truncated: true` and `meta.total_bytes` present when truncation occurs; `--max-output` or `--max-length` accepted |
| 3 | Default output limit enforced per command; `max_output_bytes` declared in schema; large string fields auto-truncated with `_truncated: true` marker |

**Check:** Pass a known large resource (e.g., a log file >50KB) to any read command — verify the response includes `meta.truncated: true` and `meta.total_bytes` rather than returning all content.

---

### Agent Workaround

**Signature:** single invocation returns very large stdout (tens of KB to MB) with no `meta.truncated` marker; output overflows context or arrives cut mid-structure

**Tier:** B (one observable check, then one command)

**Estimate output size before processing; use `--max-output` to bound large results; always check `meta.truncated`:**

```python
import subprocess, json, os

MAX_OUTPUT_TOKENS = 8000   # conservative context budget
MAX_OUTPUT_BYTES = MAX_OUTPUT_TOKENS * 4  # ~4 bytes/token

result = subprocess.run(
    ["tool", "get-record", "--id", record_id,
     "--max-output", str(MAX_OUTPUT_BYTES),
     "--output", "json"],
    capture_output=True, text=True,
)

output_bytes = len(result.stdout.encode())
approx_tokens = output_bytes // 4
if approx_tokens > MAX_OUTPUT_TOKENS:
    raise RuntimeError(
        f"Output too large (~{approx_tokens} tokens). "
        "Use --fields to select specific fields or --max-output to truncate."
    )

parsed = json.loads(result.stdout)
if parsed.get("meta", {}).get("truncated"):
    total = parsed["meta"].get("total_bytes", "unknown")
    print(
        f"WARNING: Output was truncated ({total} total bytes). "
        "Use --offset and --max-output for subsequent chunks if needed."
    )
```

**Request only needed fields to reduce output size:**
```python
result = subprocess.run(
    ["tool", "get-record", "--id", record_id,
     "--fields", "id,name,status",   # only what the agent needs
     "--output", "json"],
    capture_output=True, text=True,
)
```

**Limitation:** If the tool has no `--max-output` or `--fields` flag and returns unbounded single-result output, the only option is to post-process the raw output — extract just the needed fields using `jq` or Python dict access and discard the rest before storing in context
