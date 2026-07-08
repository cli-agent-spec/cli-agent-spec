# temporal — Environment Profile

**Generated:** 2026-07-07T12:44:17+00:00

## OS
- Platform: darwin
- Version: Darwin 25.2.0; macOS 26.2

## Runtime
- Language: Go binary
- Version: temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
- Toolchain: Homebrew-installed binary on PATH

## Binary
- Entry point: `/opt/homebrew/bin/temporal`
- Version: `temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)`
- Resolved path: `/opt/homebrew/bin/temporal`

## Non-Interactive Flags
- `--yes`: bypasses confirmation prompts on query-based workflow mutations such as `workflow delete --query`.
- `--headless`: disables Web UI startup for `server start-dev`.
- `--disable-config-env`: disables environment-derived Temporal config.
- `--disable-config-file`: disables config-file loading.

## Output Format Flags
- `--output text|json|jsonl|none`: controls non-logging data output.
- `--log-format text|json`: controls log formatting.
- `--color always|never|auto`: controls color output.
- `--time-format relative|iso|raw`: controls timestamp formatting.

## Config
- `--env-file`: path to environment settings file.
- `--config-file`: path to TOML config file.
- `--env`: active environment name.
- `--profile`: profile to use for config file.
- `--address`: Temporal Service gRPC endpoint.
- `--namespace`: Temporal namespace.
- `--api-key`: API key for request.
- `TEMPORAL_GRPC_META_[name]`: environment variable form for gRPC metadata.

## Timeout Method
- `subprocess.run(timeout=N)` for audit wrapper timeouts.
- Temporal CLI flags: `--client-connect-timeout` and `--command-timeout`.

## Source
- Local workspace docs checked: no AGENTS.md, CODING_AGENTS.md, README.md, or package manifest found.
- CLI probes read: `temporal --version`, `temporal --help`, command help for workflow/list/start/delete/signal, schedule/delete, env/set, config, batch, and server/start-dev.
