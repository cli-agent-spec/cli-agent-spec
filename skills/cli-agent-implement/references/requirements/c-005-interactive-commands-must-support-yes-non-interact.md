# REQ-C-005: Interactive Commands Must Support --yes / --non-interactive

**Tier:** Command Contract | **Priority:** P0

**Source:** [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Any command that would prompt the user for confirmation or input in interactive mode MUST accept `--yes` (auto-confirm all prompts) and `--non-interactive` (fail immediately with exit code 4 if any prompt would be shown). The framework MUST register these flags automatically for any command that declares it uses interactive prompts. Command authors MUST declare prompt usage in registration metadata.

## Acceptance Criteria

- A command that prompts for confirmation in interactive mode accepts `--yes` and proceeds without prompting
- With `--non-interactive`, a command that would prompt exits with exit code 4 and a JSON error
- The `--yes` flag is idempotent: passing it to a command that never prompts has no effect
- The `--schema` output for interactive commands includes `interactive: true`

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

The `interactive` boolean and the standard `--yes` / `--non-interactive` flags appear in the command's schema entry.

```json
{
  "interactive": {
    "type": "boolean",
    "description": "True if the command may prompt for user input in a TTY context"
  }
}
```

---

## Wire Format

```bash
$ tool delete-account --user 42 --schema
```

```json
{
  "command": "delete-account",
  "interactive": true,
  "flags": {
    "user":            { "type": "integer", "required": true,  "description": "User ID to delete" },
    "yes":             { "type": "boolean", "required": false, "default": false, "description": "Auto-confirm all prompts" },
    "non-interactive": { "type": "boolean", "required": false, "default": false, "description": "Fail immediately if a prompt would be shown" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",      "description": "Account deleted",                     "retryable": false, "side_effects": "complete" },
    "4": { "name": "PRECONDITION", "description": "Prompt required but non-interactive mode is active", "retryable": false, "side_effects": "none" }
  }
}
```

---

## Example

A command that would prompt for confirmation in interactive mode declares `interactive: true` at registration. The framework auto-registers `--yes` and `--non-interactive`.

```
register command "delete-account":
  interactive: true
  danger_level: destructive
  exit_codes:
    SUCCESS    (0): description: "Account deleted",                               retryable: false, side_effects: complete
    PRECONDITION(4): description: "Prompt required but non-interactive mode is active", retryable: false, side_effects: none

  execute(args, interactive_context):
    if not args.yes and interactive_context.is_tty():
      confirmed = prompt("Delete user {}? [y/N]".format(args.user))
      if not confirmed:
        return response(ok=False, exit=PRECONDITION)
    delete_user(args.user)
    return response(effect="deleted")

# agent call — no prompt, no hang:
# tool delete-account --user 42 --yes
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: framework auto-detects non-TTY and suppresses prompts globally |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Composes: destructive commands are the primary case requiring interactive confirmation |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Composes: `--dry-run` is the preview step before the `--yes`-confirmed live run |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Extends: `--confirm-destructive` is a stronger opt-in variant for destructive confirmation |
