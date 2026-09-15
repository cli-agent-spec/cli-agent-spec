# temporal — Readiness

**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Date:** 2026-07-07
**Depth:** full
**Total:** 3/15  [F]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | Built-in help has examples, but no local AGENTS.md/README agent guidance was present |
| Self-Description | 1/3 | Help is structured, but `--schema`, `manifest`, and `--manifest` are absent |
| Pre-built Integrations | 0/3 | No MCP/OpenAPI/skill/workflow artifacts found in the audit workspace |
| Setup Reproducibility | 0/3 | No local non-interactive install documentation was available to verify idempotently |
| Workflow Coverage | 1/3 | Basic command examples exist in help, but no agent-ready multi-step workflows were available locally |

---

## Dimension Details

### 1. Documentation Quality — 1/3

No AGENTS.md, CODING_AGENTS.md, README.md, or package manifest existed in the audit workspace. The CLI's built-in help includes examples such as starting a dev server and workflow commands, but it does not provide agent-specific invocation rules, non-interactive defaults, or environment conventions in a local agent-facing doc.

### 2. Self-Description — 1/3

`temporal --schema`, `temporal manifest`, and `temporal --manifest` all failed as unknown. `temporal --help` is structured enough to discover commands and flags, but there is no machine-readable manifest with commands, typed flags, or exit codes.

### 3. Pre-built Integrations — 0/3

No MCP server config, OpenAPI spec, Claude skill, LangChain/LlamaIndex tool, recipes, or workflow artifacts were found under the audit workspace.

### 4. Setup Reproducibility — 0/3

The installed binary verifies with `temporal --version`, but the audit inputs did not include local install instructions. No documented non-interactive, idempotent install command was available to run twice.

### 5. Workflow Coverage — 1/3

Built-in help contains examples for commands such as `server start-dev`, `workflow list`, `workflow start`, and `activity complete --help`. A documented read-only help example exited 0, but no local multi-step workflow documentation or agent-specific examples were present.

---

## Recommended Improvements

### Documentation Quality — currently 1/3

**To reach 2/3:** Add AGENTS.md with canonical invocation, non-interactive flags, config/env conventions, and input rules.
**To reach 3/3:** Validate AGENTS.md against CLI help in CI so documented flags do not drift.

### Self-Description — currently 1/3

**To reach 2/3:** Add a JSON manifest command that lists commands, flags, and exit codes.
**To reach 3/3:** Include full command schemas, etag/version metadata, auth scopes, and exit-code mappings.

### Setup Reproducibility — currently 0/3

**To reach 1/3:** Document one non-interactive install path in README or AGENTS.md.
**To reach 3/3:** Make the documented install idempotent and pair it with `temporal --version` or `temporal doctor --json`.

---

## Related failure modes

| §N | Title | Severity | Readiness dimension |
|---|---|---|
| §44 | Agent Knowledge Packaging Absence | Medium | Documentation Quality |
| §52 | Recursive Command Tree Discovery Cost | Medium | Self-Description |
| §21 | Schema & Help Discoverability | Medium | Self-Description |
| §47 | MCP Wrapper Schema Staleness | High | Pre-built Integrations |
| §20 | Environment & Dependency Discovery | Medium | Setup Reproducibility |
