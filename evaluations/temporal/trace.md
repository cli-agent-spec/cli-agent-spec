# temporal — Trace

## §1 — Exit Codes & Status Signaling
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json workflow start`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
Usage:
  temporal workflow start [flags]

Flags:
      --execution-timeout DURATION   Fail a WorkflowExecution if it lasts
                                     longer than DURATION. This time-out
                                     includes retries and ContinueAsNew
                                     tasks. (default 0s)
      --fail-existing                Fail if the Workflow already exists.
      --fairness-key string          Fairness key (max 64 bytes) for
                                     proportional task dispatch. Tasks
                                     with same key share capacity based
                                     on their weight.
      --fairness-weight float32      Weight [0.001-1000] for this
                                     fairness key. Keys are dispatched
                                     proportionally to their weights.
      --headers stringArray          Temporal workflow headers in
                                     'KEY=VALUE' format. Keys must be
                                     identifiers, and values must be JSON
                                     values. May be passed multiple times
[truncated - 184 lines total]
```

**stderr** (first 20 lines):
```
Error: required flag(s) "task-queue", "type" not set
Error: required flag(s) "task-queue", "type" not set
```

## §2 — Output Format & Parseability
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json workflow start`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Usage:
  temporal workflow start [flags]

Flags:
      --execution-timeout DURATION   Fail a WorkflowExecution if it lasts
                                     longer than DURATION. This time-out
                                     includes retries and ContinueAsNew
                                     tasks. (default 0s)
      --fail-existing                Fail if the Workflow already exists.
      --fairness-key string          Fairness key (max 64 bytes) for
                                     proportional task dispatch. Tasks
                                     with same key share capacity based
                                     on their weight.
      --fairness-weight float32      Weight [0.001-1000] for this
                                     fairness key. Keys are dispatched
                                     proportionally to their weights.
      --headers stringArray          Temporal workflow headers in
                                     'KEY=VALUE' format. Keys must be
                                     identifiers, and values must be JSON
                                     values. May be passed multiple times
[truncated - 184 lines total]
```

**stderr** (first 20 lines):
```
Error: required flag(s) "task-queue", "type" not set
Error: required flag(s) "task-queue", "type" not set
```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --address localhost:17233 --output json workflow delete --query WorkflowId = "missing-audit-workflow" --reason audit`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: must bypass prompts when using JSON output
```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json --address 203.0.113.1:7233 --client-connect-timeout 2s --command-timeout 2s workflow list`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: program interrupted
```

## §12 — Idempotency & Safe Retries
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal workflow start --idempotency-key audit-key --help`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: unknown flag: --idempotency-key
```

## §13 — Partial Failure & Atomicity
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --address localhost:17233 --output json workflow delete --query bad query --reason audit --yes`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: failed counting workflows from query: invalid query: malformed SQL query: syntax error at position 37 near 'query'
```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal workflow delete --dry-run --workflow-id missing-audit-id`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: unknown flag: --dry-run
```

## §24 — Authentication & Secret Handling
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --log-level debug --log-format json --api-key audit-secret-token-12345 --address 127.0.0.1:1 workflow list`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: failed reaching server: connection error: desc = "transport: Error while dialing: dial tcp 127.0.0.1:1: connect: connection refused"
```

## §25 — Prompt Injection via Output
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --env-file /Users/roman/Documents/Codex/2026-07-07/cli-agent-audit-users-roman-pycharmprojects/tmp/temporal-audit/temporal.yaml --config-file /Users/roman/Documents/Codex/2026-07-07/cli-agent-audit-users-roman-pycharmprojects/tmp/temporal-audit/temporal.toml --output json env list`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
[
  {
    "name": "audit"
  },
  {
    "name": "audit2"
  }
]
```

**stderr** (first 20 lines):
```

```

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output ../../etc/test env set --env acme%2Fwidgets --address 127.0.0.1:7233`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: unknown flag: --address
```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal shell`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
The Temporal CLI manages, monitors, and debugs Temporal apps. It lets you run
a local Temporal Service, start Workflow Executions, pass messages to running
Workflows, inspect state, and more.

* Start a local development service:
      `temporal server start-dev`
* View help: pass `--help` to any command:
      `temporal activity complete --help`

Usage:
  temporal [command]

Available Commands:
  activity    Operate on Activity Executions
  batch       Manage running batch jobs
  completion  Generate the autocompletion script for the specified shell
  config      Manage config files (EXPERIMENTAL)
  env         Manage environments
  help        Help about any command
  operator    Manage Temporal deployments
[truncated - 74 lines total]
```

**stderr** (first 20 lines):
```
Error: unknown command
```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --log-level debug --log-format json --api-key audit-secret-token-12345 --address 127.0.0.1:1 workflow list`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: failed reaching server: connection error: desc = "transport: Error while dialing: dial tcp 127.0.0.1:1: connect: connection refused"
```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal workflow list --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
List Workflow Executions. The optional `--query` limits the output to
Workflows matching a Query:

```
temporal workflow list \
    --query YourQuery
```

Visit https://docs.temporal.io/visibility to read more about Search Attributes
and Query creation. See `temporal batch --help` for a quick reference.

