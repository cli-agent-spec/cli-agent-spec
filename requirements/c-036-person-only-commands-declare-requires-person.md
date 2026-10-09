# REQ-C-036: Person-Only Commands Declare requires_person

**Tier:** Command Contract | **Priority:** P1

**Source:** [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) · [§23 Side Effects & Destructive Operations](../challenges/03-critical-security/23-critical-destructive-ops.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: High / Context: Medium

---

## Description

Every other prompt the spec allows has an agent alternative: [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) fails a prompt off a terminal, and [REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md) lets `--yes` answer it. A few steps exist precisely so that a person, not the calling agent, takes them: approving a change an agent proposed, accepting a release, granting an agent a permission. Any answer an agent can pass as a flag defeats such a step, so a command whose confirmation only a person may give MUST declare `requires_person: true` at registration, together with `interactive: true` ([REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md)) and `mcp: false` ([REQ-C-032](c-032-protocol-server-commands-declare-stdout-protocol.md)). The framework refuses to register `requires_person: true` without both, and the manifest schema rejects the same combination.

**The attestation.** Before the command does anything, the framework shows a statement of what the person is confirming and asks them to type back an expected string the command chooses, such as the ID of the change being approved. It asks only when both stdin and stdout are terminals and `--non-interactive` is absent. No flag or environment variable answers it: `--yes`, `--confirm-destructive` ([REQ-O-021](o-021-confirm-destructive-flag.md)), and a `confirm_flag` ([REQ-O-048](o-048-destructive-commands-default-dry-run.md)) leave the attestation in place. This is the one exception to REQ-C-005's `--yes`.

**Off a terminal.** When stdin or stdout is not a terminal, or `--non-interactive` is present, the command exits `4` (`PRECONDITION`) with `error.code: "PERSON_REQUIRED"` in place of REQ-F-009's `INPUT_REQUIRED`, `retryable: false`, and nothing done. Its `suggestion` says to hand the command to a person and names no flag; the error carries no `fix_command`, since no command an agent runs resolves it.

**A wrong answer.** When the typed string differs from the expected one, the command exits `4` (`PRECONDITION`) with `error.code: "ATTESTATION_MISMATCH"`, `retryable: false`, and nothing done.

The command's `PRECONDITION (4)` entry is `retryable: false, side_effects: "none"` and lists both codes in `error_codes` ([REQ-C-001](c-001-command-declares-exit-codes.md)).

**Never an MCP tool.** `mcp: false` keeps the command off the tool's own MCP server, where no terminal and no person stands behind the call.

**Non-goal.** `requires_person` is a speed bump and an honest record, not a security boundary. An agent running as the same OS user can fake a terminal, for example by starting the command under a pseudo-terminal and typing the expected string. A step that must hold against such an agent runs as a separate OS user, or behind a credential the agent does not have; this requirement makes a well-behaved agent stop and ask, and makes an agent that works around it do so on purpose.

## Acceptance Criteria

- `tool manifest` shows `requires_person: true`, `interactive: true`, and `mcp: false` on every person-only command, and no `requires_person` field on any other command
- The framework rejects at registration a command that declares `requires_person: true` without `interactive: true` or without `mcp: false`
- With stdin and stdout both terminals and no `--non-interactive`, the command asks for the expected string and runs only after the person types it exactly
- `--yes`, `--confirm-destructive`, or the command's `confirm_flag` on the command line does not skip the attestation
- With stdin redirected from `/dev/null`, with stdout piped, or with `--non-interactive`, the command exits `4` with `error.code: "PERSON_REQUIRED"` and `retryable: false`, and nothing changes
- The `PERSON_REQUIRED` error's `suggestion` names no flag, and the error carries no `fix_command`
- A typed string that differs from the expected one exits `4` with `error.code: "ATTESTATION_MISMATCH"`, and nothing changes
- The command's `PRECONDITION (4)` entry lists `PERSON_REQUIRED` and `ATTESTATION_MISMATCH` in `error_codes`
- The tool's MCP server lists no command marked `requires_person: true`
- A manifest with `requires_person: true` and no `mcp: false`, or with `interactive` absent or `false`, fails validation against the manifest schema

---

## Schema

**Types:**

- [`manifest-response.md`](../schemas/manifest-response.md): `requires_person` (`true` only; absent means an agent may confirm the command) on `CommandEntry`, requiring `interactive: true` and `mcp: false`
- [`exit-code-entry.md`](../schemas/exit-code-entry.md): the `PRECONDITION (4)` entry lists `PERSON_REQUIRED` and `ATTESTATION_MISMATCH` in `error_codes`
- [`response-envelope.md`](../schemas/response-envelope.md): the failure envelope, with `error.code` `PERSON_REQUIRED` or `ATTESTATION_MISMATCH`

```json
{
  "requires_person": {
    "type": "boolean",
    "const": true,
    "description": "A person confirms the command by typing back an expected string at a terminal; no flag answers the prompt"
  }
}
```

---

## Wire Format

Manifest entry:

```json
{
  "schema_version": "3.21",
  "framework_version": "2.5.0",
  "etag": "sha256:3e8a51",
  "commands": {
    "decisions.approve": {
      "description": "Record a person's approval of a decision an agent proposed",
      "danger_level": "mutating",
      "required_scopes": ["decisions:approve"],
      "interactive": true,
      "mcp": false,
      "requires_person": true,
      "flags": {},
      "positionals": [{ "name": "id", "type": "string", "required": true, "description": "ID of the decision to approve" }],
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "The approval is recorded", "retryable": false, "side_effects": "complete" },
        "4": { "name": "PRECONDITION", "description": "No person confirmed the approval at a terminal; nothing is recorded", "retryable": false, "side_effects": "none", "error_codes": ["PERSON_REQUIRED", "ATTESTATION_MISMATCH"] }
      }
    }
  }
}
```

An agent calls it from a shell, with `--yes`:

```bash
$ tool --format json decisions approve D-42 --yes </dev/null
```

```json
{"ok": false, "data": null, "error": {"code": "PERSON_REQUIRED", "message": "Approving a decision needs a person at a terminal", "retryable": false, "suggestion": "Ask a person to run `tool decisions approve D-42` in their own terminal"}, "warnings": [], "meta": {"exit_code": 4, "duration_ms": 6}}
```

A person at a terminal types the wrong ID:

```json
{"ok": false, "data": null, "error": {"code": "ATTESTATION_MISMATCH", "message": "The typed text does not match D-42; nothing is recorded", "retryable": false}, "warnings": [], "meta": {"exit_code": 4, "duration_ms": 8120}}
```

---

## Example

```
register command "decisions.approve":
  requires_person: true
  interactive: true
  mcp: false
  danger_level: mutating
  exit_codes:
    SUCCESS     (0): description: "The approval is recorded", retryable: false, side_effects: complete
    PRECONDITION(4): description: "No person confirmed the approval at a terminal; nothing is recorded",
                     retryable: false, side_effects: none, error_codes: [PERSON_REQUIRED, ATTESTATION_MISMATCH]

  execute(args, ctx):
    # off a terminal or under --non-interactive: exit 4, PERSON_REQUIRED, before this line runs
    # --yes does not answer it
    ctx.attest("Approve decision {}? Type its ID to confirm".format(args.id), expected=args.id)
    record_approval(args.id)
    return response(effect="approved")

# Agent consults the manifest before calling:
# requires_person: true → hand `tool decisions approve D-42` to a person; never add --yes
# Exit 4 with PERSON_REQUIRED → stop; never retry, with or without flags
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md) | C | Specializes: the one prompt `--yes` does not answer |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Specializes: off a terminal, the prompt fails with `PERSON_REQUIRED` instead of `INPUT_REQUIRED` |
| [REQ-C-032](c-032-protocol-server-commands-declare-stdout-protocol.md) | C | Consumes: `mcp: false` keeps the command off the tool's MCP server |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Consumes: exit `4` `PRECONDITION` for both failures |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Consumes: the `PRECONDITION (4)` entry lists both codes in `error_codes` |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | C | Consumes: `code`, `message`, and a `suggestion` that names no flag |
| [REQ-O-021](o-021-confirm-destructive-flag.md) | O | Composes: `--confirm-destructive` does not answer the attestation either |
| [REQ-O-048](o-048-destructive-commands-default-dry-run.md) | O | Composes: a `confirm_flag` runs the command instead of previewing it, and the attestation still follows |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `requires_person` appears in the manifest |
