# REQ-O-044: Non-Interactive Install Command Documentation

**Tier:** Opt-In | **Priority:** P1

**Source:** [§71 Non-Interactive Installation Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/71-critical-noninteractive-installation.md)

**Addresses:** Severity: Critical / Token Spend: Low / Time: Critical / Context: Low

---

## Description

A CLI MUST document a fully non-interactive, idempotent installation command in AGENTS.md under an `## Installation` section. The command MUST complete without reading stdin, without requiring browser interaction, and without prompting for any confirmation. Running the command a second time MUST exit 0 (idempotent). A verification command (minimally `<binary> --version`) MUST be documented immediately after the install command so agents can confirm successful installation.

## Acceptance Criteria

- AGENTS.md contains an `## Installation` section
- The documented install command exits 0 without stdin input (`< /dev/null`)
- The documented install command exits 0 when run a second time on an already-installed binary (idempotent)
- A verification command is documented that exits 0 and prints a parseable version string after successful install
- The install command does not open a browser, launch a GUI, or invoke an interactive wizard

---

## Schema

**Types:** none — documented in AGENTS.md `## Installation` section

---

## Wire Format

```markdown
## Installation

```bash
pip install my-cli==2.1.0    # non-interactive, idempotent
my-cli --version              # verify: prints "2.1.0", exits 0
```

> Agent note: set `PIP_NO_INPUT=1` and `CI=true` before running install.
```

---

## Example

```bash
# Agent runs install with stdin closed
$ pip install my-cli==2.1.0 < /dev/null
Successfully installed my-cli-2.1.0   # exits 0

# Agent verifies
$ my-cli --version
2.1.0   # parseable version string, exits 0

# Agent confirms idempotency
$ pip install my-cli==2.1.0 < /dev/null
Requirement already satisfied: my-cli==2.1.0   # exits 0
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-043](o-043-agents-md-content-spec.md) | O | Extends: Installation section is one of the required AGENTS.md sections |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: non-interactive mode must work once the CLI is installed |
| [REQ-C-005](c-005-interactive-commands-must-support-yes-non-interact.md) | C | Composes: --non-interactive flag must work for post-install first-run flows |
