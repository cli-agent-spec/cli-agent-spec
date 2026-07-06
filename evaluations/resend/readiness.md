# resend — Readiness

**CLI version:** resend-cli v2.8.1
**Date:** 2026-07-06
**Depth:** full
**Total:** 14/15  [A]

| Dimension | Score | Notes |
|---|---|---|
| Documentation Quality | 3/3 | Installed README and co-versioned `skills/resend-cli/SKILL.md` cover invocation, env vars, non-interactive flags, output contract, and input conventions; spot-checks matched `--help`. |
| Self-Description | 2/3 | `resend commands` returns valid JSON for 131 commands and 227 options, but standard `--schema`/`manifest` probes fail and output lacks `etag`, `schema_version`, and per-command `exit_codes`. |
| Pre-built Integrations | 3/3 | A first-party Codex/agent skill plus reference files and workflows ship in the same npm package as the CLI, so they are co-versioned with 2.8.1. |
| Setup Reproducibility | 3/3 | `npm install -g resend-cli --no-fund --no-audit` is non-interactive and idempotent; package dependencies are declared; `resend --version` and `resend doctor -q` are documented health checks. |
| Workflow Coverage | 3/3 | Packaged workflow recipes cover setup, sending, batch sending, domains, broadcasts, webhooks, profiles, and more; a read/write-safe `emails send --dry-run -q` example executed successfully. |

---

## Recommended Improvements

### Self-Description — currently 2/3

**To reach 3/3:** Add a ManifestResponse-compatible discovery command or extend `resend commands` with `schema_version`, `framework_version`, `etag`, a flat command map, typed flags, examples, danger levels, and per-command exit-code mappings.
