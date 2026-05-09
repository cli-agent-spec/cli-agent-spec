> **Part IV: Output & Parsing** | Challenge §76

## 76. Streaming-Default JSONL Incompatibility

**Severity:** High | **Frequency:** Situational | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Low | **Context:** Medium

### The Problem

Most agent runtimes collect all stdout after process exit and parse it with `json.loads()`. When a command emits JSONL by default (one JSON object per line), two distinct failures occur:

**Case 1 — Hard parse error:** The agent calls `json.loads(stdout)` on multi-line output and gets a `JSONDecodeError`. The error message names a character position, not the cause, so the agent cannot tell whether the command failed, returned a non-JSON format, or switched wire formats.

```bash
$ tool list-events
{"id": "e1", "type": "deploy", "ts": 1700000001}
{"id": "e2", "type": "rollback", "ts": 1700000042}
{"id": "e3", "type": "alert", "ts": 1700000099}

# Agent:
result = json.loads(stdout)
# → JSONDecodeError: Extra data: line 2 column 1 (char 49)
# Agent reads: "command produced invalid JSON"
# Actual issue: JSONL is not JSON
```

**Case 2 — Silent truncation:** The agent uses a JSON parser that stops after the first valid object (common in streaming-aware runtimes). It receives one item, treats it as the complete result, and proceeds — silently discarding the rest.

```bash
$ tool list-events
{"id": "e1", "type": "deploy", "ts": 1700000001}   ← agent parses this as the full response
{"id": "e2", "type": "rollback", "ts": 1700000042}  ← silently dropped
{"id": "e3", "type": "alert", "ts": 1700000099}     ← silently dropped

# Agent believes: one event exists
# Reality: three events exist; rollback and alert are invisible
```

Neither failure produces an `"ok": false` envelope. The agent has no structured signal to understand what went wrong or that the output format changed.

The problem is compounded when JSONL is adopted without declaring `streaming_default: true` in the manifest — the agent has no machine-readable way to choose the right parser before invoking the command.

### Impact

- Agent misclassifies a format mismatch as a command error, triggering unnecessary retries
- Silent truncation passes downstream logic silently — one item is processed where N were expected
- No structured error envelope means the agent cannot distinguish JSONL output from a broken command
- Inconsistency with other commands in the same tool (most return envelope; this one returns JSONL) breaks agent assumptions built up over previous calls
- Without `streaming_default: true` in the manifest, automated agent setup cannot warn or adapt in advance

### Solutions

**Declare `streaming_default: true` in the manifest when a command streams by default:**

```
register command "list-events":
  streaming_default: true
  supports_streaming: true
```

The framework then advertises JSONL as the default in `--help` and in the `manifest` output, giving agents a schema-level signal before invocation.

**Provide `--no-stream` / `--output json` as a compatibility escape:**

A streaming-default command MUST accept `--no-stream` (or `--output json`) and return a buffered `ResponseEnvelope`. This gives envelope-only consumers a reliable fallback without requiring them to switch to a JSONL parser.

```bash
$ tool list-events --no-stream
{
  "ok": true,
  "data": [
    {"id": "e1", "type": "deploy", "ts": 1700000001},
    {"id": "e2", "type": "rollback", "ts": 1700000042},
    {"id": "e3", "type": "alert", "ts": 1700000099}
  ],
  "error": null,
  "warnings": [],
  "meta": {"total": 3, "duration_ms": 42}
}
```

**Emit a format preamble as the first JSONL line (optional enhancement):**

```json
{"_format": "jsonl", "_schema": "EventEntry", "_version": 1}
{"id": "e1", "type": "deploy", "ts": 1700000001}
```

A preamble line lets an agent detect JSONL immediately and switch parsers before consuming data.

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Command emits JSONL by default; no declaration in manifest; no `--no-stream` flag |
| 1 | `--no-stream` flag exists and produces `ResponseEnvelope`; no manifest declaration |
| 2 | `streaming_default: true` declared in manifest; `--no-stream` available |
| 3 | `streaming_default: true` in manifest; `--no-stream` returns valid `ResponseEnvelope`; `--help` text explicitly states JSONL default |

**Check:** Run the command without any flags; pipe stdout to `python3 -c "import sys,json; json.loads(sys.stdin.read())"` — a score ≥ 1 requires either clean parse (envelope default) or a `--no-stream` flag that produces clean parse.

---

### Agent Workaround

**Probe the manifest first; fall back to heuristic JSONL detection:**

```python
import subprocess, json

def parse_output(stdout: str) -> list[dict] | dict:
    stripped = stdout.strip()
    if not stripped:
        return {}

    # Try JSON envelope first (common case)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Fall back to JSONL
    lines = [l for l in stripped.splitlines() if l.strip()]
    try:
        objects = [json.loads(l) for l in lines]
        # Filter out preamble lines
        return [o for o in objects if not o.get("_format")]
    except json.JSONDecodeError as e:
        raise ValueError(f"stdout is neither JSON nor valid JSONL: {e}") from e

# Preferred: check manifest before invoking
manifest = json.loads(
    subprocess.run(["tool", "--manifest"], capture_output=True, text=True).stdout
)
cmd_meta = next(
    (c for c in manifest.get("commands", []) if c["name"] == "list-events"), {}
)
if cmd_meta.get("streaming_default"):
    result = subprocess.run(["tool", "list-events", "--no-stream"], ...)
else:
    result = subprocess.run(["tool", "list-events"], ...)
```

**Limitation:** Without `streaming_default: true` in the manifest, the agent has no advance signal that JSONL is the default. The heuristic fallback (try JSON, then JSONL) recovers from Case 1 (hard parse error) but cannot recover from Case 2 (first-line-only parsers that silently truncate)
