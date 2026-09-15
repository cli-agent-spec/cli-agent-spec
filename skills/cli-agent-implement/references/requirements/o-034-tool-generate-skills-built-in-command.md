# REQ-O-034: tool generate-skills Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§44 Agent Knowledge Packaging Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md)

**Addresses:** Severity: Medium / Token Spend: Medium / Time: Low / Context: High

---

## Description

The framework MUST provide a built-in `tool generate-skills` command that generates agent-consumable skill files from the registered command schemas. The command MUST produce: one `CONTEXT.md` file with a high-level overview of the tool, its commands, and agent-specific guidance; and one `SKILL-<command>.md` file per command with YAML frontmatter (name, description, version, args schema) and Markdown body (usage examples, guardrails, common patterns, anti-patterns). The output MUST be compatible with the OpenClaw skill format and loadable as Claude Code skills. The command MUST support `--output-dir <path>` and `--format <markdown|json>`.

## Acceptance Criteria

- `tool generate-skills --output-dir ./skills` creates `CONTEXT.md` and one `SKILL-*.md` per command
- Each skill file includes a YAML frontmatter block with command name, description, and argument schema
- Each skill file includes at least three example invocations derived from the command's `--schema` output
- The generated files pass validation by an OpenClaw-compatible skill loader

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data.skills` is an array of generated file descriptors with `path`, `command`, and `format`.

---

## Wire Format

```bash
$ tool generate-skills --output-dir ./skills --output json
```

```json
{
  "ok": true,
  "data": {
    "skills": [
      { "path": "./skills/CONTEXT.md", "type": "context" },
      { "path": "./skills/SKILL-deploy.md", "command": "deploy", "format": "markdown" },
      { "path": "./skills/SKILL-delete.md", "command": "delete", "format": "markdown" }
    ]
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 48 }
}
```

---

## Example

Opt-in at the framework level; auto-generates skills from registered command schemas.

```
app = Framework("tool")
app.enable_generate_skills()

# Generate skill files for all registered commands:
$ tool generate-skills --output-dir ./.claude/skills/tool/

# Generated CONTEXT.md and one SKILL-*.md per command, ready for Claude Code
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: input/output schemas that populate skill YAML frontmatter |
| [REQ-O-013](o-013-schema-output-schema-flag.md) | O | Provides: command schema data that `generate-skills` reads |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Composes: manifest provides the command tree that skill generation traverses |
