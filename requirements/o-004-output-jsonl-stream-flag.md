# REQ-O-004: --format jsonl / --stream Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

For commands that process or return large datasets, the framework MUST support `--stream` (equivalent to `--format jsonl`) which emits one JSON object per line as results are produced, rather than buffering all results before emitting. Commands that support streaming MUST declare `supports_streaming: true`. In streaming mode, pagination metadata MUST be emitted as a final summary line.

Commands that stream by default (see §76) MUST additionally declare `streaming_default: true`. A streaming-default command MUST accept `--no-stream` (equivalent to `--format json`) to return a buffered `ResponseEnvelope` for compatibility with envelope-only consumers. The `streaming_default` field MUST be advertised in the manifest and in `--help` text.

A stream ends with exactly one terminal line. On success it is the summary line (`"_summary": true`). When the command fails after its first line, the terminal line is instead the error `ResponseEnvelope` (`"ok": false`, REQ-F-004), and the process exits with that envelope's `meta.exit_code`. A line holding `"_summary": true` or an `"ok"` boolean beside an `"error"` key is therefore never an item, and neither is a heartbeat line (`"heartbeat": true`, REQ-O-038).

**Numbered streams.** A stream MAY number its item lines with the reserved key `_seq` so an agent can detect a dropped line. A stream that uses it puts `_seq` on every item line: `1` on the first and one more on each next line. Heartbeat lines and the terminal line carry no `_seq`. Its summary line carries `"_count": N`, where N is the number of item lines, and an error terminal envelope carries `meta.items_emitted`: the last `_seq` emitted, `0` when the stream failed before its first item line. An agent that reads a last `_seq` lower than `_count` or `meta.items_emitted` missed lines. `_seq` is reserved like `_summary`: a line's `_seq` is framework metadata, never part of the item's data, so a command whose item type has its own `_seq` field MUST NOT number its stream. A records consumer removes `_seq` from a line before it validates and hands over the record. Numbering is optional: a stream without `_seq` keeps its meaning, and an agent reads its lines as before.

**Mutating streams.** A streaming command declares `danger_level` `safe` or `mutating` (REQ-C-002). The framework MUST refuse to register a streaming command with `danger_level: "destructive"`: a stream cannot ask confirmation for each action it takes (REQ-O-021). A stream with `danger_level: "mutating"` reports what it did event by event, not once per run:

- Every item line carries its own top-level `effect` (REQ-C-003): what that event did. The framework validates each event's `effect` as it validates a single response's
- The summary line carries `effects`, an object that maps each effect value that occurred to the number of events reporting it (`{"created": 2, "noop": 1}`). Its counts sum to the number of item lines; a stream with no items has `"effects": {}`
- When a mutating stream offers `--dry-run`, the flag covers the whole stream. Every event reports a `would_*` effect (`would_noop` for one that would change nothing) and none mutates, the summary line carries `"dry_run": true`, and a stream that fails ends on an error envelope with `meta.dry_run: true` (the field REQ-O-048 defines). One run never mixes live and `would_*` effects
- A stream has no idempotency replay: one stored result cannot stand in for a sequence of events. A streaming mutating command MUST NOT accept `--idempotency-key`, and the framework refuses to register one that does (REQ-C-007)
- A mutating stream that fails after an event with a live effect other than `noop` ends on an error envelope with `retryable: false`, because side effects occurred. The item lines already emitted tell the agent which events completed
- When the command answers buffered (without `--stream`, or with `--no-stream` on a streaming-default command), the envelope's `data` is the array of events, each with its own `effect`, and `meta.effects` carries the per-effect counts (with `meta.dry_run` in dry-run mode)
- The audit log (REQ-O-030) records one entry per run, never one per event, with the per-effect counts in `effects`

**Records consumers.** A command that reads such a stream from another command declares `stdin_input: "records"` with a record type; the manifest shows it as `CommandEntry.stdin` with `mode: "records"` and `record_schema` (ManifestResponse 3.8). The framework reads the stream through line mode (REQ-F-054, per-line cap, no total cap), skips blank lines and heartbeat lines (`"heartbeat": true`, REQ-O-038), and classifies every other line in order:

