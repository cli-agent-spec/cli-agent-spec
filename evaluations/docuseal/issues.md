# docuseal-cli - Issues

## §2, §18 - Common failures produce stack traces instead of structured JSON

Observed `templates list` without credentials, invalid JSON in `-d`, a missing upload file, and network failure. These exit 1 with Commander prose or Node stack traces rather than `{"ok": false, "error": {"code": ...}}`.

## §10 - `configure` prompt path exits 0 under non-TTY stdin

Running `node bin/run.js configure` with empty stdin printed the server prompt and exited 0 without writing configuration. That is not a hang, but it is a false success for agents.

## §40 - Async handlers are registered under `program.parse()`

`src/index.js` calls `program.parse()` while command actions are async. Commander generally requires `parseAsync()` for reliable async error handling; observed network/auth failures surfaced as unhandled stack traces.

## §72 - Integration artifact version drift

`package.json` and `node bin/run.js --version` report `1.0.3`, while `skills/docuseal-cli/SKILL.md` metadata reports `1.0.6`.
