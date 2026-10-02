# REQ-O-004: --format jsonl / --stream Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

For commands that process or return large datasets, the framework MUST support `--stream` (equivalent to `--format jsonl`) which emits one JSON object per line as results are produced, rather than buffering all results before emitting. Commands that support streaming MUST declare `supports_streaming: true`. In streaming mode, pagination metadata MUST be emitted as a final summary line.

Commands that stream by default (see §76) MUST additionally declare `streaming_default: true`. A streaming-default command MUST accept `--no-stream` (equivalent to `--format json`) to return a buffered `ResponseEnvelope` for compatibility with envelope-only consumers. The `streaming_default` field MUST be advertised in the manifest and in `--help` text.

A stream ends with exactly one terminal line. On success it is the summary line (`"_summary": true`). When the command fails after its first line, the terminal line is instead the error `ResponseEnvelope` (`"ok": false`, REQ-F-004), and the process exits with that envelope's `meta.exit_code`. A line holding `"_summary": true` or an `"ok"` boolean beside an `"error"` key is therefore never an item, and neither is a heartbeat line (`"heartbeat": true`, REQ-O-038).

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
- A command that does not declare `supports_streaming: true` emits a warning when `--stream` is passed
- A command that declares `streaming_default: true` emits JSONL without any flags
- Passing `--no-stream` to a streaming-default command returns a valid `ResponseEnvelope`
- The manifest exposes `streaming_default: true` for commands that declare it
- A streaming command that fails after emitting two items emits a third and last line that is a `ResponseEnvelope` with `"ok": false`, no summary line, and exits with that envelope's `meta.exit_code`
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

Each streamed line is a self-contained JSON object using the command's declared item type. The final summary line reuses `ResponseMeta` field names; a failed stream ends with a `ResponseEnvelope` instead. A records consumer declares `CommandEntry.stdin` with `mode: "records"` and `record_schema` in [`manifest-response.json`](../schemas/manifest-response.json); its errors are `ErrorDetail` objects in [`response-envelope.json`](../schemas/response-envelope.json).

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

Piped into a records consumer, that stream fails the consumer on line 3:

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
| [REQ-O-038](o-038-heartbeat-ms-flag-for-long-running-commands.md) | O | Composes: a records consumer skips the producer's heartbeat lines, which are neither records nor terminal lines |
| [§76](../challenges/04-critical-output-and-parsing/76-high-streaming-default-incompatibility.md) | — | Provides: failure mode when `streaming_default` is undeclared |
| [Guide: Streaming vs Envelope](../guides/streaming-vs-envelope.md) | — | Provides: decision criteria for choosing streaming-default vs envelope-default |
