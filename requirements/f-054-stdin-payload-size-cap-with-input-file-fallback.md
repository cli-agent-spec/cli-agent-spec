# REQ-F-054: Stdin Payload Size Cap with --input-file Fallback

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§61 Bidirectional Pipe Payload Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST enforce a maximum stdin read size (default: 65536 bytes, configurable via `TOOL_MAX_STDIN_BYTES`) on buffered stdin. If a stdin read would exceed this limit, the framework MUST exit with code 2 and a structured error directing the caller to use `--input-file <path>` instead. The `--input-file` flag MUST be automatically registered by the framework for any command that declares stdin input. This prevents bidirectional pipe deadlocks caused by the UNIX kernel pipe buffer limit.

Stdin is buffered unless the command declares line mode. Buffered stdin (`stdin_input: true`) is read whole before the handler runs. A command that consumes a stream one line at a time declares line mode instead (`stdin_input: "lines"`, or `"records"` for typed records under REQ-O-004): the framework reads nothing before the handler runs and hands it one line at a time as it asks, so nothing accumulates and there is no total cap. Each line is capped instead (default: 1048576 bytes, line terminator excluded; a command may declare a different cap at registration). A line over the cap ends the run with exit `1` and error code `LINE_TOO_LARGE`, carrying the 1-based line number in `context.line`. The exit is `1`, not `2`, because the handler has already started and may have acted on earlier lines; REQ-F-002 reserves `2` for failures before any side effect. Line mode is safe from the §61 deadlock only when a separate writer feeds stdin while stdout drains, as in a shell pipeline; a caller that writes stdin and reads stdout from one thread still uses `--input-file`.

`--input-file <path>` on a line-mode command reads the file as lines, with the same per-line cap and no total cap; `--input-file -` reads stdin as lines. The manifest declares each command's mode and cap in `CommandEntry.stdin` (ManifestResponse 3.8).

## Acceptance Criteria

- A stdin payload of 65537 bytes exits with code 2 and `error.code: "STDIN_TOO_LARGE"`
- The error includes `hint` pointing to `--input-file`
- A command that declares `stdin_input: true` automatically has `--input-file` registered as a flag
- A payload of 65535 bytes is accepted and processed normally
- On a command that declares `stdin_input: "lines"`, 300 lines of 320 bytes each (96000 bytes in total) piped to stdin are all handed to the handler, and the command exits `0`
- On a line-mode command, the handler receives line 1 before the producer writes line 2
- On a line-mode command with the default cap, a 1048577-byte third line exits `1` with `error.code: "LINE_TOO_LARGE"`, `error.retryable: false`, and `error.context.line: 3`, after lines 1 and 2 reached the handler
- `tool <cmd> --input-file lines.ndjson` on a line-mode command applies the same per-line cap and reads a file larger than 65536 bytes
- `TOOL_MAX_STDIN_BYTES` does not change the per-line cap, and a declared per-line cap does not change the buffered cap
- The manifest's `CommandEntry.stdin.mode` is `"buffered"` for `stdin_input: true` and `"lines"` for `stdin_input: "lines"`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md) · [`manifest-response.json`](../schemas/manifest-response.json) (`CommandEntry.stdin`)

On oversized buffered stdin, the framework exits with code 2 (`ARG_ERROR`) and emits a structured error with `code: "STDIN_TOO_LARGE"` and a `hint` field. On an oversized line in line mode, it exits with code 1 (`GENERAL_ERROR`) and emits `code: "LINE_TOO_LARGE"` with `context.line` and `context.limit_bytes`. `CommandEntry.stdin` declares `mode` with `max_bytes` (buffered) or `max_line_bytes` (lines and records).

---

## Wire Format

Oversized stdin rejection:

```bash
$ echo "$(python3 -c "print('x'*65537)")" | tool process --format json
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "STDIN_TOO_LARGE",
    "message": "Stdin payload exceeds 65536-byte limit",
    "hint": "Write the payload to a file and use --input-file <path> instead",
    "phase": "validation",
    "context": { "received_bytes": 65537, "limit_bytes": 65536 }
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 1 }
}
```

Oversized line in line mode:

```bash
$ { echo '{"id":"a1"}'; echo '{"id":"a2"}'; python3 -c "print('x'*1048577)"; } | tool tag --format json
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "LINE_TOO_LARGE",
    "message": "Stdin line 3 exceeds the 1048576-byte line limit",
    "retryable": false,
    "phase": "execution",
    "context": { "line": 3, "limit_bytes": 1048576 }
  },
  "warnings": [],
  "meta": { "exit_code": 1, "duration_ms": 9 }
}
```

The manifest declares the mode and its cap in `CommandEntry.stdin`:

```json
{
  "stdin": { "mode": "lines", "max_line_bytes": 1048576 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework enforces the cap during stdin reading at bootstrap, before the command handler runs.

```
# Automatic flag registration — command author declares stdin_input only:
register command "process":
  stdin_input: true
  # --input-file is auto-registered by the framework

# Framework enforces the cap; large payloads must use --input-file:
$ echo "$LARGE_JSON" | tool process      # → STDIN_TOO_LARGE if > 65536 bytes
$ tool process --input-file payload.json  # → accepted, no size limit

# Line mode: the handler reads one line at a time; each line is capped, the stream is not
register command "tag":
  stdin_input: "lines"
  max_line_bytes: 1048576   # the default; declare a different cap here

$ tool list-securities --format jsonl | tool tag   # any number of lines
$ tool tag --input-file securities.ndjson          # same per-line cap, from a file
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: stdin handling is only active when stdin is not a TTY |
| [REQ-O-039](o-039-input-file-flag-for-stdin-commands.md) | O | Provides: `--input-file` is the fallback the framework directs callers to use |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: the rejection error uses the standard response envelope |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Composes: the buffered stdin cap check is part of Phase 1 (validation), before any side effects; a line-mode cap fires during execution |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Enforces: an oversized line exits `1`, not `2`, because the handler has already started |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Extends: `records` mode reads a REQ-O-004 stream through line mode and ends it on the `_summary` line |
