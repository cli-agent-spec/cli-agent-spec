# REQ-C-024: GUI-Launching Commands Declare Headless Behavior

**Tier:** Command Contract | **Priority:** P1

**Source:** [§64 Headless Display and GUI Launch Blocking](../challenges/01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Any command that launches a GUI application, opens a browser, or invokes a display-requiring subprocess MUST declare `gui_operations: [<list of operation types>]` and `headless_behavior: <"emit_in_output" | "skip" | "error">` in its registration metadata. The framework raises a registration error if `gui_operations` is non-empty without `headless_behavior`. In headless mode, the framework enforces the declared behavior automatically: `emit_in_output` places the URL/path in the JSON response, `skip` omits the operation with a warning, `error` exits 4.

## Acceptance Criteria

- A command with `gui_operations: ["browser_open"]` and `headless_behavior: "emit_in_output"` returns `data.open_url` in headless mode
- A command with `gui_operations: ["browser_open"]` but no `headless_behavior` raises a registration error
- In non-headless mode, the GUI operation proceeds normally
- `meta.headless: true` is included in all responses when headless mode is active

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`response-envelope.md`](../schemas/response-envelope.md)

GUI-launching commands extend `CommandEntry` with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gui_operations` | string[] | yes | Types of display operations performed (e.g. `["browser_open", "desktop_notification"]`) |
| `headless_behavior` | `"emit_in_output"` \| `"skip"` \| `"error"` | yes | How the framework handles each `gui_operations` type in headless mode |

`ResponseMeta` is extended with:

| Field | Type | Description |
|-------|------|-------------|
| `headless` | boolean | `true` when the command ran in headless mode |

---

## Wire Format

```bash
$ tool open --schema
```
```json
{
  "gui_operations": ["browser_open"],
  "headless_behavior": "emit_in_output",
  "parameters": {
    "url": { "type": "string", "required": true, "description": "URL to open in the browser" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS", "description": "URL opened or returned in output",         "retryable": false, "side_effects": "complete" },
    "4": { "name": "NO_TTY",  "description": "GUI unavailable and headless_behavior=error", "retryable": false, "side_effects": "none"   }
  }
}
```

Headless response (`headless_behavior: "emit_in_output"`):

```json
{
  "ok": true,
  "data": { "open_url": "https://example.com/dashboard" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 5, "headless": true }
}
```

---

## Example

```
register command "open":
  gui_operations: [browser_open]
  headless_behavior: emit_in_output
  parameters:
    url: type=string, required=true, description="URL to open"

register command "notify":
  gui_operations: [desktop_notification]
  headless_behavior: skip

register command "preview":
  gui_operations: [browser_open]
  headless_behavior: error

# register command "bad-open":
#   gui_operations: [browser_open]
#   (no headless_behavior)
#  → framework error: gui_operations requires headless_behavior declaration
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-057](f-057-headless-environment-detection-and-gui-suppression.md) | F | Enforces: headless environment detection that triggers `headless_behavior` |
| [REQ-C-023](c-023-editor-requiring-commands-declare-non-interactive-.md) | C | Specializes: editor invocation is one type of `gui_operations` with a declared headless fallback |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `gui_operations` and `headless_behavior` are part of `--schema` output |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: `meta.headless` and `data.open_url` are carried in `ResponseEnvelope` |
