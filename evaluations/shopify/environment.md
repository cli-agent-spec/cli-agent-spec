# shopify — Environment Profile

**Generated:** 2026-05-28

## OS
- Platform: darwin
- Version: 25.2.0

## Runtime
- Language: Node
- Version: v25.9.0
- Toolchain: npm 11.12.1

## Binary
- Entry point: `shopify`
- Version: `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
- Resolved path: `/opt/homebrew/bin/shopify`

## Non-Interactive Flags
- `--no-color`: disables color output for commands that support it.
- `--json`: global output-format flag for some Oclif commands, and command-local JSON output for commands such as `theme push`.
- `--allow-updates`: allows app deploy additions/updates without user confirmation; documented as recommended for CI/CD.
- `--allow-deletes`: allows app deploy removals without user confirmation.
- `--no-release`: creates an app version without release and avoids user confirmation for release.
- `--name`: skips the app selection prompt in `app init` by creating a new app with the provided name.
- `--client-id`: links `app init` or `app deploy` to an existing app and avoids app selection prompts.
- `--organization-id`: supplies the organization for `app init`, avoiding an organization selection prompt.
- `--store`: supplies a store for theme commands that would otherwise infer or prompt.
- `--theme`: supplies a theme ID or name for theme commands that would otherwise prompt.
- `--password`: supplies a Theme Access password or Admin API token for theme commands.

## Output Format Flags
- `--json`: `shopify commands --json` returns machine-readable command metadata; commands such as `theme push --json` document JSON result output.
- `--columns=<option>...`: `shopify commands` can restrict columns to `id`, `plugin`, `summary`, or `type`.
- `--tree`: `shopify commands` can render command inventory as a tree.
- `--no-truncate`: `shopify commands` can preserve full table values.

## Config
- `SHOPIFY_CLI_NO_ANALYTICS=1`: opts out of anonymous usage statistics.
- `OPT_OUT_INSTRUMENTATION=true`: opts out of anonymous usage statistics.
- `SHOPIFY_HTTP_PROXY`: proxy URL for HTTP traffic.
- `SHOPIFY_HTTPS_PROXY`: proxy URL for HTTPS traffic.

## Timeout Method
- `subprocess.run(timeout=N)` from Python, or `perl -e 'alarm(N); exec(@ARGV)' -- <command>` on macOS.

## Source
- Shopify CLI docs: `https://shopify.dev/docs/api/shopify-cli`
- Runtime probes: `node --version`, `npm --version`, `git --version`, `uname -r`
- Binary probes: `which shopify`, `shopify --version`, `shopify help`, `shopify commands`, `shopify help commands`
- Command help probes: `shopify app init --help`, `shopify app deploy --help`, `shopify theme push --help`, `shopify version --help`
