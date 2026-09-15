# REQ-F-060: Third-Party Stdout Interception

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§68 Third-Party Library Stdout Pollution](../challenges/01-critical-ecosystem-runtime-agent-specific/68-high-stdout-pollution.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: High

---

## Description

The framework MUST intercept all writes to file descriptor 1 (stdout) that are not made through the framework's `output()` API. Intercepted writes MUST be buffered, classified, and reclassified: prose writes (non-JSON) are moved to `warnings[]` with `code: "THIRD_PARTY_STDOUT"` and the raw text in `detail`; JSON-shaped writes are silently discarded (to prevent double-emission). The interception MUST be installed at the file descriptor level (not just the language runtime level) to capture writes from native extensions. The interception MUST be installed before any imports.

## Acceptance Criteria

- A library that calls `print("initialized")` on import does not contaminate the JSON stdout
- The intercepted string appears as a warning: `{"code": "THIRD_PARTY_STDOUT", "message": "Third-party code wrote to stdout", "context": {"text": "initialized"}}`
- `json.loads(stdout_output)` succeeds even when a dependency prints to stdout
- In debug mode (`--debug`), intercepted stdout is emitted to stderr with source attribution

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

Intercepted non-JSON writes from third-party libraries appear in the `warnings` array with `code: "THIRD_PARTY_STDOUT"` and the raw text in `context.text`.

---

## Wire Format

```json
{
  "ok": true,
  "data": { "id": "run-99" },
  "error": null,
  "warnings": [
    {
      "code": "THIRD_PARTY_STDOUT",
      "message": "Third-party code wrote to stdout",
      "context": { "text": "initialized" }
    }
  ],
  "meta": { "exit_code": 0, "duration_ms": 55 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework installs its FD-1 interceptor before any imports so that library initialization output is captured.

```
# Third-party library prints on import
$ mytool run --json
# (underlying library printed "SDK initialized" to stdout)
{
  "ok": true,
  "data": { "id": "run-99" },
  "error": null,
  "warnings": [{ "code": "THIRD_PARTY_STDOUT", "message": "Third-party code wrote to stdout", "context": { "text": "SDK initialized" } }],
  "meta": { "exit_code": 0, "duration_ms": 55 }
}
→ json.loads(stdout) succeeds; contamination reclassified as warning
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` `warnings` array where intercepted output is placed |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Enforces: stdout is reserved for structured JSON; all other output must be redirected |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Composes: debug mode emits intercepted stdout to stderr with attribution |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Composes: intercepted text is also scanned for secrets before being placed in warnings |
