> **Part I: Output & Parsing** | Challenge §5

## 5. Pagination & Large Output

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Critical

### Impact

- Unbounded output exhausts agent context window and pipe buffers, causing the call to fail or the agent to process incomplete data
- No truncation indicator means the agent believes it has all records when it has only the first page
- Page-number pagination requires the agent to track state across calls; cursor-based pagination does not

### The Problem

Commands that return large datasets in a single response create multiple problems: the output may be too large to parse, may exceed pipe buffers, or may contain more data than the agent can process in its context.

**Unbounded output:**
```bash
$ tool list-logs
[returns 50,000 lines of JSON]
# Pipe buffer overflows, agent context overflows, parsing degrades
```

**No indication that results are truncated:**
```bash
$ tool list-users
{"users": [...100 items...]}
# Is this all users? Or first 100? Agent can't tell.
```

**Pagination that requires stateful session:**
```bash
$ tool list-users --page 2
# Requires knowing that page 1 was fetched first
# No cursor-based alternative
```

### Solutions

**Always indicate truncation and total:**
```json
{
  "ok": true,
  "data": [...],
  "pagination": {
    "total": 50000,
    "returned": 100,
    "truncated": true,
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true
  }
}
```

**Cursor-based pagination (stateless):**
```bash
tool list-users --limit 100 --cursor "eyJpZCI6MTAwfQ=="
```

**Streaming output (JSONL):**
```bash
tool list-logs --output jsonl --stream
# Emits one JSON object per line
# Agent can process incrementally
{"timestamp": "...", "level": "error", "message": "..."}
{"timestamp": "...", "level": "info",  "message": "..."}
```

**Default sensible limits:**
```bash
tool list-users           # default: --limit 20
tool list-users --limit 0 # explicit: no limit
```

**For framework design:**
- All list commands have `--limit` (default: 20) and `--cursor`
- Response always includes `pagination` metadata
- `--stream` flag for JSONL output when processing large sets

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | List commands return all results unbounded; no `has_more`, no `total`, no `next_cursor` |
| 1 | `--limit` flag exists but response contains no pagination metadata; agent cannot tell if results were truncated |
| 2 | `pagination` object in response with `total`, `has_more`, `next_cursor`; `--cursor` accepted for subsequent pages |
| 3 | Default limit applied automatically (≤100); `--stream` / JSONL mode available; `truncated: true` field present whenever output is cut |

**Check:** Run a list command without `--limit` on a dataset with more than 100 items — verify the response includes `has_more: true` and a `next_cursor` value.

---

### Agent Workaround

**Signature:** unbounded stdout (thousands of lines) from a list command; or a round-number item count with no `has_more`, `total`, or `next_cursor` field

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Run `tool <list-args> --limit 50 --output json` and treat the result as a partial subset; if that fails, escalate with the command, exit code, stdout, and stderr

**Always specify `--limit` and loop with `next_cursor` until `has_more` is false:**

```python
def paginate(base_cmd: list[str], limit: int = 50) -> list:
    all_items = []
    cursor = None

    while True:
        cmd = [*base_cmd, "--limit", str(limit), "--output", "json"]
        if cursor:
            cmd += ["--cursor", cursor]

        result = subprocess.run(cmd, capture_output=True, text=True)
        parsed = json.loads(result.stdout)
        data = parsed.get("data") or parsed.get("items") or []
        all_items.extend(data if isinstance(data, list) else [data])

        pagination = parsed.get("pagination") or parsed.get("meta", {})
        if not pagination.get("has_more"):
            break
        cursor = pagination.get("next_cursor")
        if not cursor:
            break  # no cursor provided — cannot paginate further

    return all_items
```

**Limitation:** If the tool provides no `has_more` or `next_cursor` field, the agent cannot determine whether results are complete — always apply an explicit `--limit` to prevent unbounded output, and document that results may be a subset of the full dataset
