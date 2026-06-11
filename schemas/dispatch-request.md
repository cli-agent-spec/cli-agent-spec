# Schema: DispatchRequest

**File:** [`dispatch-request.json`](dispatch-request.json)

> **Used by:** [REQ-O-050](../requirements/o-050-tool-exec-built-in-command.md)

Per-line JSONL envelope consumed by the built-in `exec` command. Routes to a subcommand by `_cmd`, applies per-line flag overrides from `_opts`, and forwards remaining fields as the `--input` JSON payload to the dispatched command.

---

## DispatchRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_cmd` | string | yes | Dot-separated subcommand path matching a key in the tool manifest `commands` map |
| `_opts` | object | no | Per-line flag overrides. Boolean `true` emits a bare flag; string or number emits `--flag=value` |
| *(remaining)* | any | no | Forwarded verbatim as the `--input` JSON payload to the dispatched command |

`_cmd` pattern: `^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$` — lowercase hyphen-separated segments joined by dots.

---

## Examples

**Minimal — read-only command, no opts, no payload:**
```json
{"_cmd": "account.list"}
```

**With payload fields only:**
```json
{"_cmd": "account.create", "name": "Assets:Bank", "open_date": "2024-01-01"}
```

**With per-line flag overrides:**
```json
{"_cmd": "transaction.add", "_opts": {"draft": true, "target": "inbox.bc"}, "date": "2024-01-15", "narration": "Buy BTC", "postings": [...]}
```

**Full JSONL batch stream (three lines):**
```jsonl
{"_cmd": "account.create", "name": "Assets:Bank", "open_date": "2024-01-01"}
{"_cmd": "transaction.add", "_opts": {"draft": true}, "date": "2024-01-15", "narration": "Buy BTC"}
{"_cmd": "commodity.create", "currency": "BTC", "name": "Bitcoin"}
```

---

## Common mistakes

**Slash-separated path instead of dot:**
```json
{"_cmd": "account/create"}
```
Use `"account.create"` — path segments are dot-joined, not slash-joined.

**Payload nested under a key:**
```json
{"_cmd": "account.create", "input": {"name": "Assets:Bank"}}
```
Flatten payload fields to the top level; the framework strips `_cmd` and `_opts` and forwards the remainder as `--input`.

**Boolean opt as a string:**
```json
{"_opts": {"draft": "true"}}
```
Use `true` (boolean). The string `"true"` is forwarded as the flag value (`--draft=true`), not as a bare flag (`--draft`).

**`_cmd` segment starting with a digit or uppercase:**
```json
{"_cmd": "Account.Create"}
```
All segments must be lowercase and start with a letter.

---

## Agent interpretation

- `_cmd` keys map 1:1 to the `commands` map in `ManifestResponse` — discover available paths via `tool manifest --output json`
- A missing or malformed `_cmd` emits a line-level error with `error.code: "DISPATCH_PARSE_ERROR"` and `error.phase: "validation"` — no side effects for that line
- `_opts` overrides are merged with global flags; a per-line `dry_run: true` overrides a global `--no-dry-run`
- Fields other than `_cmd` and `_opts` are passed verbatim as `--input` — they must match the target command's declared input schema

---

## Coding agent notes

- Generate valid `_cmd` values from `tool manifest --output json | jq -r '.data.commands | keys[]'`
- Validate payload fields against the target command's `output_schema` before submitting the batch — a validation error caught pre-flight costs nothing; one discovered at line 500 of 1000 wastes the first 499
- Sort lines so `danger_level: "safe"` read operations precede writes — if dispatch stops on first failure, reads complete before any mutation begins
- The `_line` field in each response corresponds to the 1-based line index in the request stream; use it to correlate failures back to the input

---

## Implementation notes

- `additionalProperties: true` is intentional — remaining fields are the payload, not schema violations
- `_cmd` and `_opts` use the underscore prefix to minimize collision with common domain field names (e.g. `name`, `date`, `id`)
- Frameworks must strip `_cmd` and `_opts` before forwarding the object as `--input` to the dispatched command
- The pattern constraint on `_cmd` deliberately excludes uppercase and underscores to enforce Unix subcommand naming conventions (see the [Unix Naming Conventions guide](../guides/unix-naming-conventions.md))

---

## Related

| Document | Relationship |
|----------|-------------|
| [REQ-O-050](../requirements/o-050-tool-exec-built-in-command.md) | Consumes: defines the `exec` command that reads this type |
| [schemas/response-envelope.md](response-envelope.md) | Provides: per-line output envelope shape emitted for each dispatched line |
| [schemas/manifest-response.md](manifest-response.md) | Provides: `commands` map whose keys are valid `_cmd` values |
| [§77 No Batch Command Dispatch](../challenges/02-critical-execution-and-reliability/77-high-no-batch-dispatch.md) | Sources: the failure mode this schema addresses |
| [guides/batch-dispatch.md](../guides/batch-dispatch.md) | Provides: design rationale and safe invocation patterns for this protocol |
