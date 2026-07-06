# REQ-F-054: Stdin Payload Size Cap with --input-file Fallback

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§61 Bidirectional Pipe Payload Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST enforce a maximum stdin read size (default: 65536 bytes, configurable via `TOOL_MAX_STDIN_BYTES`). If a stdin read would exceed this limit, the framework MUST exit with code 2 and a structured error directing the caller to use `--input-file <path>` instead. The `--input-file` flag MUST be automatically registered by the framework for any command that declares stdin input. This prevents bidirectional pipe deadlocks caused by the UNIX kernel pipe buffer limit.

## Acceptance Criteria

- A stdin payload of 65537 bytes exits with code 2 and `error.code: "STDIN_TOO_LARGE"`
- The error includes `hint` pointing to `--input-file`
- A command that declares `stdin_input: true` automatically has `--input-file` registered as a flag
- A payload of 65535 bytes is accepted and processed normally

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

On oversized stdin, the framework exits with code 2 (`ARG_ERROR`) and emits a structured error with `code: "STDIN_TOO_LARGE"` and a `hint` field.

---

## Wire Format

Oversized stdin rejection:

```bash
$ echo "$(python3 -c "print('x'*65537)")" | tool process --output json
```

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "STDIN_TOO_LARGE",
    "message": "Stdin payload exceeds 65536-byte limit",
    "hint": "Write the payload to a file and use --input-file <path> instead",
    "context": { "received_bytes": 65537, "limit_bytes": 65536 }
  },
  "warnings": [],
  "meta": { "phase": "validation", "duration_ms": 1 }
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
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: stdin handling is only active when stdin is not a TTY |
| [REQ-O-039](o-039-input-file-flag-for-stdin-commands.md) | O | Provides: `--input-file` is the fallback the framework directs callers to use |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: the rejection error uses the standard response envelope |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Composes: stdin cap check is part of Phase 1 (validation), before any side effects |
