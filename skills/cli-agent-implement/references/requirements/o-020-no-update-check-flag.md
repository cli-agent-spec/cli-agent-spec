# REQ-O-020: --no-update-check Flag

**Tier:** Opt-In | **Priority:** P1

**Source:** [§32 Self-Update & Auto-Upgrade Behavior](../challenges/05-high-environment-and-state/32-high-self-update.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST provide `--no-update-check` as a standard flag on every command. When passed (or when `TOOL_NO_UPDATE` is set), the framework MUST skip any update availability check for that invocation. This flag MUST be respected even in interactive TTY contexts where update checks are otherwise enabled. The flag MUST be visible in `--help` output.

## Acceptance Criteria

- `--no-update-check` prevents any network call for update checking
- `--no-update-check` and `TOOL_NO_UPDATE=1` are equivalent in effect
- `meta.update_available` is absent when `--no-update-check` is passed
- The flag is present in every command's `--help` output

---

## Schema

No dedicated schema type — `--no-update-check` suppresses `meta.update_available` from appearing; no new fields are added.

---

## Wire Format

Without `--no-update-check` (when update is available):

```json
{ "meta": { "update_available": "2.2.0", "tool_version": "2.1.0" } }
```

With `--no-update-check`:

```json
{ "meta": { "tool_version": "2.1.0" } }
```

---

## Example

Opt-in at the framework level; automatically available on every command.

```
app = Framework("tool")
app.enable_no_update_check()   # registers --no-update-check globally

# In CI — skip network call for update check:
$ tool deploy --no-update-check
# equivalent to setting TOOL_NO_UPDATE=1
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Provides: automatic suppression in non-TTY; this flag adds explicit control |
| [REQ-F-050](f-050-update-notifier-side-channel-suppression.md) | F | Composes: notifier side-channel is also suppressed when this flag is set |
| [REQ-F-023](f-023-tool-version-in-every-response.md) | F | Composes: `meta.tool_version` is always present; `update_available` is conditional |
