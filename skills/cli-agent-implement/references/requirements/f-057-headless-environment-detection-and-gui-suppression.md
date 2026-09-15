# REQ-F-057: Headless Environment Detection and GUI Suppression

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§64 Headless Display and GUI Launch Blocking](../challenges/01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST detect headless execution environments on startup by checking: `sys.stdout.isatty()`, `CI` environment variable, `DISPLAY` and `WAYLAND_DISPLAY` environment variables (Linux/Unix), and `SSH_TTY`. When headless mode is detected, the framework MUST set `framework.headless = true` and intercept any attempt to launch a GUI application (browser open, file picker, notification dialog) via `xdg-open`, `webbrowser.open()`, `open` (macOS), or equivalent. Instead of launching, the framework MUST return the URL/path in the JSON response under `data.open_url` or `data.open_path` with a `meta.headless: true` indicator.

## Acceptance Criteria

- In a container without `$DISPLAY`, `xdg-open https://example.com` via framework API does not block; URL appears in `data.open_url`
- `meta.headless: true` is set in all responses when headless mode is active
- A command that declares `gui_operations: []` and attempts a GUI launch without headless behavior declared triggers a framework registration error
- In TTY mode with `$DISPLAY` set, GUI launches proceed normally

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

In headless mode, commands that would normally open a browser or file picker return the URL or path in `data.open_url` / `data.open_path` instead, and set `meta.headless: true`.

---

## Wire Format

```json
{
  "ok": true,
  "data": {
    "open_url": "https://example.com/auth/callback",
    "opened": false
  },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 8,
    "headless": true
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework intercepts GUI launch calls and redirects output when headless mode is detected.

```
# Container environment — no $DISPLAY, CI=true
$ mytool auth login --json
{
  "ok": true,
  "data": { "open_url": "https://auth.example.com/device?code=ABC123", "opened": false },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 8, "headless": true }
}
→ browser not launched; URL available for agent to surface

# TTY with $DISPLAY set
$ mytool auth login
→ browser opens at https://auth.example.com/device?code=ABC123
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` shape used to return `data.open_url` and `meta.headless` |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Composes: `CI` environment variable detection shared with headless detection |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: non-interactive mode detection triggers headless behavior |
| [REQ-F-055](f-055-editor-and-visual-no-op-in-non-tty-mode.md) | F | Specializes: editor suppression is a specific case of the broader GUI suppression pattern |
