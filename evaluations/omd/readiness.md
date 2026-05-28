# CLI Agent Readiness Report — omd

**Generated:** 2026-05-28T07:44:55Z
**CLI version:** `omd 0.1.1`
**Depth:** full

## Readiness Score: 12/15  [B]

| Dimension | Score | Key finding |
|---|---|---|
| 1. Documentation Quality | 2/3 | `AGENTS.md` documents agent-first design and invocation, but install, env vars, and non-interactive auth are split across README/help rather than complete in `AGENTS.md`. |
| 2. Self-Description | 2/3 | `--schema` returns valid JSON with commands, typed options, capabilities, and `etag`, but it is not a complete ManifestResponse-style contract with top-level `flags` and `exit_codes`. |
| 3. Pre-built Integrations | 3/3 | MCP mode and bundled `.agents/skills` are shipped in the same Cargo package as the CLI binary. |
| 4. Setup Reproducibility | 2/3 | Non-interactive Cargo build/install paths are documented and `--version` verifies, but AGENTS.md lacks a complete install plus health-check section. |
| 5. Workflow Coverage | 3/3 | Skills, playbooks, use-cases, and README examples cover read and mutation workflows; `omd --schema` was verified successfully. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

---

## Dimension Details

### 1. Documentation Quality — 2/3

Evidence:
- `AGENTS.md` identifies the binary name, canonical local invocation forms (`cargo run -- <args>`, `./target/debug/omd <args>`), schema-first guidance, output behavior, and security posture.
- README documents install/build, `OMD_HOST`, `OMD_TOKEN`, `--headless`, `--token-env-var`, `--output json`, and `--format json`.
- `./target/debug/omd --help` confirms the documented global flags: `--host`, `--token`, `--timeout`, `--output`, `--format`, `--schema`, `--skills`, `--quiet`, and `--verbose`.

Gap:
- The agent-facing `AGENTS.md` is written primarily for coding agents modifying the repo. It does not itself contain a complete install/runbook section with canonical production invocation, all env vars, non-interactive auth, and input conventions in one place.

### 2. Self-Description — 2/3

Evidence:
- `./target/debug/omd --schema` exits 0 and returns valid JSON with `schema_version`, `cli_name`, `cli_version`, and commands.
- `./target/debug/omd search --schema` returns a scoped schema with typed options, positionals, capabilities, transport metadata, and an `etag`.
- `./target/debug/omd --skills` returns valid JSON for bundled skills.

Gap:
- The root schema is compact and incomplete for a full ManifestResponse contract: it omits top-level typed `flags` and `exit_codes`.
- Scoped command schema includes typed options but still does not expose exit-code mapping for the command.

### 3. Pre-built Integrations — 3/3

Evidence:
- `omd mcp` is a first-class subcommand implemented in `src/mcp.rs`.
- MCP client examples are present in `examples/mcp/`.
- Bundled agent skills are present under `.agents/skills/`.
- `Cargo.toml` includes `.agents/skills/**/*.md` in the package include list and the MCP server dependency is in the same Cargo package as `omd`, so the integration artifacts are co-versioned with the binary.
- `./target/debug/omd --skills` exits 0 and returns a machine-readable skills index.

### 4. Setup Reproducibility — 2/3

Evidence:
- README documents `cargo install --git https://github.com/Romamo/openmetadata-cli` and local `cargo build` usage.
- `cargo build` completed successfully.
- `./target/debug/omd --version` exits 0 with `omd 0.1.1`.
- Dependencies are explicitly declared in `Cargo.toml` and locked in `Cargo.lock`.

Gap:
- AGENTS.md includes build commands but not a complete non-interactive install plus verify command section.
- I did not run `cargo install --git` twice because the local source build already produced the audit binary and a global install would mutate user-level Cargo state.

### 5. Workflow Coverage — 3/3

Evidence:
- README includes common read workflows: search, get, lineage, and CSV export.
- `.agents/skills/` includes workflow-specific guidance for discovery, reading details, tracing lineage, applying metadata changes, bulk CSV edits, MCP setup, and auth verification.
- `docs/playbooks/` and `use-cases/` provide multi-step workflows, including discover -> dry-run -> execute -> verify patterns for mutations.
- `./target/debug/omd --schema` was run verbatim from the README's agent-first guidance and exited 0 with valid JSON.
