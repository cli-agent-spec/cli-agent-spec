# Readiness — gh

**CLI version:** 2.88.1
**Date:** 2026-05-07
**Total:** 7/15  [D]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | No AGENTS.md; README in brew package only; examples exist but no agent-specific guidance |
| Self-Description | 1/3 | --help is structured and parseable; no --schema or manifest command |
| Pre-built Integrations | 1/3 | No MCP server, OpenAPI spec, or skill files; completions (zsh/fish) only |
| Setup Reproducibility | 3/3 | `brew install gh` is idempotent (second run exits 0); `gh --version` verifies |
| Workflow Coverage | 1/3 | Examples exist per command; no multi-step agent workflows; --json flag works; non-interactive flags missing from examples |
