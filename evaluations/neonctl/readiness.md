# neonctl — Readiness

**CLI version:** 2.22.2
**Date:** 2026-06-06
**Depth:** full
**Total:** 7/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | README and official docs include install, auth, output, and `link --agent`; no AGENTS.md with canonical agent invocation. |
| Self-Description | 1/3 | Help is structured and typed, but `--schema`, `--manifest`, and `manifest` do not return a machine-readable command schema. |
| Pre-built Integrations | 1/3 | `init` references MCP/extension/agent skills, but no co-versioned manifest or integration artifact was found in the package. |
| Setup Reproducibility | 2/3 | `npm i -g neonctl` is documented and worked non-interactively; package declares Node >=18 and `--version` verifies. |
| Workflow Coverage | 2/3 | `link --agent` is a documented multi-step JSON workflow; most other workflows remain human-oriented or require auth. |

---

## Dimension Details

### 1. Documentation Quality — 1/3

The installed README and Neon docs document installation, `--output`, `--api-key`, `NEON_API_KEY`, `--no-analytics`, and `link --agent`. There is no local AGENTS.md for the CLI package with canonical invocation, non-interactive defaults, input conventions, credential scope guidance, or timeout guidance.

### 2. Self-Description — 1/3

`neonctl --schema` and `neonctl --manifest` fell back to human help output. `neonctl manifest` returned `ERROR: Unknown command: manifest`. Help output is structured enough to parse flags and choices manually, but there is no JSON manifest with commands, flags, exit codes, auth scopes, danger levels, or output schemas.

### 3. Pre-built Integrations — 1/3

The README and `init` command describe MCP/extension/agent setup, and `link --agent` exposes a JSON state machine. However, no co-versioned MCP manifest, OpenAPI spec, skill artifact, or command schema file was found under the installed `neonctl` package. `init --agent cursor` produced terminal progress output and timed out during auth in the probe environment.

### 4. Setup Reproducibility — 2/3

The documented npm install command completed non-interactively and `neonctl --version` returned `2.22.2`. Dependencies are declared in `package.json`, including Node `>=18`. There is no AGENTS.md install recipe or documented health check beyond `--version`.

### 5. Workflow Coverage — 2/3

`link --agent` is well documented as a multi-step agent workflow with `status`, `options`, and `next_command_template`. CRUD command examples exist in help and docs, but most commands do not expose agent-specific structured envelopes, idempotency keys, dry-run behavior, or credential-scope preflights.

---

## Recommended Improvements

### Documentation Quality — currently 1/3

**To reach 2/3:** Add an AGENTS.md with canonical invocation, non-interactive flags, env vars, and safe config isolation.
**To reach 3/3:** Include input conventions, timeout policy, credential-scope recipes, and command examples verified against `--help`.

### Self-Description — currently 1/3

**To reach 2/3:** Add `neonctl --schema` or `neonctl manifest` returning JSON for commands and flags.
**To reach 3/3:** Include exit codes, required scopes, danger levels, output schemas, and an `etag`.

### Pre-built Integrations — currently 1/3

**To reach 2/3:** Ship a co-versioned MCP/agent manifest in the npm package.
**To reach 3/3:** Make the artifact cover all commands and validate that its version matches the CLI binary.

### Setup Reproducibility — currently 2/3

**To reach 3/3:** Document the install and verify commands in AGENTS.md and include a health-check command for agents.

### Workflow Coverage — currently 2/3

**To reach 3/3:** Extend the `--agent` JSON state-machine pattern beyond `link` to auth, init, create/update/delete, and recovery workflows.

---

## Related failure modes

| §N | Title | Severity | Readiness dimension |
|---|---|---|---|
| §44 | Agent Knowledge Packaging Absence | Medium | Documentation Quality |
| §52 | Recursive Command Tree Discovery Cost | Medium | Self-Description |
| §21 | Schema & Help Discoverability | Medium | Self-Description |
| §47 | MCP Wrapper Schema Staleness | High | Pre-built Integrations |
| §20 | Environment & Dependency Discovery | Medium | Setup Reproducibility |
