> **Part II: Execution & Reliability** | Challenge §77

## 77. No Batch Command Dispatch

**Severity:** High | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

CLIs that lack a batch dispatch command force agents to shell out once per heterogeneous command. An LLM that generates a plan of N operations must invoke the CLI N times, paying process startup cost on every call, saturating the agent's tool-call budget, and losing any ability to express the batch as a single unit.

```bash
# Agent generates 50 operations and must invoke the tool 50 times
tool account create --input '{"name":"Assets:Bank","open_date":"2024-01-01"}'
tool transaction add --input '{"date":"2024-01-15","narration":"Buy BTC","postings":[...]}'
tool commodity create --input '{"currency":"BTC","name":"Bitcoin"}'
# ... 47 more invocations
```

Each invocation spawns a new process, reads config, validates auth, and initializes the framework. For 50 operations the startup overhead alone can exceed total execution time. The agent's tool-call budget — typically 10–20 calls per orchestration step — is exhausted before the plan is half-executed.

**In ETL pipelines, the problem compounds:**

```bash
# CSV → JSONL → one invocation per record
cat transactions.csv | csvjson | while read line; do
    tool transaction add --input "$line"
done
# 10,000 records → 10,000 process spawns
```

### Impact

- Agent tool-call budget exhausted on routine multi-operation plans
- Per-process startup overhead multiplied by N makes large batches impractical
- No cross-item atomicity: partial failure mid-batch has no single resume point
- ETL pipelines shell out per-record rather than streaming to one process

### Solutions

**Built-in `exec` command accepting JSONL from stdin:**

```bash
cat operations.jsonl | tool exec --ignore-errors --output jsonl
```

```jsonl
{"_cmd":"account.create","name":"Assets:Bank","open_date":"2024-01-01"}
{"_cmd":"transaction.add","_opts":{"draft":true},"date":"2024-01-15","narration":"Buy BTC","postings":[...]}
{"_cmd":"commodity.create","currency":"BTC","name":"Bitcoin"}
```

Each line routes to the matching subcommand in-process. Per-line output streams to stdout as JSONL, one `ResponseEnvelope` per input line extended with `_cmd` and `_line` in `meta`.

**Per-line structured output:**

```jsonl
{"_cmd":"account.create","_line":1,"ok":true,"data":{"id":"acct_123"},"error":null,"warnings":[],"meta":{"duration_ms":4}}
{"_cmd":"transaction.add","_line":2,"ok":true,"data":{"id":"txn_456","draft":true},"error":null,"warnings":[],"meta":{"duration_ms":11}}
{"_cmd":"commodity.create","_line":3,"ok":false,"data":null,"error":{"code":"ALREADY_EXISTS","message":"BTC already registered","retryable":false},"warnings":[],"meta":{"duration_ms":2}}
```

**For framework design:**
- `tool exec` is a built-in requiring zero per-command implementation
- Each line is dispatched in-process: no subprocess fork per line
- `--ignore-errors` continues after per-line failures; default stops at first error
- `--dry-run` is forwarded to every dispatched command declaring `danger_level: "mutating"` or `"destructive"`
- Exit code `0` if all lines succeeded; `1` if any line failed; `2` if the JSONL stream was malformed

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No batch dispatch mechanism; agents must shell out once per command |
| 1 | Batch available but spawns a subprocess per line or lacks structured per-line output |
| 2 | In-process dispatch with structured JSONL output per line; exit code reflects overall success |
| 3 | Full `tool exec` with `--ignore-errors`, `--dry-run` forwarding, and `_line` index in per-line output |

**Check:** Pipe three heterogeneous commands as JSONL to `tool exec --output jsonl` — verify in-process dispatch, three structured response lines, and non-zero exit code when any line fails.

---

### Agent Workaround

**Signature:** no `exec` or batch subcommand in `--help`; N operations require N separate invocations each paying startup latency; tool-call budget exhausts mid-plan

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** issue each operation as its own CLI invocation and stop at the first non-zero exit; if that fails, escalate with the command, exit code, stdout, and stderr

**Manually loop when the CLI lacks `exec`:**

```python
import subprocess, json

def batch_dispatch(cli: list[str], operations: list[dict]) -> list[dict]:
    results = []
    for i, op in enumerate(operations):
        op = dict(op)
        cmd_parts = op.pop("_cmd").split(".")
        opts = op.pop("_opts", {})
        flags = [
            f"--{k.replace('_', '-')}" if v is True
            else f"--{k.replace('_', '-')}={v}"
            for k, v in opts.items()
        ]
        result = subprocess.run(
            cli + cmd_parts + flags + ["--input", json.dumps(op), "--output", "json"],
            capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
            timeout=30,
        )
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {"ok": False, "error": {"code": "PARSE_ERROR", "message": result.stderr[:200]}}
        results.append({"_line": i + 1, **parsed})
        if not parsed.get("ok"):
            break
    return results
```

**Limitation:** Without in-process dispatch, each call pays full process startup cost — suitable only for small batches (< 20 operations). For large batches, verify whether individual commands accept `--input-file` and write a temporary JSONL file instead of looping.
