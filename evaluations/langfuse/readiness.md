# CLI Agent Readiness Report — langfuse

**Generated:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Depth:** full

## Readiness Score: 9/15  [C]

| Dimension | Score | Key finding |
|---|---:|---|
| 1. Documentation Quality | 1/3 | README has CLI examples, env vars, and agent-skill mention, but no `AGENTS.md` with canonical agent invocation/input conventions. |
| 2. Self-Description | 2/3 | `langfuse api __schema --json` returns machine-readable resource metadata, but no top-level manifest with typed commands, flags, and exit codes. |
| 3. Pre-built Integrations | 3/3 | Bundled `openapi.yml` is shipped in the same npm package as the CLI and drives the generated API command surface. |
| 4. Setup Reproducibility | 2/3 | npm/npx install paths are non-interactive and idempotent locally, with dependencies declared in `package.json`; no `AGENTS.md` health-check guidance. |
| 5. Workflow Coverage | 1/3 | Basic discovery/read/create examples exist, but most real workflows require project credentials and there is no documented multi-step agent workflow. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

---

## Dimension Details

### 1. Documentation Quality — 1/3

No `AGENTS.md` or `CODING_AGENTS.md` is present in the project or npm package. The README documents install commands, credentials, host configuration, API discovery, JSON output, curl preview, and a `get-skill` command for agent context. It does not provide a complete agent contract with canonical invocation, non-interactive policy, stdin behavior, expected exit codes, or input conventions.

### 2. Self-Description — 2/3

Tried `./node_modules/.bin/langfuse --schema`, `./node_modules/.bin/langfuse manifest`, and `./node_modules/.bin/langfuse --manifest`; each exited 0 but printed normal help rather than JSON. `./node_modules/.bin/langfuse api __schema --json` returned valid JSON with OpenAPI title/version, auth schemes, resources, and action counts. It does not expose a full CLI manifest with typed commands, flags, argument schemas, or exit-code mappings.

### 3. Pre-built Integrations — 3/3

Found `node_modules/langfuse-cli/openapi.yml` inside the same npm package as the `langfuse` binary. The CLI also exposes `api __schema` and `api __schema --json`, indicating the bundled OpenAPI metadata is functional. Co-versioning is confirmed by same-package distribution with `langfuse-cli` 0.0.10. The README also points to `langfuse get-skill`, but that skill is fetched from GitHub at runtime and is not co-versioned with the installed package.

### 4. Setup Reproducibility — 2/3

Documented install paths are `npx langfuse-cli`, `bunx langfuse-cli`, or `npm i -g langfuse-cli`. For this audit, `npm install langfuse-cli --save-dev --no-fund --no-audit` installed the CLI locally, and a second `npm install` completed idempotently. Dependencies are declared in `node_modules/langfuse-cli/package.json`, and the local binary exits 0 for help/version-style invocation. A dedicated `doctor` command or `AGENTS.md` health check is not documented.

### 5. Workflow Coverage — 1/3

The README includes discovery (`langfuse api __schema`), resource help, traces/prompts reads, datasets and scores creation, JSON output, and curl preview examples. The simplest documented read-only command, `./node_modules/.bin/langfuse api __schema`, exits 0. Real data workflows require project-specific credentials and IDs, and the docs do not provide a complete multi-step workflow that an agent can run verbatim from setup through verification.