- The summary line ends the input. The framework reads nothing after it and hands the handler no record for it
- An error envelope (`"ok": false`) ends the run with exit `1` and error code `UPSTREAM_FAILED`. `context` carries `line` (1-based), `upstream` (the upstream `error` object, with the consumer's own secret redaction applied), and `upstream_exit_code` (the envelope's `meta.exit_code`). The upstream object is another process's output, so the context carries `_source: "external"` and `_trusted: false` and the upstream's strings are masked (REQ-F-035); `line`, `upstream_exit_code`, `upstream.code`, and `upstream.retryable` are never masked
- Any other line is one record: a JSON object that MUST validate against the declared record type. A line that is not a JSON object, or fails validation, ends the run with exit `1` and error code `RECORD_INVALID`, with `context.line` and, when one field is at fault, `context.field`
- End of stdin before a terminal line ends the run with exit `1` and error code `UPSTREAM_INCOMPLETE`, with `context.line` (the last line read) and `context.records` (records handed to the handler). The producer was killed or exited without finishing its stream

All four failures happen after the handler has started, so they exit `1`, not `2` (REQ-F-002), and carry `retryable: false` and `phase: "execution"`: the consumer may already have acted on earlier records. Input read through `--input-file <path>` is a finished file, not a live producer: a summary line still ends it, and end of file without one ends the input normally instead of failing. `--input-file -` is stdin and follows the stdin rule.

## Acceptance Criteria

- `--stream` causes output to begin appearing before the command completes
- Each line of streaming output is a valid, self-contained JSON object
- On success, the final line of streaming output is a summary object containing `pagination` metadata
- A numbered stream of three items puts `"_seq": 1`, `2`, and `3` on its item lines, none on a heartbeat line, and `"_count": 3` on its summary line
- A numbered stream that fails after two items ends on an error envelope with `meta.items_emitted: 2`; one that fails before its first item has `meta.items_emitted: 0`
- A records consumer fed a numbered stream hands the handler records without `_seq`
- A command that does not declare `supports_streaming: true` emits a warning when `--stream` is passed
- A command that declares `streaming_default: true` emits JSONL without any flags
- Passing `--no-stream` to a streaming-default command returns a valid `ResponseEnvelope`
- The manifest exposes `streaming_default: true` for commands that declare it
- A streaming command that fails after emitting two items emits a third and last line that is a `ResponseEnvelope` with `"ok": false`, no summary line, and exits with that envelope's `meta.exit_code`
- Registering a streaming command with `danger_level: "destructive"` raises a registration error
- Registering a streaming command with `danger_level: "mutating"` that accepts `--idempotency-key` raises a registration error
- A mutating stream that creates two resources and finds one unchanged emits three item lines, each with its own `effect`, and a summary line with `"effects": {"created": 2, "noop": 1}`
- The same stream with `--dry-run` changes nothing, every item line has a `would_*` effect, and the summary line carries `"dry_run": true` and `"effects": {"would_create": 2, "would_noop": 1}`
- A mutating stream run with `--dry-run` that fails after its first item ends on an error envelope with `meta.dry_run: true`
- A mutating stream that fails after an item with `effect: "created"` ends on an error envelope with `retryable: false`
- A records consumer fed two items and a summary line hands the handler two records and exits `0`
- A records consumer fed one item and an error envelope on line 2 exits `1` with `error.code: "UPSTREAM_FAILED"`, `context.line: 2`, `context.upstream.code` equal to the upstream error's code, `context._trusted: false`, and `context.upstream_exit_code` equal to its `meta.exit_code`
- A records consumer fed two items and then end of stdin, with no terminal line, exits `1` with `error.code: "UPSTREAM_INCOMPLETE"`, `context.line: 2`, and `context.records: 2`
- A records consumer fed a line that is not a JSON object, or a record missing a required field, exits `1` with `error.code: "RECORD_INVALID"` and that line's number in `context.line`
- A records consumer given `--input-file <path>` whose file has two items and no summary line hands the handler two records and exits `0`
- Every one of these consumer errors carries `retryable: false`
- A records consumer fed an item, a heartbeat line, an item, and a summary line hands the handler two records and exits `0`

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) (`CommandEntry.streaming_default`) · [`response-envelope.md`](../schemas/response-envelope.md) (`ResponseMeta` field names on the summary line)

