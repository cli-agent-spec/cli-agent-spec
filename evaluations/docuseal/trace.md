# docuseal-cli - Trace

## Shared Probe Commands

These commands were reused across the per-failure-mode trace blocks below:

- `version`: `node bin/run.js --version` -> exit 0, stdout `1.0.3`
- `help`: `node bin/run.js --help` -> exit 0, prose help on stdout
- `unknown-output`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js templates list --output json` -> exit 1, stderr `error: unknown option '--output'`
- `auth-missing`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js templates list` -> exit 1, stderr uncaught `Error: No API key found...`
- `missing-required`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js submitters update` -> exit 1, stderr `error: missing required argument 'id'`
- `schema`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js --schema --output json` -> exit 1, stderr `error: unknown option '--schema'`
- `json5`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js templates create-html --html '<p>x</p>' --name Test -d '{"key": "value",}'` -> exit 1, stderr `SyntaxError... JSON.parse`
- `missing-file`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config LANG=fr_FR.UTF-8 node bin/run.js templates create-pdf --file /no/such/file --name Test` -> exit 1, stderr `Error: ENOENT...`
- `network-fail`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config DOCUSEAL_API_KEY=bad node bin/run.js templates list --server http://10.255.255.1 --limit 1` -> exit 1, stderr `Error: connect EPERM...`
- `configure-devnull`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js configure` with empty stdin -> exit 0, stdout server prompt only
- `ci-help`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config CI=true NO_UPDATE_NOTIFIER=1 node bin/run.js --help` -> exit 0, prose help on stdout
- `columns-help`: `COLUMNS=40 XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js templates list --help` -> exit 0, wrapped prose help on stdout
- `trace-env`: `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config TOOL_TRACE_ID=test-123 node bin/run.js --help` -> exit 0, no trace metadata

## §34 - Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates create-html --html '<p>x</p>' --name 'acme%2Fwidgets' --output '../../etc/test'`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--output'
```

## §37 - REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for REPL or shell subcommands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No REPL or shell subcommand found.
```

**stderr** (first 20 lines):
```
```

## §42 - Debug / Trace Mode Secret Leakage
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates list --api-key secret --debug`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--debug'
```

## §43 - Tool Output Result Size Unboundedness
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for output size limit, truncation metadata, or `--max-output`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No output limit or truncation metadata found.
```

**stderr** (first 20 lines):
```
```

## §45 - Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `XDG_CONFIG_HOME=/private/tmp/docuseal-cli-empty-config node bin/run.js templates list`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Error: No API key found.
Run `docuseal configure` or set the DOCUSEAL_API_KEY environment variable.
```

## §50 - Stdin Consumption Deadlock
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for stdin-consuming commands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No stdin-consuming command found.
```

**stderr** (first 20 lines):
```
```

## §53 - Credential Expiry Mid-Session
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of API error handling in `src/lib/api.js`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No CREDENTIALS_EXPIRED mapping or reauth_command found.
```

**stderr** (first 20 lines):
```
```

## §60 - OS Output Buffer Deadlock
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for streaming JSON lines or heartbeat protocol.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No streaming or heartbeat protocol found.
```

**stderr** (first 20 lines):
```
```

## §61 - Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for stdin payload commands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No stdin payload command found.
```

**stderr** (first 20 lines):
```
```

## §62 - $EDITOR and $VISUAL Trap
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for editor-requiring commands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No editor-requiring command found.
```

**stderr** (first 20 lines):
```
```

## §64 - Headless Display and GUI Launch Blocking
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for GUI or open-browser commands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No GUI/open-browser command found.
```

**stderr** (first 20 lines):
```
```

## §71 - Non-Interactive Installation Absence
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `npm ci`; `npm run build`; `node bin/run.js --version`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
README documents npm install -g docuseal and npx docuseal.
Local install/build/version succeeded.
```

**stderr** (first 20 lines):
```
No AGENTS.md install protocol found.
```

## §35 - Agent Hallucination Input Patterns
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates create-html --html '<p>x</p>' --name 'acme%2Fwidgets'`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
No structured VALIDATION_ERROR for percent-encoded resource name before API execution.
```

## §38 - Runtime Dependency Version Mismatch
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/package inspection for `engines` and startup runtime check.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
package.json has no engines field; no runtime-version startup JSON found.
```

**stderr** (first 20 lines):
```
```

## §40 - parse() vs parseAsync() Silent Race Condition
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of `src/index.js`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
program.parse() is used while registered action handlers are async.
```

**stderr** (first 20 lines):
```
```

## §41 - Update Notifier Side-Channel Output Pollution
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `CI=true NO_UPDATE_NOTIFIER=1 node bin/run.js --help`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
Usage: docuseal [options] [command]
...
```

**stderr** (first 20 lines):
```
No update notification emitted.
```

## §46 - API Schema to CLI Flag Translation Loss
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for `--json`, `-d`, and API schema validation.
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
-d accepts JSON and bracket notation.
No --json full-body flag or API-schema validation found.
```

**stderr** (first 20 lines):
```
```

## §47 - MCP Wrapper Schema Staleness
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/repo inspection for MCP wrapper health.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No MCP wrapper or _wrapper_health command found.
```

