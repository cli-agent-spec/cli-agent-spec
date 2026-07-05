# neon - Readiness

**CLI version:** 2.30.1
**Date:** 2026-07-05
**Depth:** full
**Total:** 8/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 2/3 | Official docs and package README include invocation, output formats, API-key auth, and agent-mode guidance, but no local `AGENTS.md`. |
| Self-Description | 1/3 | No JSON schema/manifest command; `--help` is structured enough to parse commands and flag types. |
| Pre-built Integrations | 1/3 | Co-versioned `--agent` JSON state-machine modes exist for selected workflows, but no complete CLI-wide MCP/OpenAPI/manifest artifact was found. |
| Setup Reproducibility | 2/3 | `npm i -g neon` is documented, dependencies and Node engine are declared, `--version` verifies, and a second install succeeded. |
| Workflow Coverage | 2/3 | README/docs include multi-step examples and agent workflows, but several realistic examples require live credentials and a documented offline `link --no-checks` check entered browser auth. |

---

## Dimension Details

### 1. Documentation Quality - 2/3

The official Neon CLI documentation and installed package README document the canonical `neon` invocation, global `--output json|yaml|table`, `--api-key`/`NEON_API_KEY` authentication, `--context-file`, and agent-oriented `neon link --agent`. Spot checks against `/Users/roman/.hermes/node/bin/neon --help` and `neon link --help` confirmed those flags are present. No `AGENTS.md` or `CODING_AGENTS.md` was available in the audit workspace or installed package, which prevents a full score under this rubric.

### 2. Self-Description - 1/3

Tried `/Users/roman/.hermes/node/bin/neon --schema`, `/Users/roman/.hermes/node/bin/neon manifest`, and `/Users/roman/.hermes/node/bin/neon --manifest`. `manifest` exits non-zero as an unknown command. `--schema` and `--manifest` return ordinary help text with exit code 0 rather than a machine-readable `ManifestResponse`. The help output is structured and includes commands, flag names, types, choices, defaults, and aliases.

### 3. Pre-built Integrations - 1/3

No MCP config/server, OpenAPI spec file, Claude skill, LangChain/LlamaIndex wrapper, or complete workflow artifact was found in the installed package at `/Users/roman/.hermes/node/lib/node_modules/neon` within the scan depth. The package does include co-versioned agent-mode implementations for selected commands (`link`, `bootstrap`, `init`), but they do not cover the full CLI command surface.

### 4. Setup Reproducibility - 2/3

Install command documented by official docs and README: `npm i -g neon`. The installed `package.json` declares `node >=20.19.0`, package dependencies, and binary entries for `neon` and `neonctl`. `/Users/roman/.hermes/node/bin/neon --version` returned `2.30.1`. A second `npm install -g neon --no-fund --no-audit` completed successfully.

### 5. Workflow Coverage - 2/3

The README includes examples for linking, checkout, env pull, config/deploy, psql, and agent-mode JSON flows. `neon --help` was verified as a safe documented read-only example. A documented offline write example using `neon link --no-checks --org-id org-abc123 --project-id polished-snowflake-12345678` with a temporary context file unexpectedly entered browser authentication and was killed by timeout, so not all non-interactive examples verified.

---

## Recommended Improvements

### Documentation Quality - currently 2/3

**To reach 3/3:** Add an `AGENTS.md` or equivalent package artifact covering canonical invocation, non-interactive flags, env vars, input conventions, and safe examples for agents.

### Self-Description - currently 1/3

**To reach 2/3:** Add a `neon --manifest` or `neon --schema` command that returns JSON describing commands and flags.
**To reach 3/3:** Include typed command flags, exit-code mappings, and an `etag` in the manifest response.

### Pre-built Integrations - currently 1/3

**To reach 2/3:** Ship a complete machine-readable artifact covering at least 80% of commands, such as an MCP server or CLI manifest.
**To reach 3/3:** Co-version that artifact in the same npm package and validate it in release CI.

### Setup Reproducibility - currently 2/3

**To reach 3/3:** Document the install and health check in an agent-specific file, including `neon --version` and `NEON_API_KEY` setup.

### Workflow Coverage - currently 2/3

**To reach 3/3:** Provide a fully offline, credential-free workflow example that can be run verbatim in CI and does not enter browser authentication.

---

## Related failure modes

| Section | Title | Severity | Readiness dimension |
|---|---|---|---|
| §44 | Agent Knowledge Packaging Absence | Medium | Documentation Quality |
| §52 | Recursive Command Tree Discovery Cost | Medium | Self-Description |
| §21 | Schema & Help Discoverability | Medium | Self-Description |
| §47 | MCP Wrapper Schema Staleness | High | Pre-built Integrations |
| §20 | Environment & Dependency Discovery | Medium | Setup Reproducibility |
