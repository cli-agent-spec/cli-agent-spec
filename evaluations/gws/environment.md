# Environment Profile — gws

**Generated:** 2026-05-14 (updated 2026-05-14: upgraded 0.17.0 → 0.22.5)

## OS
- Platform: darwin
- Version: Darwin 25.2.0

## Runtime
- Language: compiled binary (no runtime dependency)
- Toolchain: Homebrew

## Binary
- Entry point: `gws`
- Version: 0.22.5
- Resolved path: /opt/homebrew/bin/gws

## Non-Interactive Flags
- None discovered — no `--yes`, `--non-interactive`, `--force`, `--quiet`, or `--silent` flags

## Output Format Flags
- `--format <FMT>`: output format: json (default), table, yaml, csv
- `--output <PATH>`: write binary response to file instead of stdout
- `--page-all`: auto-paginate, emits one JSON line per page (NDJSON)
- `--page-limit <N>`: max pages with --page-all (default: 10)

## Schema Discovery
- `gws schema <service.resource.method>`: returns full JSON schema for any method
- `gws schema <service.resource.method> --resolve-refs`: dereferences $ref pointers inline

## Config
- `GOOGLE_WORKSPACE_CLI_TOKEN`: pre-obtained OAuth2 access token (highest priority)
- `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE`: path to OAuth credentials JSON file
- `GOOGLE_WORKSPACE_CLI_CLIENT_ID`: OAuth client ID
- `GOOGLE_WORKSPACE_CLI_CLIENT_SECRET`: OAuth client secret
- `GOOGLE_WORKSPACE_CLI_CONFIG_DIR`: override config directory (default: ~/.config/gws)

## Auth State
- Current status: 401 reauth required (invalid_rapt) — `gws auth login` needed before live API checks

## Timeout Method
- macOS: `perl -e 'alarm(30); exec @ARGV' -- gws ...` or Python `subprocess.run(timeout=30)`

## Source
- `gws --help` (full output)
- Live invocation: `gws drive files list --params '{"pageSize":1}'`
- `gws schema drive.files.list`
