# REQ-O-024: --context / --config Override Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§26 Stateful Commands & Session Management](../challenges/05-high-environment-and-state/26-high-session-management.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

The framework MUST provide `--context <name>` (select a named context from the config file) and `--config <path>` (use a specific config file instead of the default) as standard flags on every command. These flags MUST allow complete isolation between agent sessions that share a filesystem: each session passes `--config /tmp/agent-session-N/config.json` to prevent state conflicts. When `--context` is passed, it MUST override any context set by prior `use-context` style commands.

## Acceptance Criteria

- `--config /tmp/isolated.json` causes the command to load config only from that file
- `--context staging` causes the command to use the `staging` context from the loaded config
- Two concurrent invocations with different `--config` paths do not share any mutable state
- `meta.config_sources` reflects the `--config` path when passed

---

## Schema

No dedicated schema type — this requirement governs config isolation behavior. The existing `meta.config_sources` field (from REQ-F-028) reflects the active `--config` path; no new fields are added.

---

## Wire Format

```bash
$ tool deploy --config /tmp/agent-session-7/config.json --context staging --target app-v2
```

```json
{
  "ok": true,
  "data": { "deployed": "app-v2", "environment": "staging" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 310,
    "config_sources": ["/tmp/agent-session-7/config.json"],
    "context": "staging"
  }
}
```

---

## Example

The `--context` and `--config` flags are registered globally once at application startup; no per-command declaration is required:

```
app = Framework("tool")
app.enable_context_flags()

# Every command now accepts:
#   --config <path>    use specific config file
#   --context <name>   select named context within config
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-028](f-028-config-source-tracking-in-response-meta.md) | F | Provides: `meta.config_sources` field populated by this flag |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Composes: `meta.context` added to the standard envelope meta |
| [REQ-O-028](o-028-tool-status-built-in-command.md) | O | Exposes: `tool status --show-config` reports the active config path and context |
| [REQ-O-036](o-036-instance-id-flag-for-agent-state-namespacing.md) | O | Composes: `--instance-id` provides per-agent state namespacing complementary to `--config` |
| [REQ-C-025](c-025-config-writing-commands-declare-write-scope.md) | C | Composes: config-writing commands respect the `--config` path set by this flag |
