# REQ-F-023: Tool Version in Every Response

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§22 Schema Versioning & Output Stability](../challenges/06-high-errors-and-discoverability/22-high-schema-versioning.md) · [§32 Self-Update & Auto-Upgrade Behavior](../challenges/05-high-environment-and-state/32-high-self-update.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST automatically inject `meta.tool_version` (semver string of the running tool binary) and, when an update is available, `meta.update_available` (semver string of the latest version) into every response. The update availability check MUST be non-blocking and MUST NOT delay command execution. If the update check fails, `meta.update_available` MUST be omitted (not set to an error value).

## Acceptance Criteria

- Every response includes `meta.tool_version`
- `meta.tool_version` matches the output of `tool --version`
- `meta.update_available` is absent (not null, absent) when no update is available or check failed
- The update check does not add measurable latency to command execution

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.tool_version` and the optional `meta.update_available` are injected by the framework into every response's `meta` object.

---

## Wire Format

Response `meta` with `tool_version` and optional `update_available`:

```json
{
  "ok": true,
  "data": { "id": "deploy-99", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id":       "req_08MN",
    "command":          "deploy",
    "timestamp":        "2024-06-01T12:00:00Z",
    "schema_version":   "1.0",
    "tool_version":     "2.4.1",
    "update_available": "2.5.0"
  }
}
```

When no update is available or the check failed, `update_available` is absent (not `null`):

```json
{
  "meta": {
    "tool_version": "2.4.1"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework reads its own version at startup and injects it into every response. The update check runs in a background goroutine/thread and its result is included only if available before serialization completes.

```
$ tool --version
2.4.1

$ tool deploy --env prod
→ meta.tool_version: "2.4.1"
→ meta.update_available: "2.5.0"   ← background check completed in time

$ tool deploy --env prod
→ meta.tool_version: "2.4.1"
# meta.update_available absent — check timed out, not null
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Composes: `schema_version` accompanies `tool_version` in every response `meta` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Enforces: `tool_version` is a volatile field and belongs in `meta` |
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Composes: update check that populates `update_available` is suppressed in non-interactive mode |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope whose `meta` carries `tool_version` |