View a list of archived Workflow Executions:

```
temporal workflow list \
    --archived
```

Usage:
  temporal workflow list [flags]
[truncated - 120 lines total]
```

**stderr** (first 20 lines):
```

```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json --address 127.0.0.1:1 --client-connect-timeout 1s --command-timeout 2s operator cluster describe`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: failed reaching server: connection error: desc = "transport: Error while dialing: dial tcp 127.0.0.1:1: connect: connection refused"
```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json workflow signal`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Usage:
  temporal workflow signal [flags]

Flags:
      --headers stringArray      Temporal workflow headers in 'KEY=VALUE'
                                 format. Keys must be identifiers, and
                                 values must be JSON values. May be
                                 passed multiple times to set multiple
                                 Temporal headers. Note: These are
                                 workflow headers, not gRPC headers.
  -h, --help                     help for signal
  -i, --input stringArray        Input value. Use JSON content or set
                                 --input-meta to override. Can't be
                                 combined with --input-file. Can be
                                 passed multiple times to pass multiple
                                 arguments.
      --input-base64             Assume inputs are base64-encoded and
                                 attempt to decode them.
      --input-file stringArray   A path or paths for input file(s). Use
                                 JSON content or set --input-meta to
[truncated - 135 lines total]
```

**stderr** (first 20 lines):
```
Error: required flag(s) "name" not set
Error: required flag(s) "name" not set
```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json --address 127.0.0.1:1 --tls-cert-path /Users/roman/Documents/Codex/2026-07-07/cli-agent-audit-users-roman-pycharmprojects/tmp/temporal-audit/missing.crt workflow list`
**Exit code:** 1
**Score:** ?/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: failed to build client options: invalid TLS config: if either client cert or key path is present, other must be present too
```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal server start-dev --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
Run a development Temporal Server on your local system.

```
+------------------------------------------------------------------------+
| WARNING: The development server is not intended for production use.    |
| It skips certain HTTP security checks to make local use simpler.       |
|                                                                        |
| For production use, see:                                               |
| https://docs.temporal.io/production-deployment                         |
+------------------------------------------------------------------------+
```

View the Web UI for the default configuration at: http://localhost:8233

```
temporal server start-dev
```

Add persistence for Workflow Executions across runs:

[truncated - 130 lines total]
```

**stderr** (first 20 lines):
```

```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --output json workflow signal`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Usage:
  temporal workflow signal [flags]

Flags:
      --headers stringArray      Temporal workflow headers in 'KEY=VALUE'
                                 format. Keys must be identifiers, and
                                 values must be JSON values. May be
                                 passed multiple times to set multiple
                                 Temporal headers. Note: These are
                                 workflow headers, not gRPC headers.
  -h, --help                     help for signal
  -i, --input stringArray        Input value. Use JSON content or set
                                 --input-meta to override. Can't be
                                 combined with --input-file. Can be
                                 passed multiple times to pass multiple
                                 arguments.
      --input-base64             Assume inputs are base64-encoded and
                                 attempt to decode them.
      --input-file stringArray   A path or paths for input file(s). Use
                                 JSON content or set --input-meta to
[truncated - 135 lines total]
```

**stderr** (first 20 lines):
```
Error: required flag(s) "name" not set
Error: required flag(s) "name" not set
```

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal config edit`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
Config files are TOML files that contain profiles, with each profile
containing configuration for connecting to Temporal.

```
temporal config set \
    --prop address \
    --value us-west-2.aws.api.temporal.io:7233
```

The default config file path is `$CONFIG_PATH/temporalio/temporal.toml` where
`$CONFIG_PATH` is defined as `$HOME/.config` on Unix,
`$HOME/Library/Application Support` on macOS, and `%AppData%` on Windows.
This can be overridden with the `TEMPORAL_CONFIG_FILE` environment
variable or `--config-file`.

The default profile is `default`. This can be overridden with the
`TEMPORAL_PROFILE` environment variable or `--profile`.

Usage:
  temporal config [command]
[truncated - 77 lines total]
```

**stderr** (first 20 lines):
```
Error: unknown command
```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --open-browser server start-dev`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```
Error: unknown flag: --open-browser
```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal --version`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
```

**stderr** (first 20 lines):
```

```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-07-07
**CLI version:** temporal version 1.7.2 (Server 1.31.1, UI 2.49.1)
**Check command:** `/opt/homebrew/bin/temporal check-permissions --for workflow list`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
Usage:
  temporal [command]

Available Commands:
  activity    Operate on Activity Executions
  batch       Manage running batch jobs
  completion  Generate the autocompletion script for the specified shell
  config      Manage config files (EXPERIMENTAL)
  env         Manage environments
  help        Help about any command
  operator    Manage Temporal deployments
  schedule    Perform operations on Schedules
  server      Run Temporal Server
  task-queue  Manage Task Queues
  worker      Read or update Worker state
  workflow    Start, list, and operate on Workflows

Flags:
      --client-connect-timeout duration                     
                The client connection timeout. 0s means no timeout.
[truncated - 66 lines total]
```

**stderr** (first 20 lines):
```
Error: unknown flag: --for
Error: unknown flag: --for
```
