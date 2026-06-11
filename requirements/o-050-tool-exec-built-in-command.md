# REQ-O-050: tool exec Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§77 No Batch Command Dispatch](../challenges/02-critical-execution-and-reliability/77-high-no-batch-dispatch.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST provide a built-in `tool exec` command that reads a JSONL stream from stdin and dispatches each line to the matching subcommand **in-process** — no subprocess fork per line. Each line is a `DispatchRequest` with a `_cmd` field (dot-separated subcommand path matching the tool manifest `commands` map), an optional `_opts` object of per-line flag overrides, and any remaining fields forwarded as the `--input` JSON payload to the dispatched command.

Per-line output streams to stdout as JSONL. Each output line is a `ResponseEnvelope` with `_cmd` (echoed from the request) and `_line` (1-based line index) added to `meta`. Errors on individual lines are structured per `ResponseEnvelope.error` and never suppress output for subsequent lines.

The command supports two flags:

- `--ignore-errors`: continue dispatching after a line failure (default: stop at first failure)
- `--dry-run`: forward `dry_run: true` to every dispatched command whose `danger_level` is `"mutating"` or `"destructive"`; commands with `danger_level: "safe"` ignore it

Exit codes:

| Code | Condition |
|------|-----------|
| `0` | All lines dispatched and succeeded |
| `1` | One or more lines produced a non-zero exit |
| `2` | The JSONL stream was malformed (parse error before any dispatch) |

`tool exec` itself declares `danger_level: "safe"` — danger is determined per dispatched line, not at the `exec` call site.

## Acceptance Criteria

- `cat ops.jsonl | tool exec --output jsonl` dispatches all lines in-process and emits one response line per input line to stdout
- Each response line is a valid `ResponseEnvelope` with `_cmd` and `_line` present in `meta`
- Without `--ignore-errors`, dispatch stops at the first failure and exits `1`
- With `--ignore-errors`, dispatch continues past line failures; exit code is still `1` if any line failed
- `--dry-run` is forwarded to every dispatched command that declares `danger_level != "safe"`
- A JSONL parse error on any line emits an error response for that line with `error.code: "DISPATCH_PARSE_ERROR"` and `error.phase: "validation"`; no side effects for that line
- A fully malformed stream (cannot parse any line) exits `2`
- The command is available with zero per-command implementation work once enabled at the framework level

---

## Schema

**Types:** [`dispatch-request.md`](../schemas/dispatch-request.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Each stdin line is a `DispatchRequest`. Each stdout line is a `ResponseEnvelope` extended with `_cmd` and `_line` in `meta`.

---

## Wire Format

```bash
$ cat ops.jsonl | tool exec --ignore-errors --output jsonl
```

Input (stdin, one JSON object per line):
```jsonl
{"_cmd":"account.create","name":"Assets:Bank","open_date":"2024-01-01"}
{"_cmd":"transaction.add","_opts":{"draft":true},"date":"2024-01-15","narration":"Buy BTC"}
{"_cmd":"commodity.create","currency":"INVALID"}
```

Output (stdout, one JSON object per line):
```jsonl
{"_cmd":"account.create","_line":1,"ok":true,"data":{"id":"acct_123"},"error":null,"warnings":[],"meta":{"duration_ms":4}}
{"_cmd":"transaction.add","_line":2,"ok":true,"data":{"id":"txn_456","draft":true},"error":null,"warnings":[],"meta":{"duration_ms":11}}
{"_cmd":"commodity.create","_line":3,"ok":false,"data":null,"error":{"code":"VALIDATION_FAILED","message":"Invalid currency format","retryable":false,"phase":"validation"},"warnings":[],"meta":{"duration_ms":2}}
```

Exit code `1` (one line failed). Without `--ignore-errors`, output stops after the first failed line.

---

## Example

```python
app = Framework("tool")
app.enable_exec()  # registers `tool exec`; zero per-command work required

# Agent generates a plan and streams it in one call:
plan = [
    {"_cmd": "account.create", "name": "Assets:Bank", "open_date": "2024-01-01"},
    {"_cmd": "commodity.create", "currency": "BTC", "name": "Bitcoin"},
    {"_cmd": "transaction.add", "date": "2024-01-15", "narration": "Buy BTC"},
]
payload = "\n".join(json.dumps(op) for op in plan)
result = subprocess.run(
    ["tool", "exec", "--output", "jsonl"],
    input=payload, capture_output=True, text=True,
)
results = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: exit code declarations applied per dispatched line |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Composes: `danger_level` declarations used to route `--dry-run` forwarding |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Composes: `--dry-run` forwarded per-line to declared mutating/destructive commands |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Enforces: each output line is a `ResponseEnvelope` |
| [REQ-O-032](o-032-raw-payload-flag-for-mutating-commands.md) | O | Provides: `--input` flag that `exec` uses to forward per-line payload |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Provides: manifest `commands` map whose dot-path keys are valid `_cmd` values |
| [schemas/dispatch-request.md](../schemas/dispatch-request.md) | Schema | Provides: per-line JSONL input envelope consumed by `tool exec` |
| [guides/batch-dispatch.md](../guides/batch-dispatch.md) | Guide | Provides: design rationale, protocol details, and safe invocation patterns |
