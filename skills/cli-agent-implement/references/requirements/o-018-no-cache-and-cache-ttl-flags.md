# REQ-O-018: --no-cache and --cache-ttl Flags

**Tier:** Opt-In | **Priority:** P3

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

For commands that write to caches, the framework MUST provide `--no-cache` (skip cache reads and writes for this invocation) and `--cache-ttl <seconds>` (override the default cache TTL). These flags MUST be automatically available on commands that declare a `cache` entry in `filesystem_side_effects` (REQ-C-011). With `--no-cache`, the command MUST NOT read from or write to any declared cache path.

## Acceptance Criteria

- `--no-cache` causes the command to bypass all declared cache files
- `--cache-ttl 0` is equivalent to `--no-cache`
- Cache files older than `--cache-ttl` seconds are treated as missing (re-fetched)
- The flags are absent on commands that declare no cache side effects

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`meta.cache_used` indicates whether any cached data was read during the invocation.

---

## Wire Format

```bash
$ tool resolve --no-cache --format json
```

```json
{
  "ok": true,
  "data": { "resolved": "1.2.3" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "cache_used": false, "duration_ms": 1832 }
}
```

---

## Example

Opt-in: automatically available on commands that declare a cache entry in `filesystem_side_effects`.

```
register command "resolve":
  filesystem_side_effects:
    - type: cache
      path: ~/.tool/cache/resolve/
      ttl: 3600
  # --no-cache and --cache-ttl are auto-registered by the framework

$ tool resolve --no-cache
→ meta.cache_used: false  # fresh fetch, no cache read or write
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Provides: cache declarations that trigger these flags |
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | F | Composes: temp files and caches share the session cleanup mechanism |
| [REQ-O-027](o-027-tool-cleanup-built-in-command.md) | O | Composes: `tool cleanup --scope cache` removes what `--no-cache` bypasses |
