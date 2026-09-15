# resend — Environment Profile

**Generated:** 2026-07-06T11:50:00+03:00

## OS
- Platform: darwin
- Version: Darwin Macbook-M4.local 25.2.0 Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132 arm64

## Runtime
- Language: Node.js
- Version: v22.22.3
- Toolchain: npm 10.9.8
- Package: resend-cli@2.8.1
- Package manager declared by package: pnpm@11.8.0

## Binary
- Entry point: `/Users/roman/.hermes/node/bin/resend`
- Version: `resend-cli v2.8.1`
- Resolved path: `/Users/roman/.hermes/node/bin/resend` -> `../lib/node_modules/resend-cli/dist/cli.cjs`
- PATH note: `npm install -g resend-cli` installed the binary, but `/Users/roman/.hermes/node/bin` was not on PATH in this shell. Use the absolute entry point above for checks.

## Non-Interactive Flags
- `--api-key <key>`: override API key for a single invocation; avoids stored credential lookup.
- `--profile <name>` / `-p <name>`: select a named stored profile; also respects `RESEND_PROFILE`.
- `--quiet` / `-q`: suppress spinners and status output; implies JSON output.
- `--json`: force JSON output.
- `login --key <key>`: non-interactive login path; required when stdin/stdout is not a TTY.
- `--yes`: required by delete/rm commands in non-interactive mode to skip confirmation prompts.
- `--dry-run`: available on `emails send` and `broadcasts create` to validate and print request JSON without calling the API.

## Output Format Flags
- `--json`: force JSON output for commands that support machine output.
- `--quiet` / `-q`: suppress status/spinner output and imply JSON output.
- `commands`: prints the command tree as JSON for agents and tooling.
- Non-TTY behavior: docs and installed README state the CLI auto-detects non-TTY environments and emits success JSON on stdout and error JSON on stderr.

## Config
- `RESEND_API_KEY`: API key used for authentication; preferred for CI and agents.
- `RESEND_PROFILE`: named auth profile for multi-account setups.
- `XDG_CONFIG_HOME`: config-directory override on Linux according to docs.
- `RESEND_INSTALL`: install-directory override for the shell installer according to docs.

## Timeout Method
- `subprocess.run(timeout=N)` on macOS; GNU `timeout` is not assumed available.

## Source
- User-provided docs URL: https://resend.com/docs/cli
- npm package metadata: `npm view resend-cli version bin description --json`
- Install command: `npm install -g resend-cli --no-fund --no-audit`
- Binary checks: `/Users/roman/.hermes/node/bin/resend --version`, `/Users/roman/.hermes/node/bin/resend --help`, `/Users/roman/.hermes/node/bin/resend login --help`
- Command schema: `/Users/roman/.hermes/node/bin/resend commands`
- Installed package files: `/Users/roman/.hermes/node/lib/node_modules/resend-cli/package.json`, `README.md`, `skills/resend-cli/SKILL.md`, `skills/resend-cli/references/workflows.md`
