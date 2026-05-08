# Environment Profile — gh

**Generated:** 2026-05-07
**CWD:** /Users/roman/PycharmProjects/CLI-argonomics/cli-agent-ergonomics

## OS
- Platform: darwin
- Version: 25.2.0

## Runtime
- Language: Go (compiled binary)
- Version: n/a (native binary)
- Toolchain: homebrew

## Binary
- Entry point: `gh`
- Version: 2.88.1 (2026-03-12)
- Resolved path: /opt/homebrew/bin/gh

## Non-Interactive Flags
- `GH_PROMPT_DISABLED=1`: disables all interactive prompting in the terminal
- `--yes`: available on select commands (e.g. `gh repo delete --yes`) to skip confirmation prompts

## Output Format Flags
- `--json <fields>`: returns JSON output for supported commands (comma-separated field list)
- `--jq <query>`: filters JSON output using jq syntax
- `--template <string>`: formats JSON output using Go template syntax

## Config
- `GH_TOKEN` / `GITHUB_TOKEN`: authentication token (in precedence order); avoids auth prompts
- `GH_ENTERPRISE_TOKEN` / `GITHUB_ENTERPRISE_TOKEN`: token for GitHub Enterprise Server
- `GH_HOST`: override default GitHub hostname
- `GH_REPO`: specify repo in HOST/OWNER/REPO format for commands that infer from git context
- `GH_PAGER` / `PAGER`: paging program for output; set to `cat` or empty to suppress paging
- `GH_NO_UPDATE_NOTIFIER`: set to any value to suppress update notifications
- `GH_NO_EXTENSION_UPDATE_NOTIFIER`: set to any value to suppress extension update notifications
- `NO_COLOR`: set to any value to suppress ANSI color codes

## Timeout Method
- macOS: no GNU `timeout`; use `perl -e 'alarm(30); exec(@ARGV)' -- gh <args>` or subprocess timeout in Python

## Source
- Docs read: `gh --help`, `gh help environment`, `gh help exit-codes`, `gh help formatting`, `gh config list`
- No AGENTS.md or CODING_AGENTS.md found in CWD (not a gh source checkout)
