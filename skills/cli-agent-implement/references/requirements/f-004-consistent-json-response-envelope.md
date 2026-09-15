# REQ-F-004: Consistent JSON Response Envelope

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MUST wrap all command output in a standard JSON envelope. The envelope MUST always contain: `ok` (boolean), `data` (the command's primary output — present even when null or empty array), `error` (null on success, structured object on failure), `warnings` (array of `WarningDetail` objects, may be empty), and `meta` (object with framework-populated fields, always including `exit_code` and `duration_ms`). The schema of this envelope MUST NOT vary based on result count, command type, or success/failure state — the same top-level keys MUST always be present.

## Acceptance Criteria

- A JSON schema validator for the envelope passes on every command's stdout output in JSON mode
- `data` key is present and non-absent on both success and failure responses
- `error` key is present on all responses (null on success, structured object on failure)
- `meta.exit_code` is present on every response and equals the process exit code
- `ok` is `true` if and only if `meta.exit_code` is `0`
- Single-result and multi-result commands produce structurally identical envelopes

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

---

## Wire Format

Full envelope structure — all five top-level keys are always present regardless of outcome:

**Success response:**
```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 340, "request_id": "req_abc123" }
}
```

**Failure response (same shape):**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Cluster 'prod-eu' not found",
    "retryable": false
  },
  "warnings": [],
  "meta": { "exit_code": 5, "duration_ms": 8 }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework constructs the envelope after every command handler returns, deriving `ok` from the exit code and always emitting all five fields.

```
# Command handler returns successfully
handler returns: { id: "deploy-42", status: "complete" }
Framework wraps:
  ok      = true   (derived: exit code is SUCCESS)
  data    = handler's return value
  error   = null
  warnings= []
  meta    = { duration_ms: 340 }

# Command handler raises NOT_FOUND
Framework wraps:
  ok      = false  (derived: exit code is NOT_FOUND)
  data    = null
  error   = { code: "NOT_FOUND", message: "...", retryable: false }
  warnings= []
  meta    = { duration_ms: 8 }
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ok` is derived from whether the exit code is `SUCCESS (0)` |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: envelope is emitted whenever JSON mode is active |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: `error` object structure is declared by REQ-C-013 |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Wraps: manifest output uses this envelope as its outer container |
