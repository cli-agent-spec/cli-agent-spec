# CLI Agent Readiness Report — dokploy

**Generated:** 2026-05-26
**CLI version:** 0.3.0
**Depth:** full

## Readiness Score: 7/15  [C]

| Dimension | Score | Key finding |
|---|---:|---|
| 1. Documentation Quality | 1/3 | README has install, auth, env vars, and examples, but no agent-specific contract. |
| 2. Self-Description | 1/3 | Help is structured enough for humans, but no machine-readable schema or manifest exists. |
| 3. Pre-built Integrations | 2/3 | Source repo includes `openapi.json`, but it is not exposed as a CLI manifest and co-versioning with the installed binary is unclear. |
| 4. Setup Reproducibility | 2/3 | `npm install -g @dokploy/cli` is non-interactive and idempotent; verification is not documented in AGENTS.md. |
| 5. Workflow Coverage | 1/3 | README examples cover common operations, but they require live IDs/credentials and no runnable multi-step agent workflow is provided. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

---

## Dimension Details

### 1. Documentation Quality — 1/3

No `AGENTS.md` or `CODING_AGENTS.md` exists. The README documents installation, `dokploy auth`, environment variables, `.env`, command shape, examples, `--json`, and help discovery. It does not define canonical agent invocation, non-interactive guarantees, exit codes, timeout policy, auth scope expectations, or output envelopes.

### 2. Self-Description — 1/3

`dokploy --schema`, `dokploy manifest`, and `dokploy --manifest` are not supported. Top-level and subcommand help are structured Commander output, but they are prose, omit exit codes, and do not expose command metadata such as auth requirements, danger level, idempotency, or required credential scopes.

### 3. Pre-built Integrations — 2/3

The source repo includes `openapi.json` and generated commands. This is useful for agents and covers the API surface, but the installed npm package only declares `/dist` in `files`, so the OpenAPI artifact is not shipped as an installed CLI integration artifact. The OpenAPI document version is `1.0.0` while the installed package reports `0.29.4` and the binary reports `0.3.0`, so co-versioning is not proven.

### 4. Setup Reproducibility — 2/3

`npm install -g @dokploy/cli --no-fund --no-audit` completed without prompts, and `dokploy --version` exits 0. A second global install also exits 0. Dependencies are declared in `package.json`. There is no AGENTS.md install contract and no documented health-check/doctor command.

### 5. Workflow Coverage — 1/3

The README includes examples for listing projects, fetching one project, creating/deploying an application, creating/stopping a Postgres database, and JSON output. The examples depend on real IDs and credentials and do not form a complete copy-pasteable workflow with setup, validation, error handling, and teardown.
