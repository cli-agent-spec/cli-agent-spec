# REQ-O-036: --instance-id Flag for Agent State Namespacing

**Tier:** Opt-In | **Priority:** P1

**Source:** [§58 Multi-Agent Concurrent Invocation Conflict](../challenges/01-critical-ecosystem-runtime-agent-specific/58-high-multiagent-conflict.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST provide `--instance-id <string>` as a global flag. When set, all per-instance state (config cache, credential cache, temp directories, lock files) is namespaced under `~/.tool/instances/<instance-id>/`. This allows multiple parallel agent instances to operate on the same machine without state conflicts. The `TOOL_INSTANCE_ID` environment variable MAY also set the instance ID. If neither is set, the framework uses a default shared namespace with file locking for all writes.

## Acceptance Criteria

- `tool --instance-id agent-1 config set region=us-east-1` writes to `~/.tool/instances/agent-1/config.json`
- `tool --instance-id agent-2 config set region=eu-west-1` writes to a different path and does not affect agent-1's config
- Without `--instance-id`, concurrent config writes use file locking and succeed sequentially
- `TOOL_INSTANCE_ID=agent-3` is equivalent to `--instance-id agent-3`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.instance_id` reflects the active instance namespace. All state paths are scoped under this ID.

---

## Wire Format

```bash
$ tool --instance-id agent-1 config set region=us-east-1 --format json
```

```json
{
  "ok": true,
  "data": { "key": "region", "value": "us-east-1", "scope": "instance" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "instance_id": "agent-1", "duration_ms": 4 }
}
```

---

## Example

Opt-in at the framework level.

```
app = Framework("tool")
app.enable_instance_id()

# Each agent uses its own isolated state namespace:
$ tool --instance-id agent-1 config set region=us-east-1
$ tool --instance-id agent-2 config set region=eu-west-1
# → namespaced to ~/.tool/instances/agent-1/ and ~/.tool/instances/agent-2/ respectively

# Equivalent via env var:
export TOOL_INSTANCE_ID=agent-1
$ tool config set region=us-east-1
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-033](f-033-lock-acquisition-with-timeout-and-retry-after-ms.md) | F | Composes: without `--instance-id`, concurrent state writes use file locking |
| [REQ-F-032](f-032-session-scoped-temp-directory.md) | F | Composes: temp directories are namespaced per instance |
| [REQ-C-025](c-025-config-writing-commands-declare-write-scope.md) | C | Composes: instance-scoped writes are a subtype of local-scope writes |
