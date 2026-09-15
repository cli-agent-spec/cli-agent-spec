# REQ-C-018: Commands Declare Platform Requirements

**Tier:** Command Contract | **Priority:** P3

**Source:** [§27 Platform & Shell Portability](../challenges/05-high-environment-and-state/27-medium-platform-portability.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

Commands that have platform-specific requirements MUST declare them in their registration metadata: `platform` (array of supported OS names), `shell_requirements` (minimum shell version if applicable), and `required_tools` (array of external tool dependencies with minimum versions). The framework uses this information to populate `tool doctor` checks (REQ-O-026) and to emit a warning when a command is invoked on an unsupported platform.

## Acceptance Criteria

- `tool doctor` reports a check failure for each missing or outdated required tool
- Invoking a Linux-only command on macOS emits a compatibility warning in `meta.warnings`
- The `--schema` output for each command includes `platform` and `required_tools`

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

Platform requirements appear as additional fields in `CommandEntry`:

| Field | Type | Description |
|-------|------|-------------|
| `platform` | string[] | Supported OS names (e.g. `["linux", "darwin"]`). Absent means all platforms |
| `required_tools` | `Record<string, string>` | External binary dependencies; key is tool name, value is minimum version (semver) |

---

## Wire Format

```bash
$ tool package --schema
```
```json
{
  "parameters": {
    "output": { "type": "string", "required": true, "description": "Output archive path" }
  },
  "platform": ["linux"],
  "required_tools": {
    "dpkg-deb": "1.19.0",
    "fakeroot": "1.20.0"
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Package built successfully", "retryable": false, "side_effects": "complete" },
    "5": { "name": "NOT_FOUND", "description": "Required tool not installed", "retryable": false, "side_effects": "none" }
  }
}
```

---

## Example

```
register command "package":
  platform: [linux]
  required_tools:
    dpkg-deb: ">=1.19.0"
    fakeroot: ">=1.20.0"
  parameters:
    output: type=string, required=true, description="Output archive path"

# tool doctor  →  reports check failure if dpkg-deb or fakeroot is missing/outdated
# tool package (on macOS)  →  emits meta.warnings: ["Command not supported on darwin; expected linux"]
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `platform` and `required_tools` are part of the `--schema` output |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: platform compatibility warnings surface in `ResponseEnvelope.warnings` |
