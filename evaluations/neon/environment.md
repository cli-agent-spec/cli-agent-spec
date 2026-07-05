# neon - Environment Profile

**Generated:** 2026-07-05T15:00:00+03:00

## OS
- Platform: darwin
- Version: Darwin Macbook-M4.local 25.2.0 Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132 arm64

## Runtime
- Language: Node
- Version: v22.22.3
- Toolchain: npm 10.9.8
- Package: neon 2.30.1

## Binary
- Entry point: `/Users/roman/.hermes/node/bin/neon`
- Version: 2.30.1
- Resolved path: `/Users/roman/.hermes/node/bin/neon`
- Symlink target: `../lib/node_modules/neon/dist/cli.js`
- Alias: `/Users/roman/.hermes/node/bin/neonctl`

## Non-Interactive Flags
- `--api-key <key>`: authenticate without browser login; defaults from `NEON_API_KEY`.
- `--config-dir <dir>`: use an alternate config directory instead of the default user config path.
- `--context-file <file>`: use an explicit Neon context file instead of upward discovery.
- `--no-color` / `--color false`: disable colorized output.
- `--no-analytics` / `--analytics false`: disable anonymous analytics.
- `neon link --agent`: emit a JSON state-machine response for AI agents instead of prompting.
- `neon link --params <json>`: provide link parameters as JSON.
- `neon link --yes`: skip the already-linked confirmation in interactive mode.
- `neon link --no-checks`: write context offline without API verification; requires explicit org and project IDs.
- `neon link --no-env-pull`: skip writing branch env vars to `.env`.

## Output Format Flags
- `--output json`: emit machine-readable JSON.
- `--output yaml`: emit YAML.
- `--output table`: emit table output; this is the default and may omit fields.

## Config
- `NEON_API_KEY`: API key used for non-interactive authentication.
- Default config directory: `/Users/roman/.config/neonctl`.
- Default context file: nearest `.neon` file discovered upward from the current directory.

## Timeout Method
- `subprocess.run(timeout=N)` or equivalent process timeout; macOS does not provide GNU `timeout` by default.

## Source
- Official Neon CLI docs: https://neon.com/docs/cli
- Installed package README: `/Users/roman/.hermes/node/lib/node_modules/neon/README.md`
- Installed package manifest: `/Users/roman/.hermes/node/lib/node_modules/neon/package.json`
- Commands run: `/Users/roman/.hermes/node/bin/neon --version`, `/Users/roman/.hermes/node/bin/neon --help`, `/Users/roman/.hermes/node/bin/neon link --help`, `/Users/roman/.hermes/node/bin/neon projects --help`, `/Users/roman/.hermes/node/bin/neon auth --help`
- No `AGENTS.md`, `CODING_AGENTS.md`, `README.md`, or package manifest exists in the generated audit workspace.
