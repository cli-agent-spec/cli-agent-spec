# langfuse — Trace

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse --public-key pk-test --secret-key sk-test api prompts get ../../etc/test --curl`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```text
curl -sS -X GET -H 'authorization: Basic cGs...XN0' 'https://cloud.langfuse.com/api/public/v2/prompts/..%2F..%2Fetc%2Ftest'
```

**stderr** (first 20 lines):
```text

```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```text
Commands:
  api                     Interact with the Langfuse REST API
  get-skill               Print the latest Langfuse skill from GitHub
```

**stderr** (first 20 lines):
```text

```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse --public-key pk-test --secret-key sk-test api traces list --limit 1 --curl`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```text
curl -sS -X GET -H 'authorization: Basic cGs...XQ=' 'https://cloud.langfuse.com/api/public/traces?limit=1'
```

**stderr** (first 20 lines):
```text

```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api traces list --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
Options include --limit and --fields, but no --max-output, --max-length, meta.truncated, or total_bytes contract.
```

**stderr** (first 20 lines):
```text

```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api healths list --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"ok":false,"error":"Missing --username for basic auth"}
```

**stderr** (first 20 lines):
```text

```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api traces get`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```text
error: missing required argument 'trace-id'
```

**stderr** (first 20 lines):
```text

```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `not run — requires a real expired Langfuse credential`
**Exit code:** 124
**Score:** ?/3

**stdout** (first 20 lines):
```text
No expired credential was available in the audit environment.
```

**stderr** (first 20 lines):
```text

```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `not run — requires a long-running streaming command`
**Exit code:** 124
**Score:** ?/3

**stdout** (first 20 lines):
```text
No long-running streaming command was available without authenticated project operations.
```

**stderr** (first 20 lines):
```text

```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```text
No stdin payload command or stdin fallback is exposed by the command surface.
```

**stderr** (first 20 lines):
```text

```

## §62 — `$EDITOR` and `$VISUAL` Trap
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `EDITOR= VISUAL= ./node_modules/.bin/langfuse --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```text
No editor-requiring command is exposed.
```

**stderr** (first 20 lines):
```text

```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `DISPLAY= ./node_modules/.bin/langfuse --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```text
No GUI/browser-opening command is exposed.
```

**stderr** (first 20 lines):
```text

```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `npm install`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```text
up to date, audited 31 packages in 688ms
found 0 vulnerabilities
```

**stderr** (first 20 lines):
```text

```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api healths list --json < /dev/null`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```json
{"ok":false,"error":"Missing --username for basic auth"}
```

**stderr** (first 20 lines):
```text

```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse --public-key pk-test --secret-key sk-test --host http://10.255.255.1 api traces list --limit 1 --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"ok":false,"error":"fetch failed"}
```

**stderr** (first 20 lines):
```text

```

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api datasets create --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
Usage: datasets create [options]
Required:
  --name <string> (required)
Global options include --curl and --json; no --idempotency-key, effect field, or --dry-run is documented.
```

**stderr** (first 20 lines):
```text

```

## §13 — Partial Failure & Atomicity
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `not run — requires authenticated multi-step operation with controlled mid-run failure`
**Exit code:** 124
**Score:** ?/3

**stdout** (first 20 lines):
```text
No safe credential-free multi-step failure path was available.
```

**stderr** (first 20 lines):
```text

```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api traces delete-public --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
Usage: traces delete-public <trace-id> [options]
Global options include --curl and --json; no --dry-run, confirmation flag, danger_level, or affected-scope preview is documented.
```

**stderr** (first 20 lines):
```text

```

## §24 — Authentication & Secret Handling
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse --public-key SECRET_VALUE_123 --secret-key SECRET_VALUE_456 api traces list --limit nope --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
error: option '--limit <value>' argument 'nope' is invalid. Expected integer, got 'nope'
```

**stderr** (first 20 lines):
```text

```

## §25 — Prompt Injection via Output
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api __schema --json`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```json
{"ok":true,"data":{"title":"langfuse","version":"3.0.1", "...":"external/API data is returned under data without trusted:false annotations"}}
```

**stderr** (first 20 lines):
```text

```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api __schema --json`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```json
{"ok":true,"data":{"authSchemes":[{"key":"BasicAuth","kind":"http-basic","scheme":"basic"}],"resources":[...]}}
```

**stderr** (first 20 lines):
```text

```

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api traces get --json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```text
error: missing required argument 'trace-id'
```

**stderr** (first 20 lines):
```text

```

## §2 — Output Format & Parseability
**Date:** 2026-05-22
**CLI version:** `langfuse-cli` 0.0.10
**Check command:** `./node_modules/.bin/langfuse api no-such list --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
error: unknown command 'no-such'

Usage: langfuse api [options] [command]
```

**stderr** (first 20 lines):
```text

```
