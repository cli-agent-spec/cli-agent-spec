# REQ-F-003: JSON Output Mode Auto-Activation

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MUST automatically activate structured JSON output when stdout is not a TTY, or when the `CI` environment variable is set to any non-empty value, or when `NO_COLOR` is set. Command authors MUST NOT need to check for these conditions themselves; the framework handles format selection. When JSON mode is active, stdout MUST contain only valid JSON; all prose MUST be routed to stderr.

## Acceptance Criteria

- When `isatty(stdout) == false`, output is valid JSON without any additional configuration
- When `CI=true`, output is valid JSON regardless of TTY state
- A command author who calls only the framework's `output()` function never produces invalid JSON in non-TTY contexts
- `python -c "import json,sys; json.load(sys.stdin)"` succeeds on every line of stdout in non-TTY mode

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

No additional fields — the requirement governs format-selection logic. Once JSON mode is active, all output conforms to `ResponseEnvelope`.

---

## Wire Format

When stdout is not a TTY (or `CI` is set), the framework automatically wraps output in the standard envelope with no command-author action:

```json
{
  "ok": true,
  "data": { "id": "job-7", "status": "queued" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 18 }
}
```

No wire-format fields are added by this requirement — it activates the envelope unconditionally in non-TTY contexts.

---

## Example

Framework-Automatic: no command author action needed. The framework detects the execution context at startup and selects the output format before any command handler runs.

```
# TTY context (human terminal)
$ tool status
● job-7  queued  (human-readable prose to stdout)

# Non-TTY context (pipe / agent / CI)
$ tool status | cat
{"ok":true,"data":{"id":"job-7","status":"queued"},"error":null,"warnings":[],"meta":{"duration_ms":18}}

# CI environment variable set
$ CI=true tool status
{"ok":true,"data":{"id":"job-7","status":"queued"},"error":null,"warnings":[],"meta":{"duration_ms":18}}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: the envelope structure emitted once JSON mode is active |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: prose is routed to stderr so stdout contains only JSON |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Composes: ANSI codes are stripped from all JSON string values |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Specializes: `CI` and `NO_COLOR` detection that also triggers JSON mode |
