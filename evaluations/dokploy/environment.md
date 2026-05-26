# dokploy — Environment Profile

**Generated:** 2026-05-26

## OS
- Platform: darwin
- Version: macOS host; shell `zsh`

## Runtime
- Language: Node
- Version: v25.9.0
- Toolchain: npm 11.12.1

## Binary
- Entry point: `dokploy`
- Version: `0.3.0`
- Resolved path: `/opt/homebrew/bin/dokploy`
- Installed package: `@dokploy/cli@0.29.4`
- Version note: `npm list -g @dokploy/cli --depth=0` reports package version `0.29.4`, while `dokploy --version` reports `0.3.0`.

## Non-Interactive Flags
- `--json`: available on generated API commands; prints the raw API response instead of the default Commander/Chalk formatted output. Not available on `auth` or top-level commands.

## Output Format Flags
- `--json`: raw JSON for generated API command success responses only. Errors observed during auth/config failures are prose, not JSON.

## Config
- `DOKPLOY_URL`: Dokploy server URL.
- `DOKPLOY_API_KEY`: API key used for `x-api-key` authentication.
- `DOKPLOY_AUTH_TOKEN`: fallback token environment variable used when `DOKPLOY_API_KEY` is absent.
- `.env`: loaded from the current working directory if present; shell environment variables take priority.
- Stored config: source code writes `config.json` next to the installed package directory via `path.join(__dirname, "..", "config.json")`.

## Timeout Method
- `subprocess.run(timeout=N)` or caller-managed timeout. The CLI itself exposes no `--timeout` flag and the Axios client has no configured request timeout.

## Source
- Installed binary: `/opt/homebrew/bin/dokploy`
- Source inspected: `/private/tmp/dokploy-cli-src`
- Docs read: `readme.md`, `package.json`, `src/index.ts`, `src/client.ts`, `src/commands/auth.ts`, `src/generated/commands.ts`
- No `AGENTS.md`, `CODING_AGENTS.md`, manifest command, or schema command was found.
