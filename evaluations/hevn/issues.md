# hevn — Issues

## §37 / Readiness D3 — Packaged agent skill command crashes

**Date:** 2026-06-01
**Trigger:** `hevn agent-skill`
**Observed:** The command raises `FileNotFoundError` for `hevn_cli/res/CLAUDE.md`.
**Impact:** Agents cannot load the advertised agent-facing guide from the installed wheel.

## §71 / §1 — Conventional version health check is absent

**Date:** 2026-06-01
**Trigger:** `hevn --version`
**Observed:** Exit 2 with `No such option: --version`.
**Impact:** Agents and CI cannot verify the installed binary using the standard version probe.

## §45 / §64 — Headless login is not an immediate structured auth response

**Date:** 2026-06-01
**Trigger:** `hevn login --timeout 10 --no-open --json`
**Observed:** The command prints an auth URL to stderr, waits for a callback, then emits a Typer prose timeout error.
**Impact:** Headless agents cannot discover auth methods or recover programmatically.

## §50 / §24 — Secret prompt emits terminal warnings in non-TTY mode

**Date:** 2026-06-01
**Trigger:** `hevn mcp-key --json` with stdin closed
**Observed:** The command prints `MCP key:` to stdout, emits getpass warnings, and aborts.
**Impact:** Captured output is polluted and lacks structured `STDIN_REQUIRED` remediation.
