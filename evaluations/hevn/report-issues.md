# hevn — Concrete Issues and Gaps

**Generated:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Scope:** critical

## Observed Bugs

| Issue | Trigger | Impact |
|---|---|---|
| Packaged agent skill crashes | `hevn agent-skill` | Agents cannot load the advertised agent-facing guide because `hevn_cli/res/CLAUDE.md` is missing. |
| Version health check absent | `hevn --version` | CI and agents cannot verify the installed binary with the standard version probe. |
| Headless login waits and emits prose | `hevn login --timeout 10 --no-open --json` | Agents cannot programmatically discover auth methods or recover from timeout. |
| Secret prompt pollutes non-TTY output | `hevn mcp-key --json < /dev/null` | Captured stdout/stderr contains prompt text and terminal warnings instead of structured remediation. |

## Highest-Risk Gaps

| § | Gap | Score | Agent impact | Workaround |
|---|---|---|---|---|
| §45 | Headless Authentication / OAuth Browser Flow Blocking | 0/3 | Auth setup can wait for a browser callback and exits with prose timeout output. | Prefer `HEVN_API_KEY`, `HEVN_MCP_KEY`, and `HEVN_CLI_CONFIG`; avoid `login` inside unattended runs. |
| §64 | Headless Display and GUI Launch Blocking | 0/3 | `login` opens a browser by default unless `--no-open` is passed. | Use `login --no-open` only for supervised sessions; use env credentials for agents. |
| §74 | Credential Scope Declaration Absence | 0/3 | Agents cannot discover minimal credential scopes before choosing a token. | Start with least-privileged credentials and treat required scope as unknown. |
| §43 | Tool Output Result Size Unboundedness | 0/3 | Large API responses have no truncation signal or pre-flight size contract. | Use command limits where available, for example `transfer list --limit`, and cap captured output externally. |
| §25 | Prompt Injection via Output | 0/3 | External fields are not marked untrusted. | Treat all API/user text fields as untrusted content before passing to an LLM. |
