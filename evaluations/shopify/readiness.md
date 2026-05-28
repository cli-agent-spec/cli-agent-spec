# CLI Agent Readiness Report — shopify

**Generated:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Depth:** full

## Readiness Score: 6/15  [D]

| Dimension | Score | Key finding |
|---|---:|---|
| 1. Documentation Quality | 1/3 | Official docs and package README cover install and basic usage, but there is no `AGENTS.md` or agent-specific invocation guidance. |
| 2. Self-Description | 2/3 | `shopify commands --json` returns parseable command and typed flag metadata, but `--schema`, `manifest`, and `--manifest` are not supported and no exit-code map or `etag` is exposed. |
| 3. Pre-built Integrations | 0/3 | No MCP server, OpenAPI spec, Claude skill, agent config, LangChain/LlamaIndex tool, or workflow recipe artifact was found in the installed package. |
| 4. Setup Reproducibility | 2/3 | `npm install -g @shopify/cli@latest --no-fund --no-audit` is documented, non-interactive, idempotent after npm completes, dependencies are declared, and `shopify --version` verifies the install. |
| 5. Workflow Coverage | 1/3 | Basic workflow commands and examples exist, but realistic app/theme/store workflows require auth, stores, app IDs, project files, or human-specific values and do not consistently document non-interactive agent paths. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

## Notes

- Documentation source checked: Shopify CLI docs at `https://shopify.dev/docs/api/shopify-cli`, installed package `README.md`, and `shopify help`.
- Schema probes:
  - `shopify --schema` exited 1: command not found.
  - `shopify manifest` exited 1: command not found.
  - `shopify --manifest` exited 1: command not found.
  - `shopify commands --json` exited 0 and returned JSON command metadata including command IDs, summaries, flags, flag types, environment variable bindings, aliases, plugin names, and strictness.
- Integration artifact scan under `/opt/homebrew/lib/node_modules/@shopify/cli` found no MCP, OpenAPI, Claude skill, agent recipe, or workflow artifact. The package does include `oclif.manifest.json`, which is useful for CLI self-description but is not a pre-built agent integration.
- Install idempotency check: a second `npm install -g @shopify/cli@latest --no-fund --no-audit` completed successfully. A simultaneous `shopify version` probe failed while npm was replacing files, then succeeded after npm completed; this was treated as an installation race observation, not a persistent install failure.
- Verified read-only example: `shopify version` exited 0 and returned `4.1.0`.
