# Guide: Designing a Built-In Batch Dispatch Command

> **The principle:** Any CLI that an agent may call more than once in a session should offer a single `exec` entry point that accepts a JSONL stream and routes each line to the matching subcommand in-process — one invocation, N operations, zero per-record startup cost.

An agent that generates a plan of N operations has a fixed tool-call budget. When N is large and each operation requires a separate process invocation, the budget is consumed before the plan is complete. The agent either truncates the plan or splits it into multiple orchestration steps, both of which add latency, increase context overhead, and risk partial completion. A built-in `exec` command removes this constraint entirely: the agent writes a JSONL file once and streams it in, paying startup cost exactly once regardless of N.

This guide covers when to provide `exec`, how to design the JSONL protocol, what the per-line output should look like, and the invocation patterns agent builders can use today with CLIs that already support it.

---

## When to Provide `exec`

Add `exec` whenever any of these conditions applies:

- The CLI manages stateful records (accounts, transactions, tasks, configurations, users)
- An agent workflow commonly creates, updates, or queries multiple objects per orchestration step
- The CLI is used in ETL pipelines where a CSV or structured file maps one-to-one to commands
- Any individual command accepts a `--input` JSON payload (meaning the command is already batch-friendly by structure)

`exec` is a zero-per-command-cost feature at the framework level. Once the framework dispatches by `_cmd`, every existing command becomes batchable without modification.

---

## The `_cmd` Routing Key

Each input line is a JSON object. The `_cmd` field is the only reserved key the framework consumes; everything else is forwarded as payload.

```jsonl
{"_cmd": "account.create", "name": "Assets:Bank", "open_date": "2024-01-01"}
{"_cmd": "transaction.add", "date": "2024-01-15", "narration": "Buy coffee"}
{"_cmd": "account.list"}
```

`_cmd` uses the same dot-separated path as the tool manifest `commands` map keys. This is not a coincidence: agents discover the available paths from `tool manifest --output json`, then populate `_cmd` directly from that map. The dot-separation mirrors subcommand nesting (`tool account create` → `"account.create"`), so no additional translation layer is needed.

Use underscore-prefixed keys (`_cmd`, `_opts`) to minimize collision with domain field names. An application model that happens to have a `cmd` field would collide with a plain `cmd` key; `_cmd` is a visible signal that this field is routing metadata, not payload.

---

## Per-Line Flag Overrides with `_opts`

`_opts` is an optional object of per-line flag overrides. Boolean `true` emits a bare flag; string or number emits `--flag=value`:

```json
{"_cmd": "transaction.add", "_opts": {"draft": true, "target": "inbox.bc"}, "date": "2024-01-15", "narration": "Buy BTC"}
```

Translates to:

```bash
tool transaction add --draft --target=inbox.bc --input '{"date":"2024-01-15","narration":"Buy BTC"}'
```

This is the mechanism for per-line dry-run, per-line output target, or per-line verbosity. Global flags (passed to `tool exec` itself) apply to the entire stream; `_opts` overrides apply to that line only.

---

## Per-Line Output

Each dispatched line emits one response to stdout. The shape is `ResponseEnvelope` with two additions in `meta`: `_cmd` (echoed from the request) and `_line` (1-based line index in the input stream).

```jsonl
{"_cmd":"account.create","_line":1,"ok":true,"data":{"id":"acct_123"},"error":null,"warnings":[],"meta":{"duration_ms":4}}
{"_cmd":"transaction.add","_line":2,"ok":true,"data":{"id":"txn_456","draft":true},"error":null,"warnings":[],"meta":{"duration_ms":11}}
{"_cmd":"commodity.create","_line":3,"ok":false,"data":null,"error":{"code":"ALREADY_EXISTS","message":"BTC already registered","retryable":false},"warnings":[],"meta":{"duration_ms":2}}
```

The `_line` field is the correlation key. When an agent processes the output stream and a line fails, `_line` maps the failure back to the exact input object without requiring the agent to maintain a parallel counter.

Errors on individual lines never suppress output for succeeding lines. The stream is always one-in, one-out.

---

## Failure Modes and Exit Codes

Three distinct exit codes cover the three meaningful states:

| Exit code | Meaning |
|-----------|---------|
| `0` | All lines dispatched and succeeded |
| `1` | One or more lines produced a non-zero exit |
| `2` | The JSONL stream was malformed (parse error before any dispatch) |

`--ignore-errors` changes `exit 1` behavior: dispatch continues after a line failure and the final exit code is `1` if any line failed (not `0`). It does not change `exit 2` — a malformed stream is a caller error.

