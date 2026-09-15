# REQ-O-039: --input-file Flag for Stdin Commands

**Tier:** Opt-In | **Priority:** P1

**Source:** [§61 Bidirectional Pipe Payload Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) · [§50 Stdin Consumption Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST automatically register `--input-file <path>` for any command that declares `stdin_input: true`. When `--input-file` is passed, the framework reads input from the file instead of stdin, bypassing the pipe buffer limit entirely. The file is read in streaming fashion; there is no size limit for file-based input. `--input-file -` is equivalent to stdin (preserving backward compatibility). The framework MUST document that payloads larger than 64KB should use `--input-file` rather than stdin piping.

## Acceptance Criteria

- `tool process --input-file /path/to/large.json` reads from the file, not stdin
- `tool process --input-file -` reads from stdin (equivalent to piping)
- A 10MB file passed via `--input-file` is processed successfully
- A 10MB payload via stdin is rejected with `STDIN_TOO_LARGE` and `hint: "use --input-file"`

---

## Schema

No dedicated schema type — `--input-file` is a behavioral flag that routes input from a file path instead of stdin, with no new wire-format fields.

---

## Wire Format

No wire-format fields — `--input-file` affects input routing only. The response envelope is identical to a successful stdin read.

```bash
$ tool process --input-file ./payload.json --output json
```

```json
{
  "ok": true,
  "data": { "processed": true, "items": 1024 },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 412 }
}
```

---

## Example

Opt-in: automatically registered for commands that declare `stdin_input: true`.

```
register command "process":
  stdin_input: true
  # --input-file is auto-registered by the framework

# For small payloads — stdin is fine:
$ echo '{"items":[1,2,3]}' | tool process

# For large payloads (>64KB) — use --input-file to avoid pipe buffer limit:
$ tool process --input-file ./large-payload.json

# --input-file - explicitly reads from stdin (backward compatibility):
$ cat payload.json | tool process --input-file -
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md) | F | Provides: the `STDIN_TOO_LARGE` error that directs callers to use this flag |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: non-TTY detection governs whether stdin is read at all |
| [REQ-O-006](o-006-stdin-as-id-source.md) | O | Composes: stdin ID source and `--input-file` are complementary stdin patterns |
