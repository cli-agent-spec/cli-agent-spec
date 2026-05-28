# shopify — Trace

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app init --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
FLAGS
  -n, --name=<value>
      The name for the new app. When provided, skips the app selection prompt and
      creates a new app with this name.
  -p, --path=<value>
      [default: /home/runner/work/cli/cli/packages/cli]
```

**stderr** (first 20 lines):
```

```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `perl -e 'alarm 3; exec @ARGV' -- shopify theme console`
**Exit code:** 255
**Score:** 0/3

**stdout** (first 20 lines):
```
Release notes for 4.1.0
Release highlights:
- [App] The extension-only app template now includes an App Home extension by default
```

**stderr** (first 20 lines):
```
[terminated by alarm after 3 seconds]
```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify theme pull --store invalid.myshopify.com --password [REDACTED] --theme 123 --verbose`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
2026-05-28T11:02:05.709Z: Running command theme pull
2026-05-28T11:02:05.717Z: Running system process in background:
  · Command: /opt/homebrew/Cellar/node/25.9.0_3/bin/node /opt/homebrew/bin/shopify notifications list --ignore-errors
Release notes for 4.1.0
```

**stderr** (first 20 lines):
```
EPERM: operation not permitted, mkdir '/Users/roman/Library/Preferences/shopify-cli-theme-conf-nodejs'
```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify commands --json`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
[
  {
    "summary": "Build the app, including extensions.",
    "descriptionWithMarkdown": "...",
    "flags": { ... }
  }
]
[truncated — 7528 lines total]
```

**stderr** (first 20 lines):
```

```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify auth login`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
To run this command, log in to Shopify.
User verification code: ZGXM-PLJP
Open this link to start the auth process: https://accounts.shopify.com/activate-with-code?...
[process kept running until terminated]
```

**stderr** (first 20 lines):
```

```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `perl -e 'alarm 3; exec @ARGV' -- shopify theme console`
**Exit code:** 255
**Score:** 0/3

**stdout** (first 20 lines):
```
Release notes for 4.1.0
[no structured STDIN_REQUIRED error before timeout]
```

**stderr** (first 20 lines):
```
[terminated by alarm after 3 seconds]
```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify auth login; no expiring authenticated session available`
**Exit code:** 124
**Score:** ?/3

**stdout** (first 20 lines):
```
Could not run the expiry-specific check without a controlled authenticated Shopify session.
```

**stderr** (first 20 lines):
```

```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `perl -e 'alarm 3; exec @ARGV' -- shopify theme console`
**Exit code:** 255
**Score:** 0/3

**stdout** (first 20 lines):
```
Release notes for 4.1.0
[no JSON heartbeat or incremental progress contract observed]
```

**stderr** (first 20 lines):
```
[terminated by alarm after 3 seconds]
```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app bulk execute --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
--query-file  Path to a file containing the GraphQL query or mutation. Can't be used with --query.
--variables   The values for any GraphQL variables in your mutation, in JSON format.
--variable-file Path to a file containing GraphQL variables in JSONL format.
```

**stderr** (first 20 lines):
```

```

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify commands --json`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No editor-requiring command was found in command inventory or help probes.
```

**stderr** (first 20 lines):
```

```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify theme open --store invalid.myshopify.com --password invalid --theme 123`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Release notes for 4.1.0
```

**stderr** (first 20 lines):
```
EPERM: operation not permitted, mkdir '/Users/roman/Library/Preferences/shopify-cli-theme-conf-nodejs'
```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `npm install -g @shopify/cli@latest --no-fund --no-audit; npm install -g @shopify/cli@latest --no-fund --no-audit; shopify --version`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
changed 26 packages in 3s
@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0
```

**stderr** (first 20 lines):
```
npm warn deprecated boolean@3.2.0: Package no longer supported.
```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify auth login < /dev/null`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
To run this command, log in to Shopify.
User verification code: ZGXM-PLJP
Open this link to start the auth process: https://accounts.shopify.com/activate-with-code?...
[process kept running until terminated]
```

**stderr** (first 20 lines):
```

```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app dev --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No generic --timeout, --heartbeat-interval, timeout JSON error, or resume token appears in long-running command help.
```

**stderr** (first 20 lines):
```

```

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app deploy --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No --idempotency-key, universal --dry-run, or effect field contract is documented for mutating commands.
```

**stderr** (first 20 lines):
```

```

## §13 — Partial Failure & Atomicity
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app deploy --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No completed_steps, failed_step, partial, resume token, or rollback-on-failure contract is documented.
```

**stderr** (first 20 lines):
```

```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify theme delete --help; shopify app deploy --dry-run`
**Exit code:** 2
**Score:** 1/3

**stdout** (first 20 lines):
```
theme delete: You're asked to confirm that you want to delete the specified themes. You can skip this confirmation using the --force flag.
app deploy --dry-run: Nonexistent flag: --dry-run
```

**stderr** (first 20 lines):
```

```

## §24 — Authentication & Secret Handling
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify theme pull --store invalid.myshopify.com --password [REDACTED] --theme 123 --verbose`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Verbose output did not echo the fake credential, but --password is accepted as a command-line flag.
```

**stderr** (first 20 lines):
```
EPERM: operation not permitted, mkdir '/Users/roman/Library/Preferences/shopify-cli-theme-conf-nodejs'
```

## §25 — Prompt Injection via Output
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify commands --json`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Command descriptions include external documentation/user-facing content as raw strings without trusted/untrusted markers or metadata separation.
```

**stderr** (first 20 lines):
```

```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify --schema; shopify manifest; shopify --manifest`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
Command --schema not found.
Command manifest not found.
Command --manifest not found.
```

**stderr** (first 20 lines):
```

```

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify app bulk cancel`
**Exit code:** 2
**Score:** 1/3

**stdout** (first 20 lines):
```
The following error occurred:
  Missing required flag id
See more help with --help
```

**stderr** (first 20 lines):
```

```

## §2 — Output Format & Parseability
**Date:** 2026-05-28
**CLI version:** `@shopify/cli/4.1.0 darwin-arm64 node-v25.9.0`
**Check command:** `shopify commands --json; shopify theme pull --store invalid.myshopify.com --password [REDACTED] --theme 123 --verbose`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
shopify commands --json returns valid JSON command metadata, but theme commands emitted release-note boxes and prose errors rather than a consistent ok/data/error envelope.
```

**stderr** (first 20 lines):
```
EPERM: operation not permitted, mkdir '/Users/roman/Library/Preferences/shopify-cli-theme-conf-nodejs'
```
