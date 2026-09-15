# cube — Readiness

**CLI version:** 1.7.16
**Date:** 2026-08-06
**Depth:** full
**Total:** 7/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | Official README and CLI reference are detailed and match `--help`, but no `AGENTS.md` packages canonical agent invocation, flags, environment, and input conventions together |
| Self-Description | 1/3 | Structured clap help is parseable; `--schema`, `manifest`, and `--manifest` are unsupported |
| Pre-built Integrations | 0/3 | The `cube-cli` package contains no MCP server, OpenAPI artifact, agent skill, tool wrapper, or packaged workflow recipes |
| Setup Reproducibility | 2/3 | Official non-interactive installer is documented, dependencies are declared in Cargo manifests, reinstall succeeded, and `--version` verifies the result; no `AGENTS.md` health-check guidance |
| Workflow Coverage | 3/3 | Docs cover authenticated read/create/update/delete flows and multi-step deployment/data-model workflows; `cube update --check` ran successfully without authentication |
