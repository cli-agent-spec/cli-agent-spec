# REQ-O-012: --heartbeat-interval Flag

**Tier:** Opt-In | **Priority:** P2

**Source:** [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

For long-running commands, the framework MUST provide `--heartbeat-interval <seconds>` as a standard flag. When set, the framework emits periodic progress messages to stderr at the specified interval, formatted as `[<elapsed>s] <status_message>`. Commands declare their progress reporting by calling the framework's `progress()` API; the framework handles the throttling and formatting. This prevents the caller from mistaking a long-running command for a hang.

## Acceptance Criteria

- `--heartbeat-interval 5` causes a progress message to stderr every 5 seconds
- The heartbeat message includes elapsed time and the most recent status from the command's `progress()` call
- Heartbeat messages are plain text, never JSON (they are diagnostic, not structured output)
- With `--quiet`, heartbeat messages are suppressed

---

## Schema

No dedicated schema type — heartbeat messages are plain-text diagnostic output to stderr, not structured JSON fields.

---

## Wire Format

No wire-format fields — heartbeat messages go to stderr and do not appear in the JSON response envelope.

Stderr output during a long-running command:

```
[5s] Connecting to database...
[10s] Running migration batch 1/10...
[15s] Running migration batch 2/10...
```

---

## Example

Opt-in at the framework level; commands call `progress()` to supply the status message.

```
app = Framework("tool")
app.enable_heartbeat_interval()

register command "migrate":
  handler:
    for batch in batches:
      ctx.progress(f"Running migration batch {i}/{total}...")
      run_batch(batch)

# Agent invocation with 5-second heartbeats to stderr:
$ tool migrate --heartbeat-interval 5 2>./heartbeat.log
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Composes: heartbeats help distinguish running-long from hung (pre-timeout) |
| [REQ-O-038](o-038-heartbeat-ms-flag-for-long-running-commands.md) | O | Extends: `--heartbeat-ms` emits JSON heartbeats to stdout; this flag emits plain-text to stderr |
| [REQ-F-039](f-039-duration-tracking-in-response-meta.md) | F | Composes: `meta.duration_ms` in the final response complements the elapsed time in heartbeats |
