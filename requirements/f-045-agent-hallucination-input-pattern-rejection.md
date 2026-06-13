# REQ-F-045: Agent Hallucination Input Pattern Rejection

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§35 Agent Hallucination Input Patterns](../challenges/01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST automatically validate all arguments declared as resource IDs, paths, or identifiers against a set of known agent hallucination patterns. The following patterns MUST be rejected with exit code 2 before any side effect: path traversal sequences (`../`, `..%2f`, `..%5c`, `%2e%2e/`), percent-encoded segments in resource IDs (`%2e`, `%2f`, `%40`), embedded query parameters (`?`, `&` in resource IDs), fragment identifiers (`#` in resource IDs), and URL-encoded shell metacharacters. Command authors declare the argument type; the framework applies appropriate pattern checks automatically.

## Acceptance Criteria

- An argument of type `resource_id` containing `../` is rejected in Phase 1 with exit code 2
- An argument containing `%2e%2e` is rejected in Phase 1 with exit code 2
- An argument containing `?foo=bar` where `?` is not expected is rejected with exit code 2
- A path argument that is valid (e.g., `/home/user/file.txt`) passes validation without modification

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

When an argument is rejected, the framework emits a structured error with `code: "INVALID_AGENT_INPUT"`, `input_value` (the offending value), and `rejected_pattern` (the matched pattern name).

---

## Wire Format

`tool <cmd> --resource-id "../etc/passwd"` → error response (exit 3):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_AGENT_INPUT",
    "message": "Argument 'resource_id' contains a rejected pattern",
    "input_value": "../etc/passwd",
    "rejected_pattern": "path_traversal"
  },
  "warnings": [],
  "meta": {}
}
```

---

## Example

Framework-Automatic: no command author action needed. The command author declares the argument type; the framework applies appropriate pattern checks automatically.

```
# Command registration — type declaration only
register argument "resource_id":
  type: resource_id

# Framework rejects hallucinated input before any side effect
tool files get --resource-id "../etc/passwd"
→ exit 3: INVALID_AGENT_INPUT — argument contains path_traversal pattern

tool files get --resource-id "files%2fetc%2fpasswd"
→ exit 3: INVALID_AGENT_INPUT — argument contains percent_encoded_separator pattern

# Valid input passes through unchanged
tool files get --resource-id "usr-a1b2c3"
→ proceeds to execution
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-044](f-044-shell-argument-escaping-enforcement.md) | F | Composes: shell metacharacter rejection is a complementary Phase 1 validation layer |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: hallucination pattern checks run in Phase 1 before any side effect |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ARG_ERROR (2)` is the exit code for rejected arguments |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: rejection is reported as a structured JSON error response |
