# CLI Agent Readiness Report — hevn

**Generated:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Depth:** full

## Readiness Score: 7/15  [C]

| Dimension | Score | Key finding |
|---|---|---|
| 1. Documentation Quality | 1/3 | PyPI README has install, env vars, and examples, but there is no AGENTS.md with agent-specific invocation rules. |
| 2. Self-Description | 1/3 | Help output is structured, but `--schema`, `manifest`, and `--manifest` are absent. |
| 3. Pre-built Integrations | 1/3 | `hevn agent-skill` exists but crashes because `hevn_cli/res/CLAUDE.md` is missing from the wheel. |
| 4. Setup Reproducibility | 2/3 | Non-interactive install is documented and worked from PyPI, but no `--version` health check exists and no AGENTS.md install contract is shipped. |
| 5. Workflow Coverage | 2/3 | README examples cover many read/create/update workflows, but many examples require credentials or placeholders and there is no fully machine-readable workflow manifest. |

Grade scale: A 13-15 · B 10-12 · C 7-9 · D 4-6 · F 0-3

## Notes

- Verified install with `pip install hevn-cli --quiet --no-input` in a Python 3.11 venv.
- `hevn --help` exits 0 and lists command groups.
- `hevn --version` exits 2, so agents cannot use the conventional version health check.
- `hevn agent-skill` raises `FileNotFoundError: .../hevn_cli/res/CLAUDE.md`.