Each streamed line is a self-contained JSON object using the command's declared item type. The final summary line reuses `ResponseMeta` field names, including `effects` and `dry_run` on a mutating stream (ResponseEnvelope 2.2); a failed numbered stream's error envelope carries `meta.items_emitted` (ResponseEnvelope 2.3); a failed stream ends with a `ResponseEnvelope` instead. A records consumer declares `CommandEntry.stdin` with `mode: "records"` and `record_schema` in [`manifest-response.json`](../schemas/manifest-response.json); its errors are `ErrorDetail` objects in [`response-envelope.json`](../schemas/response-envelope.json).

---

## Wire Format

```bash
$ tool list-deployments --stream
```

```
{"id": "d1", "status": "complete", "target": "prod"}
{"id": "d2", "status": "running", "target": "staging"}
{"id": "d3", "status": "failed", "target": "dev"}
{"_summary": true, "total": 3, "duration_ms": 280}
```

The same stream, numbered:

```jsonl
{"id": "d1", "status": "complete", "target": "prod", "_seq": 1}
{"id": "d2", "status": "running", "target": "staging", "_seq": 2}
{"status": "running", "heartbeat": true, "elapsed_ms": 10012}
{"id": "d3", "status": "failed", "target": "dev", "_seq": 3}
{"_summary": true, "total": 3, "_count": 3, "duration_ms": 280}
```

With an unsupported command:

```bash
$ tool deploy --target staging --stream
```

```json
{
  "ok": false,
  "data": null,
  "error": { "code": "STREAMING_NOT_SUPPORTED", "message": "deploy does not support --stream" },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 3 }
}
```

Streaming-default command — JSONL without flags; envelope via `--no-stream`:

```bash
$ tool list-events
{"id": "e1", "type": "deploy", "ts": 1700000001}
{"id": "e2", "type": "rollback", "ts": 1700000042}
{"_summary": true, "total": 2, "duration_ms": 18}

$ tool list-events --no-stream
{"ok": true, "data": [{"id": "e1", ...}, {"id": "e2", ...}], "error": null, "warnings": [], "meta": {"total": 2, "duration_ms": 18}}
```

A stream that fails mid-way ends on the error envelope, not a summary line:

```jsonl
{"id": "d1", "status": "complete", "target": "prod"}
{"id": "d2", "status": "running", "target": "staging"}
{"ok": false, "data": null, "error": {"code": "UNAVAILABLE", "message": "Deployment API returned 503", "retryable": true}, "warnings": [], "meta": {"exit_code": 12, "duration_ms": 1840}}
```

Numbered, the same failure tells the agent where the stream stopped:

```jsonl
{"id": "d1", "status": "complete", "target": "prod", "_seq": 1}
{"id": "d2", "status": "running", "target": "staging", "_seq": 2}
{"ok": false, "data": null, "error": {"code": "UNAVAILABLE", "message": "Deployment API returned 503", "retryable": true}, "warnings": [], "meta": {"exit_code": 12, "duration_ms": 1840, "items_emitted": 2}}
```

A mutating stream puts an `effect` on each event and counts them on the summary line:

```bash
$ tool sync-users --source users.csv --stream
```

```jsonl
{"id": "u1", "effect": "created"}
{"id": "u2", "effect": "noop"}
{"id": "u3", "effect": "created"}
{"_summary": true, "total": 3, "effects": {"created": 2, "noop": 1}, "duration_ms": 412}
```

The same run with `--dry-run` changes nothing:

```jsonl
{"id": "u1", "effect": "would_create"}
{"id": "u2", "effect": "would_noop"}
{"id": "u3", "effect": "would_create"}
{"_summary": true, "total": 3, "effects": {"would_create": 2, "would_noop": 1}, "dry_run": true, "duration_ms": 37}
```

