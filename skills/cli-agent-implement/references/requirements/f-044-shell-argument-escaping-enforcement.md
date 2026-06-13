# REQ-F-044: Shell Argument Escaping Enforcement

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§34 Shell Injection via Agent-Constructed Commands](../challenges/01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST provide subprocess invocation APIs that never construct shell command strings. All subprocess calls MUST use exec-array style (argument list, not shell string) APIs, bypassing the shell entirely. The framework MUST prohibit `shell=True` (Python), `sh -c <string>` composition, and equivalent patterns. When the framework detects that a command argument contains shell metacharacters (`; | & $ ( ) < > \` \n \r`), it MUST reject the argument with exit code 2 before execution. This protection applies to all arguments derived from user input, environment variables, and prior command output.

## Acceptance Criteria

- A subprocess invocation via the framework API with a user-supplied argument containing `; rm -rf /` succeeds or rejects the argument cleanly — it MUST NOT execute the injected command.
- The framework's subprocess API raises a registration error if `shell=True` is passed.
- An argument containing a newline character is rejected in Phase 1 with exit code 2.
- Shell metacharacter rejection is documented in the framework's command author guide

---

## Schema

No dedicated schema type — this requirement governs subprocess invocation safety without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework raises an error if a shell string API is used or if an argument contains shell metacharacters.

```
# Rejected at registration — shell string API not permitted
framework.run("git clone " + user_input)
→ FrameworkError: shell string subprocess API is prohibited; use exec-array

# Correct — exec-array style
framework.run(["git", "clone", user_input])

# Argument containing shell metacharacter — rejected in Phase 1
framework.run(["git", "clone", "https://example.com/repo; rm -rf /"])
→ exit 2: ARG_ERROR — argument contains shell metacharacter ';'
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-045](f-045-agent-hallucination-input-pattern-rejection.md) | F | Composes: hallucination pattern rejection is a complementary Phase 1 validation layer |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: metacharacter check runs in Phase 1 before any side effect |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `ARG_ERROR (2)` is the exit code for rejected arguments |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Composes: rejection is reported as a structured JSON error response |
