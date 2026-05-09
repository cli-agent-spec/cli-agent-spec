# Guide: Choosing Between Streaming and Envelope Output

> **The principle:** Use a `ResponseEnvelope` when the response is only meaningful as a whole; use streaming (JSONL) when partial results are independently actionable and the command may outlast the agent's liveness budget.

Most agent runtimes call CLI tools by spawning a subprocess, blocking until it exits, then reading all of stdout as a single string. They do not consume output line-by-line in real time. This shapes every output-mode decision: the question is not "how does the output arrive?" but "what happens to the agent if the process takes too long, or if stdout is parsed with `json.loads()`?"

---

## The Default: JSON Response Envelope

The `ResponseEnvelope` schema (`{"ok": bool, "data": ..., "error": ..., "warnings": [], "meta": {...}}`) is the canonical default for all commands. Its `ok`/`error` semantics only make sense when the response is received as a whole object. An envelope parsed as JSONL is a single valid line; a JSONL stream parsed as a JSON envelope throws `JSONDecodeError`.

**Use envelope-default when:**

- The command completes in under ~5 seconds
- The result is only meaningful when complete (a created resource, a diff, a validation outcome)
- Partial results have no actionable value — a truncated `{"data": [...]` tells the agent nothing
- You want compatibility with all agent runtimes, including those that do `json.loads(stdout)`

---

## When to Use Streaming Default

**Use streaming-default (`streaming_default: true`) when:**

| Signal | Rationale |
|--------|-----------|
| Command takes >5 seconds under normal conditions | Agent timeout may fire before completion; partial results are better than nothing |
| Results are produced and usable one-at-a-time | Each JSONL line is a complete, actionable item |
| Result set is unbounded or user-specified (see §43) | A single envelope over thousands of items exceeds agent context window |
| The command is inherently a stream (`logs`, `watch`, `follow`) | These have no natural "done" point where an envelope would form |

**The key criterion:** can the agent act on a single result before all results are available? If yes, streaming-default is appropriate. If the results only make sense together (e.g., a multi-step validation report), envelope-default is safer.

---

## The `streaming_default: true` Declaration

A command that streams by default MUST declare this explicitly so the framework can advertise it in `--help`, in the manifest, and in schema discovery. Without declaration, agents have no machine-readable signal to choose the right parser before invoking the command.

```
register command "list-events":
  streaming_default: true
  supports_streaming: true   # implied, but explicit is clearer

# tool list-events            → JSONL (default)
# tool list-events --no-stream → ResponseEnvelope (buffered)
# tool list-events --output json → identical to --no-stream
```

`--no-stream` (or `--output json`) MUST produce a valid `ResponseEnvelope`, not raw JSONL wrapped in a JSON string. This gives envelope-only consumers a reliable fallback.

---

## The Heartbeat Middle Ground

For commands that are long-running but produce a single, unified result (a migration report, a deployment summary), streaming-default is the wrong choice — the result only makes sense as a whole. The correct approach is envelope-default with heartbeats:

1. Keep the default output as `ResponseEnvelope`
2. Enable `--heartbeat-ms` (REQ-O-038) so the agent receives proof-of-life JSON lines during the wait
3. The final output is still a single `ResponseEnvelope` that `json.loads()` parses cleanly

This decouples liveness signaling from output format. Heartbeat lines are safe to receive by agents that read stdout line-by-line AND by agents that collect all output at exit (heartbeat lines are valid JSONL; the final envelope line is also valid JSONL).

---

## Decision Table

| Command type | Duration | Partial results actionable? | Recommended default |
|-------------|----------|----------------------------|---------------------|
| CRUD operation | <1s | No | `ResponseEnvelope` |
| Status / health check | <1s | No | `ResponseEnvelope` |
| Query / list (bounded) | <5s | Each item independently | `ResponseEnvelope` + `--stream` opt-in |
| Query / list (unbounded) | Variable | Each item independently | `streaming_default: true` |
| Long-running job (single result) | >5s | No | `ResponseEnvelope` + heartbeats |
| Log tail / watch / follow | Unbounded | Each event independently | `streaming_default: true` |
| AI / token-streaming generation | >5s | Each token/chunk independently | `streaming_default: true` |

---

## Related

| Document | Relationship |
|----------|-------------|
| [§76 Streaming-Default JSONL Incompatibility](../challenges/04-critical-output-and-parsing/76-high-streaming-default-incompatibility.md) | Provides: the failure mode this guide prevents |
| [§60 OS Output Buffer Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) | Provides: why envelope-default commands still need unbuffered stdout |
| [§5 Pagination & Large Output](../challenges/04-critical-output-and-parsing/05-high-pagination.md) | Provides: the unbounded-size failure mode that motivates streaming-default |
| [REQ-O-004](../requirements/o-004-output-jsonl-stream-flag.md) | Enforces: `--stream` / `streaming_default` declaration contract |
| [REQ-O-038](../requirements/o-038-heartbeat-ms-flag-for-long-running-commands.md) | Provides: heartbeat mechanism for long-running envelope-default commands |
| [REQ-F-053](../requirements/f-053-stdout-unbuffering-in-non-tty-mode.md) | Provides: stdout unbuffering required for streaming or heartbeats to work |
| [schemas/response-envelope.md](../schemas/response-envelope.md) | Provides: canonical envelope schema for non-streaming output |
