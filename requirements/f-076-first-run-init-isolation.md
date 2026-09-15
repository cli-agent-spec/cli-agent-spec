# REQ-F-076: First-Run Init Isolation

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents assume the first call to a tool behaves identically to the hundredth call; silent first-run initialization that can fail leaves the agent in an unrecoverable state with no actionable error

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: Low

---

## Description

The framework MUST NOT perform one-time initialization (config directory creation, schema migration, keypair generation, default config write, dependency download) as a side effect of the first regular command invocation. Any such initialization MUST either:

1. Be exposed as an explicit `tool init` subcommand that the agent can call intentionally, or
2. Be guaranteed infallible (no network, no disk space requirement, no permissions beyond the user's home directory) and idempotent

If initialization can fail for any reason (network unavailable, permissions denied, disk full), it MUST be exposed as `tool init` so the agent can detect and handle the failure. Mixing initialization with command execution produces errors that look like command failures, not init failures, making them unrecoverable without human intervention.

## Acceptance Criteria

- First invocation of any non-init command produces identical output to the 100th invocation (same stdout schema, same exit codes)
- Any initialization that requires network access is gated behind `tool init` or `tool doctor`
- `tool init` is idempotent — calling it on an already-initialized environment exits 0 with `{"already_initialized": true}`
- A failed `tool init` exits non-zero with a structured error indicating the specific failure (permissions, network, disk)
- First invocation in a clean environment without running `tool init` first either works identically OR exits with a structured `INIT_REQUIRED` error pointing to `tool init`

---

## Schema

No dedicated schema type — `INIT_REQUIRED` uses standard `error` block in `response-envelope`

---

## Wire Format

If init is required and has not been run:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INIT_REQUIRED",
    "message": "Run 'tool init' before first use",
    "retryable": false,
    "next_steps": ["tool init"]
  },
  "warnings": [],
  "meta": { "exit_code": 4, "duration_ms": 6 }
}
```

---

## Example

Without this requirement:
```
$ HOME=/tmp/fresh tool deploy --env prod
Error: cannot open /tmp/fresh/.config/tool/schema.db: no such file or directory
→ exit code: 1   ← looks like a deploy failure, not an init failure
```

With this requirement:
```
$ HOME=/tmp/fresh tool deploy --env prod
{"ok":false,"error":{"code":"INIT_REQUIRED","message":"Run 'tool init' before first use","next_steps":["tool init"]}}
→ exit code: 1

$ HOME=/tmp/fresh tool init
{"ok":true,"data":{"initialized":true}}
→ exit code: 0

$ HOME=/tmp/fresh tool deploy --env prod
(normal deploy output)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-068](f-068-help-and-version-flag-purity.md) | F | Extends: --help and --version bypass init checks entirely |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Composes: INIT_REQUIRED check runs before Phase 1 argument validation |
| [REQ-O-026](o-026-tool-doctor-built-in-command.md) | O | Provides: tool doctor diagnoses init failures post-hoc |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Provides: structured error format for INIT_REQUIRED response |
