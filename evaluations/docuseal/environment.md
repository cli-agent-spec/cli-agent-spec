# docuseal-cli - Environment Profile

**Generated:** 2026-05-20

## OS
- Platform: darwin
- Version: Darwin Macbook-M4.local 25.2.0 Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132 arm64

## Runtime
- Language: Node.js
- Version: v25.9.0
- Toolchain: npm 11.12.1

## Binary
- Entry point: `node bin/run.js`
- Version: `1.0.3`
- Resolved path: `/Users/roman/PycharmProjects/Experiments/docuseal-cli/bin/run.js`
- Note: after clone, `bin/run.js` required `dist/index.js`, which was missing until `npm run build` was run.

## Non-Interactive Flags
- `configure --api-key <value>`: save API key without prompt.
- `configure --server <value>`: save server without prompt.
- Command-level hidden `--api-key <value>`: override API key for one invocation.
- Command-level hidden `--server <value>`: override server for one invocation.

## Output Format Flags
- None discovered. API success responses are printed as raw JSON by default, but there is no `--output`, `--json`, or consistent `ok`/`data`/`error` envelope.

## Config
- `DOCUSEAL_API_KEY`: API key.
- `DOCUSEAL_SERVER`: `global`, `europe`, or full URL.
- Config file: `$XDG_CONFIG_HOME/docuseal/credentials.json` when `XDG_CONFIG_HOME` is set, otherwise `~/.config/docuseal/credentials.json`.

## Timeout Method
- `subprocess.run(timeout=N)` or equivalent child-process timeout.

## Source
- Read `README.md`, `CLAUDE.md`, `skills/docuseal-cli/SKILL.md`, `package.json`, `src/index.js`, `src/commands/configure.js`, `src/lib/config.js`, `src/lib/api.js`, `src/lib/output.js`, `src/lib/data-flags.js`.
- Installed dependencies with `npm ci` after sandboxed install failed on DNS resolution.
- Built local runnable dist with `npm run build`.
