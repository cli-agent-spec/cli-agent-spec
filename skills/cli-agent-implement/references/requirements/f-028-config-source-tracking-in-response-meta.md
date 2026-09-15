# REQ-F-028: Config Source Tracking in Response Meta

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§28 Config File Shadowing & Precedence](../challenges/05-high-environment-and-state/28-high-config-shadowing.md)

**Addresses:** Severity: High / Token Spend: High / Time: High / Context: Medium

---

## Description

The framework MUST automatically inject `meta.config_sources` (array of config file paths that were loaded, in precedence order) and `meta.effective_config_hash` (a short stable hash of the resolved configuration) into every response. This allows callers to detect when configuration has changed between invocations without needing to call `--show-config` separately.

## Acceptance Criteria

- Every response includes `meta.config_sources` as an array of absolute path strings
- `meta.effective_config_hash` changes when any config file is modified
- `meta.effective_config_hash` is stable when no config has changed
- The array is empty (not absent) when no config files were loaded

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.config_sources` and `meta.effective_config_hash` are framework-injected extensions to `ResponseMeta`

---

## Wire Format

`meta` in the response envelope, showing config files loaded in precedence order (highest priority first):

```json
{
  "ok": true,
  "data": { "deployed": true },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 204,
    "request_id": "req_01HZ",
    "config_sources": [
      "/home/user/myproject/.mytool.json",
      "/home/user/.config/mytool/config.json"
    ],
    "effective_config_hash": "a3f1c9"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework records each config file path as it is loaded and computes a stable hash of the merged configuration before dispatching the command.

```
$ tool deploy --env prod
→ meta.config_sources: ["/home/user/myproject/.mytool.json", "/home/user/.config/mytool/config.json"]
→ meta.effective_config_hash: "a3f1c9"

$ echo '{}' > /tmp/override.json && MYTOOL_CONFIG=/tmp/override.json tool deploy --env prod
→ meta.config_sources: ["/tmp/override.json", "/home/user/.config/mytool/config.json"]
→ meta.effective_config_hash: "7b2d01"   (hash changed — config changed)

$ tool deploy --env prod   (no config files found)
→ meta.config_sources: []
→ meta.effective_config_hash: "e3b0c4"  (hash of empty config)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries `meta.config_sources` |
| [REQ-F-027](f-027-cwd-in-response-meta.md) | F | Composes: both requirements inject diagnostic context into `meta` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Provides: `meta` separation that keeps config provenance out of `data` |
| [REQ-F-034](f-034-secret-field-auto-redaction-in-logs.md) | F | Enforces: secret values in loaded config are redacted before being logged |