**stderr** (first 20 lines):
```
```

## §49 - Async Job / Polling Protocol Absence
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for async job and status commands.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No async job/status protocol found.
```

**stderr** (first 20 lines):
```
```

## §51 - Shell Word Splitting and Glob Expansion Interference
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates create-pdf --file '/no/such file.pdf' --name Test`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Error: ENOENT: no such file or directory, open '/no/such file.pdf'
```

## §54 - Conditional / Dependent Argument Requirements
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for arg groups and missing_args structured validation.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No arg_groups, --validate-only, or missing_args array found.
```

**stderr** (first 20 lines):
```
```

## §55 - Silent Data Truncation
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for max lengths and FIELD_TRUNCATED warnings.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No max_length schema or FIELD_TRUNCATED protocol found.
```

**stderr** (first 20 lines):
```
```

## §56 - Exit Code Masking in Shell Pipelines
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates list --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--output'
```

## §58 - Multi-Agent Concurrent Invocation Conflict
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of `saveConfig()`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
saveConfig() writes JSON directly with no locking.
```

**stderr** (first 20 lines):
```
```

## §59 - High-Entropy String Token Poisoning
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of `configure --list`.
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
apiKey is masked as first 8 + ... + last 4.
No semantic summary/unmask protocol.
```

**stderr** (first 20 lines):
```
```

## §65 - Global Configuration State Contamination
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of config path and configure command.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Default config path is ~/.config/docuseal/credentials.json; no --global flag required.
```

**stderr** (first 20 lines):
```
```

## §66 - Symlink Loop and Recursive Traversal Exhaustion
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for recursive traversal commands.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No recursive traversal command found.
```

**stderr** (first 20 lines):
```
```

## §67 - Agent-Generated Input Syntax Rejection
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates create-html --html '<p>x</p>' --name Test -d '{"key": "value",}'`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
SyntaxError: Expected double-quoted property name in JSON at position 16
```

## §68 - Third-Party Library Stdout Pollution
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection for stdout interception and warnings envelope.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No stdout interceptor or warnings envelope found.
```

**stderr** (first 20 lines):
```
```

## §69 - Argument Order Ambiguity
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --api-key test templates list` and `node bin/run.js templates list --api-key test`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Subcommand-level global flags are supported after subcommand.
```

**stderr** (first 20 lines):
```
Root-level --api-key placement is rejected as unknown.
```

## §70 - Single-Argument Arity Forcing Agent Loop Overhead
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for variadic destructive/resource commands.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Single-ID commands use one positional id; no variadic results array.
```

**stderr** (first 20 lines):
```
```

## §72 - Integration Artifact Version Drift
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Compare `node bin/run.js --version` with `skills/docuseal-cli/SKILL.md`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Binary/package version: 1.0.3
Skill metadata version: 1.0.6
```

**stderr** (first 20 lines):
```
```

## §73 - Documentation Accuracy Drift
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Inspect AGENTS.md/CLAUDE.md/skill docs against help and version.
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
No AGENTS.md found. CLAUDE.md and skill docs exist; skill version drifts from binary.
```

**stderr** (first 20 lines):
```
```

## §44 - Agent Knowledge Packaging Absence
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --schema --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Repository includes CLAUDE.md and skills/docuseal-cli/SKILL.md.
```

**stderr** (first 20 lines):
```
error: unknown option '--schema'
```

## §52 - Recursive Command Tree Discovery Cost
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --schema --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--schema'
```

