# firecrawl - Readiness

**CLI version:** 1.18.1
**Date:** 2026-05-27
**Depth:** full
**Total:** 7/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | Package README and public docs provide CLI examples and agent setup notes, but no AGENTS.md with canonical invocation, env vars, and input conventions. |
| Self-Description | 1/3 | --schema, manifest, and --manifest are absent; --help is structured but prose-only. |
| Pre-built Integrations | 1/3 | setup skills/workflows/mcp installers exist, but no co-versioned manifest/OpenAPI/MCP artifact is shipped in the package. |
| Setup Reproducibility | 2/3 | Non-interactive npm install is documented and local reinstall was idempotent; no AGENTS.md health-check path. |
| Workflow Coverage | 2/3 | Docs include many copy-paste examples and view-config ran successfully; authenticated workflows require credentials and lack structured non-interactive failure examples. |
