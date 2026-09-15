# REQ-F-050: Update Notifier Side-Channel Suppression

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§41 Update Notifier Side-Channel Output Pollution](../challenges/01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: High

---

## Description

In non-TTY mode and when `CI` is set, the framework MUST suppress all update/upgrade notification output on both stdout and stderr. The suppression MUST be applied by: setting `CI=1` (suppresses most Node.js package update notifiers), `NO_UPDATE_NOTIFIER=1`, `HOMEBREW_NO_AUTO_UPDATE=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1`, and any other environment variables appropriate to the host runtime. The framework MUST provide a registration hook `suppress_update_notifier(fn)` for command authors to register custom suppression logic for third-party libraries that check updates in non-standard ways.

## Acceptance Criteria

- A command that uses a library with a built-in update notifier produces no update notification on stdout or stderr in non-TTY mode
- The suppression environment variables are set before any command execution
- `CI=1` is set in the subprocess environment for all child processes spawned by the framework
- In TTY mode, update notifications are unaffected (shown as normal)

---

## Schema

No dedicated schema type — this requirement governs environment variable injection and stdout protection without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework sets suppression environment variables before any command execution.

```
# Framework bootstrap in non-TTY mode (transparent to command author)
os.environ["CI"] = "1"
os.environ["NO_UPDATE_NOTIFIER"] = "1"
os.environ["HOMEBREW_NO_AUTO_UPDATE"] = "1"
os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

# A command using a library with a built-in update notifier:
tool deploy --target prod
→ stdout: {"ok":true,"data":{...}}   (no update banner)
→ stderr: (empty)

# Without suppression (TTY mode, allowed):
$ tool deploy --target prod
→ stdout: deploy output
→ stderr: "Update available: 1.2.3 → 1.3.0. Run: pip install --upgrade mycli"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Specializes: this requirement extends the base update suppression with explicit env vars |
| [REQ-F-046](f-046-pager-environment-variable-suppression.md) | F | Composes: pager suppression uses the same env var injection pattern |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Composes: quiet mode and update suppression are both applied at bootstrap in non-TTY mode |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Enforces: update notifiers must not pollute the stdout JSON stream |
