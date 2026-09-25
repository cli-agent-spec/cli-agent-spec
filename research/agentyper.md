# agentyper

> Agent-first Python CLI library — Typer-compatible, built on argparse + pydantic
> GitHub: https://github.com/romamo/agentyper
> Version: 0.1.4 (Alpha) | License: MIT | Language: Python 3.10+
> Author: Roman Medvedev | First release: 2026-03-03

---

## Overview

agentyper is an early-stage Python CLI framework explicitly designed for agent-first CLI ergonomics. It is API-compatible with Typer (drop-in replacement via `import agentyper as typer`) but built on argparse + pydantic instead of Click. Its central thesis: existing CLI frameworks were designed for human operators; agentyper is designed for the era when AI agents are the primary CLI consumer.

Key design decision: agent ergonomics are injected automatically at the framework level — command authors write normal Python functions, and the framework handles `--schema`, `--format`, `--yes`, `--answers`, structured errors, and exit code taxonomy without any per-command work.

---

## Architecture & Design

**Stack:**
- Parser: `argparse` (stdlib — no Click dependency)
- Validation: `pydantic` v2 (type coercion, field-level errors, schema export)
- Output: `rich` (human display) + structured JSON (agent display)
- TTY detection: `isatty()` for automatic format selection

**Core components:**
```
src/agentyper/
  _internal/
    _app.py       — Agentyper app, command registration, routing
    _errors.py    — Exit codes, structured error formatting
    _interactive.py — confirm(), prompt(), edit() with agent bypass
    _output.py    — output(), echo(), render_output()
    _params.py    — Option, Argument (Typer-compatible)
    _schema.py    — JSON Schema generation from function signatures
  __init__.py     — Public API
  cli.py          — CLI entry point
  testing.py      — Test helpers
```

**Auto-injected global flags (every command gets these for free):**
- `--format {table,json,csv}` — structured output, auto-selected via `isatty()`
- `--schema` — JSON Schema for command params or full app
- `--yes` / `--no` — bypass `confirm()` calls non-interactively
- `--answers '{"confirms":[...],"prompts":[...]}'` — pre-supply all interactive answers
- `-v` / `-vv` — INFO/DEBUG logging

**Exit code taxonomy (3-code system):**
```
EXIT_SUCCESS    = 0  — success
EXIT_VALIDATION = 1  — bad input, agent should retry with correction
EXIT_SYSTEM     = 2  — system error, agent should abort
```

**Typer migration path:**
```python
# Before:
import typer
# After (one line change):
import agentyper as typer  # everything else stays identical
```

---

## Agent Compatibility Assessment

### What it handles natively

- **Schema discoverability** — `--schema` on every command and the full app, exports JSON Schema derived from Python type hints and docstrings
- **Output format** — `--format json/csv/table`, auto-detected via `isatty()`; non-TTY defaults to machine-readable
- **Interactivity bypass** — `confirm()`, `prompt()`, `edit()` all resolve without blocking in non-TTY/agent mode via `--yes` and `--answers`
- **Structured errors** — `exit_error()` emits structured JSON error objects; pydantic validation errors are formatted into field-level structured output automatically
- **Exit code taxonomy** — 3-code system (0/1/2) with named constants
- **Validation before execution** — pydantic validates all arguments before the command function body executes

### What it handles partially

- **Exit codes** — 3-code system (0/1/2) is simpler than the 9-code table in the requirements (no distinct codes for NOT_FOUND, TIMEOUT, CONFLICT, RATE_LIMITED, etc.)
- **Output format** — JSON output exists but no `ok`/`data`/`error`/`meta` envelope schema; no `pagination` metadata; no `warnings[]` array
- **ANSI suppression** — uses `rich` which has `NO_COLOR` support, but not all edge cases of color leakage are documented as handled
- **Stderr/stdout discipline** — `echo()` vs `output()` separation exists but enforcement is opt-in by command authors

### What it does not handle

- Timeouts (`--timeout` flag, timeout exit code 7)
- Idempotency keys (`--idempotency-key`)
- Partial failure / multi-step step manifests
- Pagination (`--limit`, `--cursor`, pagination metadata in responses)
- Signal handling (SIGTERM handler, partial JSON on kill)
- Child process tracking
- Config file shadowing / `--show-config`
- Retry hints (`retryable`, `retry_after_ms` in errors)
- Observability / audit trail / request IDs
- Dry-run for destructive operations
- Network proxy awareness
- Binary/encoding safety
- Working directory sensitivity
- Undeclared filesystem side effects

---

## Challenge Coverage Table