## §57 - Locale-Dependent Error Messages
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `LANG=fr_FR.UTF-8 node bin/run.js templates create-pdf --file /no/such/file --name Test`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Error: ENOENT: no such file or directory, open '/no/such/file'
```

## §63 - Terminal Column Width Output Corruption
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `COLUMNS=40 node bin/run.js templates list --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Help prose wraps long strings at terminal width; no JSON mode exists.
```

**stderr** (first 20 lines):
```
```

## §10 - Interactivity & TTY Requirements
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js configure` with empty stdin
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
Server [global | europe | https://docuseal.yourdomain.com] (default: global):
```

**stderr** (first 20 lines):
```
```

## §11 - Timeouts & Hanging Processes
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `DOCUSEAL_API_KEY=bad node bin/run.js templates list --server http://10.255.255.1 --limit 1`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Error: connect EPERM 10.255.255.1:80 - Local (0.0.0.0:0)
```

## §12 - Idempotency & Safe Retries
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for `--idempotency-key` and effect fields.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No --idempotency-key or effect/noop response field found.
```

**stderr** (first 20 lines):
```
```

## §13 - Partial Failure & Atomicity
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for partial failure and resume protocol.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No partial/resume protocol found.
```

**stderr** (first 20 lines):
```
```

## §14 - Argument Validation Before Side Effects
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js submitters update`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: missing required argument 'id'
```

## §15 - Race Conditions & Concurrency
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection for lock handling in mutating/config operations.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No lock handling found.
```

**stderr** (first 20 lines):
```
```

## §16 - Signal Handling & Graceful Cancellation
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection for SIGTERM/SIGPIPE handlers.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No SIGTERM partial-result handler found.
```

**stderr** (first 20 lines):
```
```

## §17 - Child Process Leakage
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for background child processes.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No command found that spawns background child processes.
```

**stderr** (first 20 lines):
```
```

## §23 - Side Effects & Destructive Operations
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates archive --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No --dry-run or danger declaration found for archive commands.
```

**stderr** (first 20 lines):
```
```

## §24 - Authentication & Secret Handling
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/help inspection for secret input paths.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Hidden --api-key flag is accepted on commands; no framework redaction policy found.
```

**stderr** (first 20 lines):
```
```

## §25 - Prompt Injection via Output
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of `renderJson` API response handling.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
External API data is rendered raw without trusted/untrusted envelope.
```

**stderr** (first 20 lines):
```
```

## §74 - Credential Scope Declaration Absence
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --schema`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--schema'
```

## §1 - Exit Codes & Status Signaling
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Missing required arg, missing auth, and network failure probes.
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
All observed failures exited 1; no semantic exit-code table found.
```

## §2 - Output Format & Parseability
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates list --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--output'
```

## §3 - Stderr vs Stdout Discipline
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of `src/lib/output.js` and help/configure probes.
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
renderError and renderSuccess write prose to stdout.
```

**stderr** (first 20 lines):
```
```

## §5 - Pagination & Large Output
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates list --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
--limit, --after, and --before flags exist. No standard pagination envelope exists.
```

**stderr** (first 20 lines):
```
```

## §8 - ANSI & Color Code Leakage
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --help | cat`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No ANSI escape sequences observed.
```

**stderr** (first 20 lines):
```
```

## §9 - Binary & Encoding Safety
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of file upload handling.
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
File upload commands use Buffer.from(readFileSync(file)).toString('base64').
```

**stderr** (first 20 lines):
```
Errors remain unstructured.
```

## §4 - Verbosity & Token Cost
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `CI=true node bin/run.js --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
Usage: docuseal [options] [command]
...
```

**stderr** (first 20 lines):
```
No --quiet or CI structured mode found.
```

## §6 - Command Composition & Piping
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Help/source inspection for `--output id` and stdin `-` ID support.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No --output id or stdin ID protocol found.
```

**stderr** (first 20 lines):
```
```

## §7 - Output Non-Determinism
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection for stable-output mode and sorting.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Raw API output is emitted; no --stable-output or volatile-field isolation found.
```

**stderr** (first 20 lines):
```
```

## §26 - Stateful Commands & Session Management
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js status --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown command 'status'
```

## §28 - Config File Shadowing & Precedence
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/README inspection and `node bin/run.js configure --help`.
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
README documents CLI flag > environment variable > config file.
configure --list is prose and has no per-field sources.
```

**stderr** (first 20 lines):
```
```

## §31 - Network Proxy Unawareness
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `HTTPS_PROXY=http://127.0.0.1:9 DOCUSEAL_API_KEY=bad node bin/run.js templates list --limit 1`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Network errors include no network_context.proxy_used.
```

## §32 - Self-Update & Auto-Upgrade Behavior
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source/package inspection for self-update or update notifier.
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No self-update behavior found.
```

**stderr** (first 20 lines):
```
```

## §27 - Platform & Shell Portability
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js doctor --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown command 'doctor'
```

## §29 - Working Directory Sensitivity
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Source inspection of file path handling.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
File paths are resolved relative to current working directory; no meta.cwd or --cwd.
```

**stderr** (first 20 lines):
```
```

## §30 - Undeclared Filesystem Side Effects
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js status --show-side-effects --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown command 'status'
```

## §18 - Error Message Quality
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js templates create-html --html '<p>x</p>' --name Test -d '{"key": "value",}'`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
SyntaxError: Expected double-quoted property name in JSON at position 16
```

## §19 - Retry Hints in Error Responses
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Error probe inspection for `retryable` and `retry_after_ms`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No retryable or retry_after_ms fields found.
```

**stderr** (first 20 lines):
```
```

## §22 - Schema Versioning & Output Stability
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** Response/source inspection for `meta.schema_version`.
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No meta.schema_version found.
```

**stderr** (first 20 lines):
```
```

## §20 - Environment & Dependency Discovery
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js doctor --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown command 'doctor'
```

## §21 - Schema & Help Discoverability
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `node bin/run.js --schema --output json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
error: unknown option '--schema'
```

## §33 - Observability & Audit Trail
**Date:** 2026-05-20
**CLI version:** 1.0.3
**Check command:** `TOOL_TRACE_ID=test-123 node bin/run.js --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Usage: docuseal [options] [command]
```

**stderr** (first 20 lines):
```
No meta.trace_id, request_id, or duration_ms emitted.
```
