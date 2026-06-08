# link-cli — Environment Profile

**Generated:** 2026-06-08

## OS
- Platform: darwin
- Version: Darwin Macbook-M4.local 25.2.0 Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132 arm64

## Runtime
- Language: Node.js
- Version: v26.0.0
- Toolchain: npm 11.12.1; package manager declared by source repo: pnpm@10.32.1

## Binary
- Entry point: `link-cli`
- Version: `0.7.1`
- Resolved path: `/opt/homebrew/bin/link-cli`
- Package: `@stripe/link-cli@0.7.1`

## Non-Interactive Flags
- `--format <toon|json|yaml|md|jsonl>`: Select output format. README says non-TTY defaults to `toon`; `--format json` is available for structured output.
- `--full-output`: Wrap command result in an envelope with `ok`, `data`, and `meta`.
- `--auth <path>`: Store or read auth credentials at an explicit file path instead of the platform default.
- `--interval <seconds>`: Poll for auth or spend-request status without requiring an interactive loop.
- `--timeout <seconds>`: Bound auth or spend-request polling.
- `--max-attempts <n>`: Bound polling attempts.
- `--force`: Overwrite an existing `--output-file` target for commands that write card credentials.
- `NO_UPDATE_NOTIFIER=1`: Suppress update checks.

## Output Format Flags
- `--format json`: Emit JSON output.
- `--format toon`: Emit compact default agent-oriented text output.
- `--format yaml`: Emit YAML output.
- `--format md`: Emit Markdown output.
- `--format jsonl`: Emit JSON Lines output.
- `--filter-output <keys>`: Filter output by key paths.
- `--token-count`: Print token count instead of command output.
- `--token-limit <n>`: Limit output to the first `n` tokens and print a truncation marker.
- `--token-offset <n>`: Skip the first `n` tokens.
- `--llms`, `--llms-full`: Print an LLM-readable command manifest.
- `--schema`: Show a command schema. Root `link-cli --schema` returned top-level help; command-level schema worked.

## Config
- `LINK_AUTH_FILE`: Same purpose as `--auth`; override auth credential file path.
- `LINK_ACCESS_TOKEN`: Use an access token directly, bypassing auth storage.
- `LINK_REFRESH_TOKEN`: Refresh token to use when `LINK_ACCESS_TOKEN` is expired.
- `LINK_NO_REFRESH`: When set, do not auto-refresh an expired access token.
- `LINK_API_BASE_URL`: Override API base URL.
- `LINK_AUTH_BASE_URL`: Override auth base URL.
- `LINK_HTTP_PROXY`: Route SDK requests through an HTTP proxy.
- `NO_UPDATE_NOTIFIER`: Suppress npm update notifier checks.

## Timeout Method
- `subprocess.run(timeout=N)` or a process-level wrapper such as `perl -e 'alarm(N); exec @ARGV'` on macOS.

## Source
- Read: `README.md`, `CLAUDE.md`, root `package.json`, `packages/cli/package.json`, `.mcp.json`, `.codex-plugin/plugin.json`, `skills/create-payment-credential/SKILL.md`.
- Verified: `which link-cli`, `link-cli --version`, `link-cli --help`, `link-cli --llms-full`, `link-cli --schema`, `link-cli spend-request create --schema`, `link-cli spend-request create --help`.
- Note: no `AGENTS.md` or `CODING_AGENTS.md` exists in the source repo. The workspace-level `AGENTS.md` only points Codex to local development rules.
