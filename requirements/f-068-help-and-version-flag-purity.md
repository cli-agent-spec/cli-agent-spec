# REQ-F-068: Help and Version Flag Purity

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** Silent assumption — agents call `--help` and `--version` freely for discovery and schema extraction without expecting side effects

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: Low

---

## Description

The framework MUST guarantee that `--help` and `--version` (and their short forms `-h`, `-V`) exit before any application initialization code runs. This means: no config directory creation, no schema migration, no database connection, no network call, no credential validation, no first-run setup, no file writes of any kind. The framework dispatches help/version output directly from argument parsing, before any command handler or lifecycle hook is invoked.

Agents call `--help` routinely to inspect flag schemas, discover subcommands, and extract type annotations. Any side effect on this path contaminates isolated agent environments and corrupts parallelism.

Multi-command CLIs MUST render root help on empty invocation (`tool` with no subcommand) and exit 0. Erroring out on empty invocation (e.g., argparse `add_subparsers(required=True)` or a required positional `COMMAND`) is a violation: agents use the bare invocation as their standard first-contact probe for capability discovery (see §21 agent workaround), so a non-zero exit signals failure before any discovery can occur. That empty-invocation help path MUST follow the same purity guarantees as `--help`. It remains a lightweight usage surface, not an implicit substitute for `--schema` or `tool manifest`.

## Acceptance Criteria

- `--help` on a command that would otherwise fail (missing credentials, missing config, missing network) must succeed with exit 0 and produce help output
- `--version` must succeed in a completely empty environment (`HOME=/tmp`, no config, no credentials)
- Neither flag creates files, directories, network connections, or log entries
- `tool` with no subcommand MUST render root help with exit 0 — not an error, not a usage message with non-zero exit
- That empty-invocation path creates no files, directories, network connections, or log entries
- Calling `--help` 1000 times in parallel produces no race conditions, no lock contention, no file conflicts
- `--help` exit code is `0`; `--version` exit code is `0`

---

## Schema

No dedicated schema type — this requirement governs framework dispatch order, not wire format

---

## Wire Format

`--version` output must be machine-parseable: the semver string on a single line, optionally prefixed by the tool name and a space:

```
tool 1.2.3
```

or just:

```
1.2.3
```

Not: `tool version 1.2.3 (built 2026-01-01 with go1.21 on linux/amd64)` — this format cannot be reliably parsed by `cut -d' ' -f2`.

---

## Example

```
# In an environment with no config, no credentials, no network
$ HOME=/tmp/empty TOOL_TOKEN="" tool deploy --help
Usage: tool deploy [OPTIONS]

Options:
  --env TEXT    Target environment (required)
  --dry-run     Preview changes without applying
  --output TEXT Output format: plain|json [default: plain]

→ exit code: 0
→ no files created in /tmp/empty
→ no network connections attempted

$ HOME=/tmp/empty TOOL_TOKEN="" tool
Usage: tool [OPTIONS] COMMAND [ARGS]...

→ exit code: 0
→ no files created in /tmp/empty
→ no network connections attempted
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-interactive detection that --help bypasses entirely |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Extends: help/version exit before even Phase 1 validation runs |
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Provides: update check suppression that --help also bypasses |
| [REQ-F-047](f-047-repl-mode-prohibition-in-non-tty-context.md) | F | Composes: empty invocation may show root help safely instead of entering interactive mode |
