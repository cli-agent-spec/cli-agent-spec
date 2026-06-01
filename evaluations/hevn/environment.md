# hevn — Environment Profile

**Generated:** 2026-06-01

## OS
- Platform: darwin
- Version: macOS host; evaluated from `/Users/roman/Documents/HEVN CLI`

## Runtime
- Language: Python
- Version: 3.11.12
- Toolchain: local venv created from uv-managed CPython 3.11.12

## Binary
- Entry point used during audit: `/Users/roman/Documents/HEVN CLI/.audit-venv311/bin/hevn`
- Version: `hevn-cli 0.1.0` from package metadata
- Resolved path during audit: `/Users/roman/Documents/HEVN CLI/.audit-venv311/bin/hevn`
- Version command: `hevn --version` exits 2 with `No such option: --version`
- Note: the transient audit virtualenv was removed after report validation; reinstall with Python 3.11+ to reproduce live checks.

## Non-Interactive Flags
- `--json`: Print raw JSON on many commands.
- `--yaml`: Print YAML on many commands.
- `--yes` / `-y`: Skip confirmation on selected mutating commands such as transfers and contract deletion.
- `login --no-open`: Print the auth URL without opening a browser, but still waits for callback.

## Output Format Flags
- `--json`: Command-specific JSON output.
- `--yaml`: Command-specific YAML output.

## Config
- `HEVN_ENV`: Select `prod`, `dev`, or `local`.
- `HEVN_BASE_URL`: Override API base URL.
- `HEVN_SITE_URL`: Override site URL.
- `HEVN_API_KEY`: App bearer token / API key.
- `HEVN_MCP_KEY`: MCP key.
- `HEVN_API_KEY_HEADER`: Header for app API key mode.
- `HEVN_CLI_CONFIG`: Override local config path.

## Timeout Method
- `subprocess.run(timeout=N)` used by audit checks.
- CLI HTTP requests use an internal `httpx.Client(timeout=60)`.
- `hevn login` has `--timeout` with minimum 10 seconds.

## Source
- PyPI metadata for `hevn-cli 0.1.0`.
- Installed wheel source under `.audit-venv311/lib/python3.11/site-packages/hevn_cli`.
- `hevn --help`, command help, and live command checks.
