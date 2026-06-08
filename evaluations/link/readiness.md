# CLI Agent Readiness Report — link-cli

**Generated:** 2026-06-08
**CLI version:** 0.7.1
**Depth:** full

## Readiness Score: 10/15  [B]

| Dimension | Score | Key finding |
|---|---:|---|
| 1. Documentation Quality | 1/3 | README and skill docs are agent-focused, but the repo has no `AGENTS.md` with canonical invocation, env vars, and input conventions. |
| 2. Self-Description | 1/3 | `--llms-full`, `--help`, and command-level `--schema` are structured for humans/LLMs, but no root machine-readable JSON manifest validates as commands/flags/exit codes. |
| 3. Pre-built Integrations | 3/3 | MCP, Codex plugin metadata, and a bundled skill are present and co-versioned with the repo/CLI package. |
| 4. Setup Reproducibility | 2/3 | `npm install -g @stripe/link-cli` is documented, non-interactive, idempotent, and `--version` verifies; setup guidance is not in `AGENTS.md`. |
| 5. Workflow Coverage | 3/3 | README and the bundled skill document full authentication, payment-method, spend-request, credential retrieval, and MPP workflows. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

---

## Dimension Details

### 1. Documentation Quality — 1/3

No `AGENTS.md` or `CODING_AGENTS.md` exists in the repository. `README.md` includes installation, agent usage, output formats, MCP setup, authentication, spend-request lifecycle, polling, limits, and examples. `CLAUDE.md` provides development and command guidance, and `skills/create-payment-credential/SKILL.md` is strong agent-facing workflow documentation.

The score stays at 1 because the readiness rubric requires `AGENTS.md` for scores 2-3.

### 2. Self-Description — 1/3

Tried:

- `link-cli --schema`: returned top-level help, not JSON.
- `link-cli manifest`: unavailable.
- `link-cli --manifest`: unavailable.
- `link-cli --llms-full`: returned a structured Markdown command tree.
- `link-cli spend-request create --schema`: returned a schema-like text format, not JSON.

The CLI is discoverable, but it does not expose a machine-readable manifest with `commands`, `flags`, `exit_codes`, and `etag`.

### 3. Pre-built Integrations — 3/3

Found:

- `.mcp.json` with an MCP server command: `npx @stripe/link-cli --mcp`.
- `link-cli --mcp` built into the same CLI binary.
- `.codex-plugin/plugin.json` pointing to local skills and MCP configuration.
- `skills/create-payment-credential/SKILL.md`.

These artifacts live in the same source repository as `packages/cli/package.json` version `0.7.1`, and the package exposes MCP directly through the same binary, so drift risk is low by construction.

### 4. Setup Reproducibility — 2/3

Documented install command:

```bash
npm install -g @stripe/link
```

Verification:

```bash
link --version
```

Observed version: `0.7.1`. The install command completed non-interactively and a second install is idempotent for npm global packages. Dependencies are declared in `packages/cli/package.json`, with monorepo lockfiles present.

The score is 2 because install and verify instructions are not centralized in `AGENTS.md`.

### 5. Workflow Coverage — 3/3

The README and bundled skill cover realistic end-to-end workflows:

- auth status/login/logout
- payment-method listing
- shipping-address listing
- spend-request create/update/retrieve/request-approval/cancel
- card credential handoff with `--output-file`
- MPP challenge decoding and payment execution
- polling with `--interval`, `--timeout`, and `--max-attempts`

Verified read-only example with workspace-local auth storage:

```bash
LINK_AUTH_FILE=/Users/roman/Documents/Link-cli/source/tmp/link-auth.json link auth status --format json
```

It exited 0 and returned `authenticated: false` with the explicit credential path.
