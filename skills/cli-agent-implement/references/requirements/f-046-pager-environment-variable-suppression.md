# REQ-F-046: Pager Environment Variable Suppression

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

In addition to the pager suppression in REQ-F-010, the framework MUST set the following environment variables before any subprocess invocation to prevent third-party libraries from spawning interactive pagers: `PAGER=cat`, `GIT_PAGER=cat`, `LESS=-F -X -R`, `MORE= ` (empty), `MANPAGER=cat`. These variables MUST be set in the subprocess environment unconditionally when the framework's subprocess API is used, regardless of any inherited environment. Framework-level help rendering MUST also respect these settings.

## Acceptance Criteria

- A subprocess invoked via the framework API cannot open an interactive pager even if the host `PAGER` env var is set to `less`
- `git log` invoked via the framework API does not block waiting for pager input in non-TTY mode
- The environment variable injection is applied to all levels of subprocess nesting (direct children and grandchildren of the framework process)
- The suppression is transparent to command authors: no per-command configuration required

---

## Schema

No dedicated schema type — this requirement governs environment variable injection without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework injects pager-suppression variables before any command or subprocess runs.

```
# Framework bootstrap (transparent to command author)
os.environ["PAGER"] = "cat"
os.environ["GIT_PAGER"] = "cat"
os.environ["LESS"] = "-F -X -R"
os.environ["MORE"] = ""
os.environ["MANPAGER"] = "cat"

# git log via framework subprocess API — does not block in non-TTY mode
framework.run(["git", "log", "--oneline"])
→ output printed directly, no interactive pager spawned

# Even if host environment had PAGER=less:
$ PAGER=less tool git-summary
→ GIT_PAGER=cat overrides, no pager spawned
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-010](f-010-pager-suppression.md) | F | Extends: this requirement adds env var injection on top of the base pager suppression |
| [REQ-F-055](f-055-editor-and-visual-no-op-in-non-tty-mode.md) | F | Composes: `$EDITOR` / `$VISUAL` suppression uses the same env var injection pattern |
| [REQ-F-050](f-050-update-notifier-side-channel-suppression.md) | F | Composes: update notifier suppression injects additional env vars via the same mechanism |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Composes: verbosity suppression is part of the same non-TTY hardening applied at bootstrap |
