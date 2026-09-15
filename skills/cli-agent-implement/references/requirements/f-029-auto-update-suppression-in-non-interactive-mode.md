# REQ-F-029: Auto-Update Suppression in Non-Interactive Mode

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§32 Self-Update & Auto-Upgrade Behavior](../challenges/05-high-environment-and-state/32-high-self-update.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST disable any auto-update behavior (including update checks that add latency) when: `isatty(stdout) == false`, `CI` is set, `TOOL_NO_UPDATE` is set, or `--no-update-check` is passed. The framework MUST ensure that update availability information is surfaced only as a non-blocking `meta.update_available` field. The framework MUST ensure that the tool binary is never replaced while any instance is running.

## Acceptance Criteria

- No update check occurs when `CI=true`
- No update check occurs when stdout is not a TTY
- Setting `TOOL_NO_UPDATE=1` disables all update behavior including background checks
- No measurable latency is added to any command due to update checking in non-interactive mode

---

## Schema

No dedicated schema type — this requirement governs framework startup behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework checks `isatty(stdout)` and the `CI` and `TOOL_NO_UPDATE` environment variables before the command is dispatched. If any suppression condition is met, the framework sets `NO_UPDATE_NOTIFIER=1` (or the equivalent internal flag) before executing the command.

```
$ CI=true tool deploy --env prod
→ No update check performed
→ No "update available" message on stderr
→ Command executes with zero added latency

$ TOOL_NO_UPDATE=1 tool deploy --env prod
→ No update check performed, background checks also disabled

$ tool deploy --env prod   (stdout is a pipe)
→ isatty(stdout) == false → update check suppressed automatically
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-interactive mode detection reused to suppress updates |
| [REQ-F-050](f-050-update-notifier-side-channel-suppression.md) | F | Specializes: suppresses update notifier side-channel writes in non-interactive mode |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Composes: `CI` environment variable detection shared with this requirement |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Composes: auto-quiet mode applies the same non-TTY detection |