`--dry-run` on `exec` is forwarded to every dispatched command that declares `danger_level: "mutating"` or `"destructive"`. Read-only commands (`danger_level: "safe"`) ignore it. This lets an agent validate an entire plan against the live system before committing any mutations.

---

## Safe Invocation Pattern for Agent Builders

Use this pattern for any CLI that supports `exec`. The key decisions: always set `stdin=DEVNULL` on the subprocess itself (the agent's own stdin must not leak into the process), and check `_line` in the response to correlate failures back to input.

```python
import subprocess, json

PIPE_SAFE_BYTES = 32 * 1024  # 32 KB: conservative half of the 64 KB pipe buffer

def exec_batch(cli: list[str], operations: list[dict], ignore_errors: bool = False) -> list[dict]:
    payload = "\n".join(json.dumps(op) for op in operations)
    flags = ["--ignore-errors"] if ignore_errors else []

    if len(payload.encode()) > PIPE_SAFE_BYTES:
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(payload)
            tmp = f.name
        try:
            result = subprocess.run(
                cli + ["exec"] + flags + ["--input-file", tmp, "--output", "jsonl"],
                capture_output=True, text=True,
                stdin=subprocess.DEVNULL,
                timeout=120,
            )
        finally:
            os.unlink(tmp)
    else:
        result = subprocess.run(
            cli + ["exec"] + flags + ["--output", "jsonl"],
            input=payload,
            capture_output=True, text=True,
            timeout=120,
        )

    if result.returncode == 2:
        raise ValueError(f"Malformed JSONL stream: {result.stderr[:200]}")

    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
```

`stdin=DEVNULL` is not optional. Without it, the subprocess inherits the agent's own stdin — any tool that silently falls back to reading stdin will consume it, corrupting the agent's own input stream.

The 32 KB threshold avoids the bidirectional pipe deadlock described in §61: when both the input stream and the output stream are large, both sides fill their pipe buffers and block waiting for the other to drain. Writing the payload to a temp file and passing `--input-file` eliminates the input side of the deadlock.

---

## Ordering Reads Before Writes

When a batch mixes read-only and mutating commands, sort reads first:

```python
def sort_for_safety(operations: list[dict], manifest: dict) -> list[dict]:
    def danger(op):
        cmd_key = op["_cmd"]
        level = manifest["commands"].get(cmd_key, {}).get("danger_level", "mutating")
        return {"safe": 0, "mutating": 1, "destructive": 2}[level]
    return sorted(operations, key=danger)
```

If `exec` stops at the first failure (default behavior), reads complete before any write is attempted. An agent that needs to validate prerequisites before mutating state gets that guarantee for free.

---

## Implementation Checklist for CLI Authors

| Rule | Requirement | What to implement |
|------|-------------|-------------------|
| Built-in `exec` command | REQ-O-050 | Register via `app.enable_exec()`; no per-command work |
| In-process dispatch | REQ-O-050 | Route by `_cmd` through the framework's own command registry — no subprocess per line |
| Structured per-line output | REQ-F-004 · REQ-O-050 | Each output line is a `ResponseEnvelope` with `_cmd` and `_line` in `meta` |
| `--ignore-errors` flag | REQ-O-050 | Continue after line failure; summary exit code still `1` if any line failed |
| `--dry-run` forwarding | REQ-C-004 · REQ-O-050 | Forward to every dispatched command with `danger_level != "safe"` |
| Malformed stream exit 2 | REQ-O-050 | JSONL parse errors emit `DISPATCH_PARSE_ERROR` and exit `2`, not `1` |

---

## Related

| Document | Relationship |
|----------|-------------|
| [§77 No Batch Command Dispatch](../challenges/02-critical-execution-and-reliability/77-high-no-batch-dispatch.md) | Sources: the failure mode this guide addresses |
| [REQ-O-050](../requirements/o-050-tool-exec-built-in-command.md) | Enforces: the `tool exec` built-in that implements this guide's protocol |
| [schemas/dispatch-request.md](../schemas/dispatch-request.md) | Provides: canonical schema for the per-line JSONL input envelope |
| [schemas/response-envelope.md](../schemas/response-envelope.md) | Provides: per-line output shape emitted for each dispatched line |
| [schemas/manifest-response.md](../schemas/manifest-response.md) | Provides: `commands` map whose keys populate `_cmd` |
| [REQ-C-004](../requirements/c-004-destructive-commands-must-support-dry-run.md) | Provides: `--dry-run` declaration that `exec` forwards per-line |
| [REQ-O-032](../requirements/o-032-raw-payload-flag-for-mutating-commands.md) | Provides: `--input` flag that `exec` uses to forward per-line payload |
| [guides/stdin-native-cli.md](stdin-native-cli.md) | Provides: pipe safety patterns used by the invocation examples in this guide |