Piped into a records consumer, the failed `list-deployments` stream above fails the consumer on line 3:

```bash
$ tool list-deployments --stream | tool annotate --format json
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_FAILED",
    "message": "Upstream stream failed on line 3: Deployment API returned 503",
    "retryable": false,
    "phase": "execution",
    "context": {
      "_source": "external",
      "_trusted": false,
      "line": 3,
      "upstream": { "code": "UNAVAILABLE", "message": "Deployment API returned 503", "retryable": true },
      "upstream_exit_code": 12
    }
  },
  "warnings": [],
  "meta": { "exit_code": 1, "duration_ms": 1852 }
}
```

A producer killed before its terminal line:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UPSTREAM_INCOMPLETE",
    "message": "Stdin ended after line 2 without a _summary line",
    "retryable": false,
    "phase": "execution",
    "context": { "line": 2, "records": 2 }
  },
  "warnings": [],
  "meta": { "exit_code": 1, "duration_ms": 31 }
}
```

---

## Example

Commands opt in by declaring `supports_streaming: true` at registration time.

```
app = Framework("tool")

register command "list-deployments":
  supports_streaming: true
  stream_seq: true   # optional: _seq on each item line, _count on the summary line
  # items emitted via framework stream() call as they arrive

# tool list-deployments --stream  →  JSONL lines as items arrive
# tool list-deployments --format jsonl  →  identical behavior

register command "annotate":
  stdin_input: "records"
  record_type: Deployment   # {id, status, target}; published as stdin.record_schema
  # handler iterates records as they arrive; the framework stops at _summary

# tool list-deployments --stream | tool annotate  →  one record per item
# tool annotate --input-file deployments.ndjson   →  end of file ends the input
```

---

## Related

| Requirement / Source | Tier | Relationship |
|----------------------|------|--------------|
| [REQ-O-001](o-001-output-format-flag.md) | O | Specializes: `--stream` is equivalent to `--format jsonl` with incremental emission |
| [REQ-O-003](o-003-limit-and-cursor-pagination-flags.md) | O | Composes: pagination summary emitted as the final stream line |
| [REQ-F-053](f-053-stdout-unbuffering-in-non-tty-mode.md) | F | Provides: stdout unbuffering required for streaming to work |
| [REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md) | F | Provides: line mode and its per-line cap, through which a records consumer reads the stream |
| [REQ-F-065](f-065-pipeline-exit-code-propagation.md) | F | Composes: REQ-F-065 covers pipelines the framework runs; `UPSTREAM_FAILED` and `UPSTREAM_INCOMPLETE` surface an upstream failure in a pipeline the caller's shell runs |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: a failed stream ends with the standard error envelope |
| [REQ-F-035](f-035-external-data-trust-tagging.md) | F | Enforces: the `UPSTREAM_FAILED` context is tagged external and its upstream strings are masked |
| [REQ-O-039](o-039-input-file-flag-for-stdin-commands.md) | O | Composes: `--input-file <path>` feeds a records consumer a finished file, so end of file ends the input |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Consumes: `danger_level` decides whether a stream reports effects and whether it may register at all |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Specializes: a mutating stream carries `effect` on each event and counts them in `effects` |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Specializes: a streaming mutating command takes no `--idempotency-key` |
| [REQ-O-048](o-048-destructive-commands-default-dry-run.md) | O | Consumes: the `dry_run` field a dry-run stream puts on its summary line |
| [REQ-O-030](o-030-opt-in-audit-log.md) | O | Composes: a stream is one audit entry with its per-effect counts |
| [REQ-O-038](o-038-heartbeat-ms-flag-for-long-running-commands.md) | O | Composes: a records consumer skips the producer's heartbeat lines, which are neither records nor terminal lines and carry no `_seq` |
| [§76](../challenges/04-critical-output-and-parsing/76-high-streaming-default-incompatibility.md) | — | Provides: failure mode when `streaming_default` is undeclared |
| [Guide: Streaming vs Envelope](../guides/streaming-vs-envelope.md) | — | Provides: decision criteria for choosing streaming-default vs envelope-default |