| # | Challenge | Rating | Reason |
|---|-----------|--------|--------|
| 1 | Exit Codes & Status Signaling | ~ | 3-code taxonomy (0/1/2) — partial; missing NOT_FOUND, TIMEOUT, etc. |
| 2 | Output Format & Parseability | ~ | `--format json` automatic; no standard envelope, no pagination meta |
| 3 | Stderr vs Stdout Discipline | ~ | `output()` vs `echo()` split exists; not strictly enforced on authors |
| 4 | Verbosity & Token Cost | ~ | `--format csv` is 4× cheaper than table; no `--fields` selector |
| 5 | Pagination & Large Output | ✗ | No `--limit`, `--cursor`, or pagination metadata |
| 6 | Command Composition & Piping | ✗ | No `--format id` mode, no stdin pipe support |
| 7 | Output Non-Determinism | ✗ | No stable sorting guarantee, no `data`/`meta` separation |
| 8 | ANSI & Color Code Leakage | ~ | `rich` respects `NO_COLOR`; isatty() detection; not exhaustively tested |
| 9 | Binary & Encoding Safety | ✗ | No explicit binary/encoding handling |
| 10 | Interactivity & TTY Requirements | ✓ | `--yes`, `--answers`, isatty() auto-detection — core feature |
| 11 | Timeouts & Hanging Processes | ✗ | No built-in timeout mechanism |
| 12 | Idempotency & Safe Retries | ✗ | No idempotency key support |
| 13 | Partial Failure & Atomicity | ✗ | No step manifests or partial failure reporting |
| 14 | Argument Validation Before Side Effects | ✓ | Pydantic validates all args before function body runs |
| 15 | Race Conditions & Concurrency | ✗ | No session isolation or locking primitives |
| 16 | Signal Handling & Graceful Cancellation | ✗ | No SIGTERM/SIGPIPE handlers installed |
| 17 | Child Process Leakage | ✗ | No child process tracking |
| 18 | Error Message Quality | ✓ | Structured JSON errors with field-level pydantic details |
| 19 | Retry Hints in Error Responses | ✗ | No `retryable` or `retry_after_ms` fields |
| 20 | Environment & Dependency Discovery | ✗ | No `doctor` command or preflight checks |
| 21 | Schema & Help Discoverability | ✓ | `--schema` on every command and full app — core feature |
| 22 | Schema Versioning & Output Stability | ✗ | No `schema_version` in responses, no deprecation warnings |
| 23 | Side Effects & Destructive Operations | ✗ | No `danger_level`, no `--dry-run` framework support |
| 24 | Authentication & Secret Handling | ✗ | No secret redaction or `--secret-from-file` |
| 25 | Prompt Injection via Output | ✗ | No external data tagging or sanitization |
| 26 | Stateful Commands & Session Management | ✗ | No `--config` isolation or state inspection |
| 27 | Platform & Shell Portability | ~ | Python stdlib base is portable; no explicit platform checks |
| 28 | Config File Shadowing & Precedence | ✗ | No config precedence tracking or `--no-config` |
| 29 | Working Directory Sensitivity | ✗ | No `--cwd` flag, no absolute path enforcement |
| 30 | Undeclared Filesystem Side Effects | ✗ | No side effect declaration or cleanup command |
| 31 | Network Proxy Unawareness | ✗ | No proxy handling (network is out of scope) |
| 32 | Self-Update & Auto-Upgrade Behavior | ✓ | Early-stage tool; no auto-update behavior implemented |
| 33 | Observability & Audit Trail | ✗ | No request IDs, trace IDs, or audit log |

**Summary: ✓ 5 / ~ 6 / ✗ 22**

---

## Strengths for Agent Use

1. **Drop-in Typer replacement** — lowest migration cost of any framework; massive Typer ecosystem becomes agent-compatible with one import change
2. **Schema-first** — `--schema` is automatic on every command, not an afterthought
3. **Interactivity solved** — `--answers` JSON payload is a uniquely powerful pattern for pre-supplying all interactive responses
4. **Pydantic validation** — field-level structured errors are immediately useful to agents for self-correction
5. **isatty() auto-detection** — format selection without agent configuration
6. **Active agent focus** — the only Python CLI framework explicitly designed around agent ergonomics

## Weaknesses for Agent Use

1. **Alpha quality** (v0.1.4, March 2026) — not production-ready; API may change
2. **3-code exit taxonomy** — too coarse; agents can't distinguish NOT_FOUND from TIMEOUT from RATE_LIMITED
3. **No output envelope** — JSON output lacks `ok`/`data`/`error`/`meta` structure; agents must handle ad-hoc schemas per command
4. **Execution gaps** — no timeouts, signals, partial failure, pagination, idempotency
5. **Security gaps** — no secret redaction, no prompt injection protection
6. **No observability** — no request IDs, no audit trail
7. **Rich dependency** — pulls in `rich` even for agent use where all color output should be suppressed

## Verdict

agentyper is the most conceptually aligned framework in this review — it explicitly targets agent ergonomics as its primary design goal, not a retrofit. Its auto-injected `--schema`, `--format`, `--yes`/`--answers`, and structured errors address the highest-frequency agent pain points. However, at v0.1.4 it covers only ~17% of the 33 challenges, leaving critical execution reliability (timeouts, signals, idempotency), security (secrets, prompt injection), and observability entirely unaddressed. As a foundation for a more complete agent-compatible CLI framework, it is the strongest starting point in the Python ecosystem — but it requires significant extension before it meets the full requirements.
