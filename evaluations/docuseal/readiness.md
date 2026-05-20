# docuseal-cli - Readiness

**CLI version:** 1.0.3
**Date:** 2026-05-20
**Depth:** full
**Total:** 7/15  [C]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 1/3 | README has strong CLI examples, env vars, and non-interactive setup, but no AGENTS.md. |
| Self-Description | 1/3 | `--schema`, `manifest`, and `--manifest` are unsupported; prose help is structured but not machine-readable. |
| Pre-built Integrations | 1/3 | Bundled `skills/docuseal-cli` exists and covers workflows, but its metadata version is `1.0.6` while the CLI is `1.0.3`, and it claims output is always JSON despite observed prose/stack-trace failures. |
| Setup Reproducibility | 2/3 | README documents non-interactive npm install/use, `package.json` declares dependencies, `npm ci` is idempotent locally, and `--version` works; no AGENTS.md health-check setup path. |
| Workflow Coverage | 2/3 | README and skill examples cover read/create/update/archive workflows with placeholders and `-d` data syntax, but the simplest read example could not be verified without credentials. |

## Dimension Details

### 1. Documentation Quality - 1/3

No `AGENTS.md` or `CODING_AGENTS.md` exists. `README.md` includes installation, configuration, environment variables, non-interactive `configure --api-key --server`, global `--api-key`/`--server`, and many command examples. Spot checks against help passed for `--api-key`, `--server`, and `-d/--data`; the issue is placement and agent-specific completeness rather than factual flag drift in README.

### 2. Self-Description - 1/3

Tried `node bin/run.js --schema`, `node bin/run.js manifest`, and `node bin/run.js --manifest`; all failed as unknown option/command. Root and subcommand help is regular Commander output with readable flag names and types, but there is no JSON manifest, command tree, typed parameter schema, exit-code map, or `etag`.

### 3. Pre-built Integrations - 1/3

Found `skills/docuseal-cli/SKILL.md` plus reference files under `skills/docuseal-cli/references/`, and `package.json` includes `skills` in published files. The artifact is useful and covers the three command groups, but the skill metadata version is `1.0.6` while the binary/package version is `1.0.3`. It also says "Output is always JSON", which does not match observed `configure` prose output and stack traces for auth/file/JSON errors.

### 4. Setup Reproducibility - 2/3

README documents `npx docuseal configure` and `npm install -g docuseal`; both are non-interactive as install commands, though `configure` itself is interactive unless `--api-key` and `--server` are supplied. `package.json` declares dependencies. `node bin/run.js --version` returned `1.0.3`. A second local `npm ci` run completed successfully. There is no `AGENTS.md` setup section or `doctor` health-check command.

### 5. Workflow Coverage - 2/3

README and the bundled skill include many examples for templates, submissions, and submitters, including list/retrieve/create/update/archive flows and a multi-step "create template then send for signing" pattern. Examples use clear placeholders such as `1001`, `john@acme.com`, and `YOUR_KEY`, and explain `-d` bracket/JSON input. A read-only probe equivalent to `docuseal templates list` failed without `DOCUSEAL_API_KEY`, so no documented workflow was verified end-to-end.

## Recommended Improvements

### Documentation Quality - currently 1/3

**To reach 2/3:** Add `AGENTS.md` with canonical invocation, required env vars, non-interactive setup, and input conventions.
**To reach 3/3:** Keep `AGENTS.md` complete and add a CI check that validates documented commands/flags against `--help`.

### Self-Description - currently 1/3

**To reach 2/3:** Add `docuseal --schema` returning JSON for commands, flags, parameters, and exit codes.
**To reach 3/3:** Return a complete ManifestResponse with all commands, typed flags, exit codes, and `etag`.

### Pre-built Integrations - currently 1/3

**To reach 2/3:** Align skill metadata with package version and remove stale claims such as "Output is always JSON" until all errors are structured.
**To reach 3/3:** Generate the skill/reference docs from the same command manifest used by the CLI release.

### Setup Reproducibility - currently 2/3

**To reach 3/3:** Document setup in `AGENTS.md` and add a health-check command such as `docuseal doctor --output json`.

### Workflow Coverage - currently 2/3

**To reach 3/3:** Add one credential-free or mock-server workflow example that can be executed in CI and by agents without a live DocuSeal account.

## Related Failure Modes

| §N | Title | Severity | Readiness dimension |
|---|---|---|---|
| §44 | Agent Knowledge Packaging Absence | Medium | Documentation Quality |
| §52 | Recursive Command Tree Discovery Cost | Medium | Self-Description |
| §21 | Schema & Help Discoverability | Medium | Self-Description |
| §47 | MCP Wrapper Schema Staleness | High | Pre-built Integrations |
| §72 | Integration Artifact Version Drift | High | Pre-built Integrations |
| §20 | Environment & Dependency Discovery | Medium | Setup Reproducibility |
