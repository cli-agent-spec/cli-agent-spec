# hevn — Fix List for CLI Authors

**Generated:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Scope:** critical

## Priority Fixes

1. Add `--version` and a stable health check.
   - `hevn --version` should exit 0 and print `hevn-cli 0.1.0` or equivalent parseable text.

2. Ship a machine-readable manifest.
   - Add `hevn --schema` with commands, flags, output modes, possible exit codes, required credentials/scopes, interactivity, destructive behavior, and max output contracts.

3. Make JSON an invariant for agent mode.
   - Prefer a global `--output json` or auto-enable structured output when `CI=true`.
   - Use a consistent envelope: `ok`, `data`, `error`, `warnings`, `meta`.
   - Include `exit_code` in error bodies.

4. Fix headless auth behavior.
   - `hevn login --json` should either return an auth URL plus structured wait metadata or fail immediately in non-TTY with `AUTH_REQUIRED` and `auth_methods`.
   - Avoid `webbrowser.open()` unless stdout/stdin indicate an interactive human session or the user explicitly requests it.

5. Package the agent skill resource.
   - Include `hevn_cli/res/CLAUDE.md` in the wheel or remove the `agent-skill` command until it works.

6. Add non-interactive prompt contracts.
   - Convert stdin/prompt failures into structured `STDIN_REQUIRED` or `INTERACTIVE_REQUIRED` errors with hints.
   - Add a global `--non-interactive` or `--no-input` flag.

7. Add mutation safety contracts.
   - Add `--dry-run`, `effect`, `danger_level`, and full idempotency coverage for mutating commands.

## Passing Areas

- No REPL/shell subcommand was exposed.
- No editor-requiring command was found.

## Remaining Critical Gaps

Failing checks: §43, §45, §53, §60, §64, §13, §25, §74.

Partial checks: §34, §42, §50, §61, §71, §10, §11, §12, §23, §24, §1, §2.
