# REQ-O-004: --output jsonl / --stream Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Critical

---

## Description

For commands that process or return large datasets, the framework MUST support `--stream` (equivalent to `--output jsonl`) which emits one JSON object per line as results are produced, rather than buffering all results before emitting. Commands that support streaming MUST declare `supports_streaming: true`. In streaming mode, pagination metadata MUST be emitted as a final summary line.

Commands that stream by default (see §76) MUST additionally declare `streaming_default: true`. A streaming-default command MUST accept `--no-stream` (equivalent to `--output json`) to return a buffered `ResponseEnvelope` for compatibility with envelope-only consumers. The `streaming_default` field MUST be advertised in the manifest and in `--help` text.

## Acceptance Criteria

- `--stream` causes output to begin appearing before the command completes
- Each line of streaming output is a valid, self-contained JSON object
- The final line of streaming output is a summary object containing `pagination` metadata
- A command that does not declare `supports_streaming: true` emits a warning when `--stream` is passed
- A command that declares `streaming_default: true` emits JSONL without any flags
- Passing `--no-stream` to a streaming-default command returns a valid `ResponseEnvelope`
- The manifest exposes `streaming_default: true` for commands that declare it

---

## Schema

No dedicated schema type — this requirement governs streaming output format without adding new wire-format fields. Each line is a self-contained JSON object using the command's declared item type. The final summary line reuses `ResponseMeta` field names.

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
  "meta": { "duration_ms": 3 }
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

---

## Example

Commands opt in by declaring `supports_streaming: true` at registration time.

```
app = Framework("tool")

register command "list-deployments":
  supports_streaming: true
  # items emitted via framework stream() call as they arrive

# tool list-deployments --stream  →  JSONL lines as items arrive
# tool list-deployments --output jsonl  →  identical behavior
```

---

## Related

| Requirement / Source | Tier | Relationship |
|----------------------|------|--------------|
| [REQ-O-001](o-001-output-format-flag.md) | O | Specializes: `--stream` is equivalent to `--output jsonl` with incremental emission |
| [REQ-O-003](o-003-limit-and-cursor-pagination-flags.md) | O | Composes: pagination summary emitted as the final stream line |
| [REQ-F-053](f-053-stdout-unbuffering-in-non-tty-mode.md) | F | Provides: stdout unbuffering required for streaming to work |
| [§76](../challenges/04-critical-output-and-parsing/76-high-streaming-default-incompatibility.md) | — | Provides: failure mode when `streaming_default` is undeclared |
| [Guide: Streaming vs Envelope](../guides/streaming-vs-envelope.md) | — | Provides: decision criteria for choosing streaming-default vs envelope-default |
