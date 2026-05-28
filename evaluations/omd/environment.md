# omd — Environment Profile

**Generated:** 2026-05-28T07:44:55Z

## OS
- Platform: darwin
- Version: macOS host; timeout handled with subprocess timeouts rather than GNU `timeout`

## Runtime
- Language: Rust
- Version: Cargo package `openmetadata-cli` 0.1.1
- Toolchain: cargo

## Binary
- Entry point: `./target/debug/omd`
- Version: `omd 0.1.1`
- Resolved path: `/Users/roman/Documents/Opemetadata-cli/openmetadata-cli/target/debug/omd`

## Non-Interactive Flags
- `--token <TOKEN>`: supplies JWT token directly and bypasses stored credentials
- `--host <HOST>`: supplies OpenMetadata server URL directly
- `auth login --token-env-var <ENV> --headless`: documented non-interactive token login flow
- `--output json`: forces JSON output for automation
- `--format json`: alias for `--output json`
- `--schema`: emits machine-readable CLI schema as JSON
- `--skills`: emits machine-readable skills index as JSON
- `--skills-content`: includes Markdown content in `--skills` output
- `--quiet`: reduces log output to errors only

## Output Format Flags
- `--output <table|json>`: output format, defaulting to JSON when stdout is not a TTY, CI, or NO_COLOR
- `--format <table|json>`: automation-friendly output format alias
- `--schema`: machine-readable CLI schema
- `--skills`: machine-readable skills index

## Config
- `OMD_PROFILE`: configuration profile name
- `OMD_HOST`: OpenMetadata server URL
- `OMD_TOKEN`: JWT token
- `OMD_TIMEOUT`: request timeout in seconds for network-backed commands

## Timeout Method
- `subprocess.run(timeout=N)` on macOS

## Source
- Read: `AGENTS.md`, `README.md`, `Cargo.toml`
- Verified: `cargo build`, `./target/debug/omd --version`, `./target/debug/omd --help`, `./target/debug/omd --schema`
