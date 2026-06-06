# neonctl — Environment Profile

**Generated:** 2026-06-06

## OS
- Platform: darwin
- Workspace: `/Users/roman/Documents/Neondb cli`

## Runtime
- Language: Node.js
- Version: v22.22.3
- Toolchain: npm 10.9.8

## Binary
- Entry point: `/Users/roman/.hermes/node/bin/neonctl`
- Alias: `/Users/roman/.hermes/node/bin/neon`
- Version: 2.22.2
- Resolved path: `/Users/roman/.hermes/node/bin/neonctl` -> `../lib/node_modules/neonctl/cli.js`

## Non-Interactive Flags
- `--api-key`: supplies a Neon API key; also reads `NEON_API_KEY`.
- `--config-dir`: isolates credentials/config from the default user config directory.
- `--no-analytics` / `--analytics false`: disables analytics.
- `--no-color` / `--color false`: disables colorized output.
- `link --agent`: emits a JSON state-machine response for the `link` workflow.
- `init --agent <cursor|copilot|claude>`: selects a target coding assistant for init, but still performed auth/progress flows during testing.

## Output Format Flags
- `-o, --output <json|yaml|table>`: sets output format; default is `table`.

## Config
- `NEON_API_KEY`: API key fallback for `--api-key`.
- `NEON_API_HOST`: hidden API host override.
- `NEON_OAUTH_HOST`: hidden OAuth host override.
- Default config dir from help: `/Users/roman/.config/neonctl`.

## Timeout Method
- `subprocess.run(timeout=N)` on macOS.

## Source
- Neon CLI docs: `https://neon.com/docs/reference/neon-cli`
- Installed package: `/Users/roman/.hermes/node/lib/node_modules/neonctl/package.json`
- Installed README: `/Users/roman/.hermes/node/lib/node_modules/neonctl/README.md`
- CLI help: `/Users/roman/.hermes/node/bin/neonctl --help`

## Notes
- The global npm bin directory `/Users/roman/.hermes/node/bin` was not on the shell `PATH` during the audit, so the resolved absolute binary was used.
- A fake `--api-key` auth probe against the default config printed `Authentication failed, deleting credentials...` for `/Users/roman/.config/neonctl/credentials.json`. Subsequent probes used an isolated `--config-dir`.
