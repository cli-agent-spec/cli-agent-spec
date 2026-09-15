# REQ-C-012: Commands with Network I/O Support --timeout

**Tier:** Command Contract | **Priority:** P0

**Source:** [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Every command that performs network I/O or any potentially long-running blocking operation MUST accept `--timeout <duration>` and `--connect-timeout <duration>` flags (where applicable). The framework registers these flags automatically for commands that declare `has_network_io: true`. Command authors MUST pass the configured timeout to all network calls; the framework MUST enforce that no network call is made without a finite timeout.

## Acceptance Criteria

- A command with `has_network_io: true` always accepts `--timeout`
- The configured `--timeout` value is passed to all network requests made by the command
- A network call with no explicit timeout is flagged by the framework's static analysis rule
- `--timeout 0` explicitly opts into no timeout (must be a deliberate choice, not the default)

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`exit-code.md`](../schemas/exit-code.md)

The `has_network_io` boolean and the standard `--timeout` / `--connect-timeout` flags appear in the command's schema entry.

```json
{
  "has_network_io": {
    "type": "boolean",
    "description": "True if the command makes outbound network connections or long-running blocking I/O calls"
  }
}
```

---

## Wire Format

```bash
$ tool deploy --target staging --schema
```

```json
{
  "command": "deploy",
  "has_network_io": true,
  "flags": {
    "target":          { "type": "string",  "required": true,  "description": "Target environment name" },
    "timeout":         { "type": "string",  "required": false, "default": "300s", "description": "Maximum total operation time; 0 = no timeout" },
    "connect-timeout": { "type": "string",  "required": false, "default": "10s",  "description": "Maximum time to establish each connection" }
  },
  "exit_codes": {
    "0":  { "name": "SUCCESS",   "description": "Deployment completed",                "retryable": false, "side_effects": "complete" },
    "10": { "name": "TIMEOUT",   "description": "Deployment timed out after --timeout", "retryable": false, "side_effects": "partial"  }
  }
}
```

---

## Example

A command that makes HTTP calls declares `has_network_io: true` at registration. The framework auto-registers `--timeout` and `--connect-timeout` and enforces that they are passed to all network calls.

```
register command "deploy":
  danger_level: mutating
  has_network_io: true
  exit_codes:
    SUCCESS (0): description: "Deployment completed",                retryable: false, side_effects: complete
    TIMEOUT(10): description: "Deployment timed out after --timeout", retryable: false, side_effects: partial

  execute(args):
    # Framework injects args.timeout and args.connect_timeout from flags
    client = http_client(
      timeout=args.timeout,
      connect_timeout=args.connect_timeout,
    )
    client.post("/deploy", body={target: args.target})
    # Any call without an explicit timeout → framework static analysis warning
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Provides: framework sets the default timeout value used when `--timeout` is not supplied |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Enforces: framework emits `TIMEOUT (10)` and structured JSON error when the timeout expires |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `TIMEOUT (10)` must be declared in the command's `exit_codes` map |
| [REQ-C-008](c-008-multi-step-commands-emit-step-manifest.md) | C | Composes: on timeout, multi-step commands emit `completed_steps` and `failed_step` via the step manifest |
