# REQ-O-038: --heartbeat-ms Flag for Long-Running Commands

**Tier:** Opt-In | **Priority:** P1

**Source:** [§60 OS Output Buffer Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) · [§49 Async Job / Polling Protocol Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/49-high-async-job-polling.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST provide `--heartbeat-ms <milliseconds>` (default: `10000`) for commands that may run longer than their timeout. When active, the framework emits a JSON heartbeat object to stdout at the specified interval: `{"status": "running", "heartbeat": true, "elapsed_ms": N, "step": "<current step if known>"}`. Heartbeats MUST be valid JSON lines compatible with JSONL streaming. The heartbeat interval MUST be configurable; `--heartbeat-ms 0` disables heartbeats.

## Acceptance Criteria

- A 25-second command with `--heartbeat-ms 10000` emits at least 2 heartbeat objects before the final result
- Each heartbeat is a valid JSON object parseable independently
- The final response (success or failure) is also a valid JSON object and is distinguishable from heartbeats by `"heartbeat": false` or absence of the `heartbeat` field
- `--heartbeat-ms 0` produces no heartbeat objects

---

## Schema

No dedicated schema type — heartbeat lines are JSONL objects emitted to stdout alongside the final response envelope; they are not fields within it.

---

## Wire Format

```bash
$ tool long-job --heartbeat-ms 10000 --output json
```

Stdout JSONL stream:

```
{"status":"running","heartbeat":true,"elapsed_ms":10012}
{"status":"running","heartbeat":true,"elapsed_ms":20031,"step":"processing batch 2/5"}
{"ok":true,"data":{"processed":5},"error":null,"warnings":[],"meta":{"duration_ms":22418}}
```

The final line (without `"heartbeat": true`) is the response envelope.

---

## Example

Opt-in at the framework level.

```
app = Framework("tool")
app.enable_heartbeat_ms()

# Agent reads heartbeats to confirm the process is alive:
$ tool migrate --heartbeat-ms 5000 --output json | while IFS= read -r line; do
    python3 -c "import json,sys; d=json.loads('$line'); print('alive' if d.get('heartbeat') else 'done')"
  done
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-053](f-053-stdout-unbuffering-in-non-tty-mode.md) | F | Provides: unbuffered stdout ensures heartbeats reach the caller immediately |
| [REQ-F-049](f-049-async-command-handler-enforcement.md) | F | Composes: async commands use heartbeats to signal liveness before job descriptor emission |
| [REQ-O-012](o-012-heartbeat-interval-flag.md) | O | Extends: `--heartbeat-interval` sends plain-text to stderr; this flag sends JSON to stdout |
