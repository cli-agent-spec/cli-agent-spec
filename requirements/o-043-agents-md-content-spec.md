# REQ-O-043: AGENTS.md Required Content

**Tier:** Opt-In | **Priority:** P1

**Source:** [§44 Agent Knowledge Packaging Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) · [§73 Documentation Accuracy Drift](../challenges/01-critical-ecosystem-runtime-agent-specific/73-high-documentation-accuracy-drift.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: High

---

## Description

When a CLI ships AGENTS.md, it MUST contain four required sections: (1) canonical invocation — the exact command prefix agents must use; (2) non-interactive flags — every flag that suppresses prompts or enables headless operation; (3) environment variables — every env var the CLI reads, with type and purpose; (4) input conventions — how the CLI accepts structured input (stdin, `--json`, `--input-file`). Each section MUST be accurate against the current binary — the AGENTS.md MUST include a `<!-- cli-version: X.Y.Z -->` comment matching `<binary> --version` output exactly.

## Acceptance Criteria

- AGENTS.md contains a `## Canonical Invocation` section with the exact command string agents use
- AGENTS.md contains a `## Non-Interactive Flags` section listing all flags that suppress prompts (e.g. `--yes`, `--non-interactive`, `--force`, `--no-pager`)
- AGENTS.md contains an `## Environment Variables` section listing every env var the CLI reads, with type and description
- AGENTS.md contains an `## Input Conventions` section describing how structured input is passed (flags, stdin, file)
- AGENTS.md includes `<!-- cli-version: X.Y.Z -->` on line 1, matching `<binary> --version` output
- Every flag, command, and env var documented in AGENTS.md is present and correctly named in `<binary> --help` output

---

## Schema

**Types:** none — AGENTS.md is a freeform Markdown document with required sections

---

## Wire Format

```markdown
<!-- cli-version: 2.1.0 -->
<!-- last-validated: 2026-04-01 -->
# AGENTS.md — <tool-name>

## Canonical Invocation
<exact command prefix>

## Non-Interactive Flags
- `--yes`: auto-confirms all prompts
- `--non-interactive`: exits 4 if any prompt would be shown
- `--no-pager`: suppresses pager for long output

## Environment Variables
- `MY_TOOL_TOKEN` (string, required): API authentication token
- `MY_TOOL_TIMEOUT` (integer, optional, default 30): request timeout in seconds

## Input Conventions
Structured input is passed via `--json` flag or `--input-file <path>`.
Stdin is not read unless `--stdin` is explicitly passed.
```

---

## Example

```bash
$ cat AGENTS.md | head -1
<!-- cli-version: 2.1.0 -->

$ my-cli --version
2.1.0   # versions match → AGENTS.md is current
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-034](o-034-tool-generate-skills-built-in-command.md) | O | Composes: generate-skills can produce AGENTS.md from registered schemas |
| [REQ-O-046](o-046-agents-md-ci-validation.md) | O | Enforces: CI gate validates AGENTS.md content against live --help |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Sources: non-interactive flags documented in AGENTS.md must be registered with the framework |
