# REQ-C-023: Editor-Requiring Commands Declare Non-Interactive Alternative

**Tier:** Command Contract | **Priority:** P1

**Source:** [§62 $EDITOR and $VISUAL Trap](../challenges/01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Any command that invokes `$EDITOR` or `$VISUAL` MUST declare `requires_editor: true` in its registration metadata AND MUST declare at least one non-interactive alternative flag (e.g., `--message <text>`, `--from-file <path>`, `--content <text>`). The framework verifies this at registration and raises an error if `requires_editor: true` without a declared alternative. In non-TTY mode, the framework automatically uses the non-interactive alternative; if no value is provided for it, the command exits 4 with the alternative flag listed in the error.

## Acceptance Criteria

- A command with `requires_editor: true` but no declared alternative raises a registration error
- In non-TTY mode, `git commit` equivalent exits 4 with `hint: "use --message <text> instead"`
- Passing `--message "text"` in non-TTY mode bypasses the editor and proceeds normally
- In TTY mode, the editor is invoked normally when neither alternative flag is provided

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

Editor-requiring commands extend `CommandEntry` with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requires_editor` | boolean (`true`) | yes | Marks the command as invoking `$EDITOR` or `$VISUAL` when no alternative is supplied |
| `non_interactive_alternatives` | string[] | yes | Flag names that bypass the editor (e.g. `["message", "from-file"]`) |

---

## Wire Format

```bash
$ tool commit --schema
```
```json
{
  "requires_editor": true,
  "non_interactive_alternatives": ["message", "from-file"],
  "parameters": {
    "message":   { "type": "string", "required": false, "description": "Commit message text; bypasses editor" },
    "from-file": { "type": "string", "required": false, "description": "Path to file containing commit message" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS", "description": "Commit created",                                      "retryable": false, "side_effects": "complete" },
    "4": { "name": "NO_TTY",  "description": "Editor unavailable in non-TTY mode; use --message",  "retryable": true,  "side_effects": "none"     }
  }
}
```

---

## Example

```
register command "commit":
  requires_editor: true
  non_interactive_alternatives: [message, from-file]
  parameters:
    message:   type=string, required=false, description="Commit message text; bypasses editor"
    from-file: type=string, required=false, description="Path to file containing commit message"

# tool commit  (non-TTY, no --message, no --from-file)
#  → exit 4: {"code": "NO_TTY", "message": "Editor not available", "suggestion": "use --message <text> or --from-file <path>"}

# tool commit --message "Fix typo"  (non-TTY)
#  → exit 0: commit created without editor

# register command "bad-commit":
#   requires_editor: true
#   (no non_interactive_alternatives)
#  → framework error: requires_editor: true requires at least one non_interactive_alternative
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-055](f-055-editor-and-visual-no-op-in-non-tty-mode.md) | F | Enforces: `$EDITOR` and `$VISUAL` are suppressed in non-TTY mode at the framework level |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-TTY detection used to enforce the declared `non_interactive_alternatives` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `requires_editor` and `non_interactive_alternatives` are part of `--schema` output |
| [REQ-C-024](c-024-gui-launching-commands-declare-headless-behavior.md) | C | Specializes: editor invocation is one category of interactive operation with a declared headless fallback |
