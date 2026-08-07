# cube — Environment Profile

**Generated:** 2026-08-06

## OS
- Platform: darwin
- Version: 25.2.0

## Runtime
- Language: Rust (native static release binary)
- Version: Cube CLI 1.7.16
- Toolchain: Prebuilt release binary; local `rustc 1.91.1` is present but not required

## Binary
- Entry point: `/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube`
- Version: Cube CLI 1.7.16
- Resolved path: `/Users/roman/Documents/Codex/2026-08-06/cli-agent-evaluate-batch-users-roman/work/bin/cube`

## Non-Interactive Flags
- `--token <TOKEN>` / `CUBE_API_KEY`: authenticate with an API key, JWT, or OAuth access token without launching the browser device flow
- `login --api-key <KEY>`: save an API key without starting the OAuth device flow
- `--api-url <API_URL>` / `CUBE_API_URL`: select the Cube Cloud tenant API endpoint explicitly
- `--context <CONTEXT>`: select a saved named context without prompting

## Output Format Flags
- `--json`: output raw JSON instead of human-oriented tables

## Config
- `CUBE_API_KEY`: API key, JWT, or OAuth access token
- `CUBE_API_URL`: Cube Cloud API base URL
- `CUBE_AUTH_SCHEME`: force the authorization scheme to `bearer` or `api-key`
- `CUBE_NO_UPDATE_CHECK=1`: disable the background release check
- `CUBE_NO_TELEMETRY=1`: disable anonymous usage telemetry
- `CUBEJS_TELEMETRY=false`: legacy telemetry opt-out alias
- `CI`: disables telemetry automatically
- `CUBE_OAUTH_CLIENT_ID`, `CUBE_OAUTH_CLIENT_SECRET`, `CUBE_OAUTH_SCOPE`: override OAuth device-flow client settings

## Timeout Method
- `subprocess.run(timeout=N)`

## Source
- No `AGENTS.md`, `CODING_AGENTS.md`, `README.md`, or project manifest was present in the audit working directory
- Runtime inspection: `cube --help`, `cube --version`, `uname -s`, `uname -r`, and `rustc --version`
- Documentation: Cube CLI reference and `rust/cube-cli/README.md` from the official Cube repository
- Installation reference: Cube's official `install-cli.sh` linked from the “Power of CLI” article
