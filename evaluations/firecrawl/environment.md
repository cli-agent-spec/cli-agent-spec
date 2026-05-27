# firecrawl - Environment Profile

**Generated:** 2026-05-27

## OS
- Platform: darwin
- Version: 25.2.0

## Runtime
- Language: Node
- Version: v25.9.0
- Toolchain: npm 11.12.1

## Binary
- Entry point: `./node_modules/.bin/firecrawl`
- Version: 1.18.1
- Resolved path: `/Users/roman/Documents/Firecrawl CLI/node_modules/firecrawl-cli/dist/index.js`

## Non-Interactive Flags
- `--api-key <key>`: provides an API key without invoking login.
- `--api-url <url>`: points commands at a custom Firecrawl API endpoint.
- `--status`: prints version, authentication status, concurrency, and credits without prompting.

## Output Format Flags
- `--json`: available on multiple commands to force JSON output.
- `--format <formats>`: controls result formats for scrape-like commands.
- `--output <path>` / `-o <path>`: saves output to a file for commands that support file output.
- `--pretty`: pretty-prints JSON output where supported.

## Config
- `FIRECRAWL_API_KEY`: API key used for authenticated Firecrawl API calls.
- `FIRECRAWL_API_URL`: custom API URL for self-hosted/local Firecrawl instances.

## Timeout Method
- `subprocess.run(timeout=N)`

## Source
- Firecrawl CLI docs at `https://docs.firecrawl.dev/sdks/cli`.
- Local `package.json` from `npm install firecrawl-cli`.
- `./node_modules/.bin/firecrawl --version`.
- `./node_modules/.bin/firecrawl --help`.
- `./node_modules/.bin/firecrawl --status`.
