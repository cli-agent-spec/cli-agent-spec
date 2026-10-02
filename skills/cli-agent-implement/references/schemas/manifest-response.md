# Schema: ManifestResponse

**File:** [`manifest-response.json`](manifest-response.json)

> **Used by:** [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) · [REQ-O-030](../requirements/o-030-opt-in-audit-log.md) · [REQ-O-013](../requirements/o-013-schema-output-schema-flag.md) · [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) · [REQ-C-002](../requirements/c-002-command-declares-danger-level.md) · [REQ-C-005](../requirements/c-005-interactive-commands-must-support-yes-non-interact.md) · [REQ-C-008](../requirements/c-008-multi-step-commands-emit-step-manifest.md) · [REQ-C-010](../requirements/c-010-background-process-commands-declare-metadata.md) · [REQ-C-011](../requirements/c-011-commands-declare-filesystem-side-effects.md) · [REQ-C-012](../requirements/c-012-commands-with-network-i-o-support-timeout.md) · [REQ-C-015](../requirements/c-015-commands-declare-input-and-output-schema.md) · [REQ-C-016](../requirements/c-016-secrets-accepted-only-via-env-var-or-file.md) · [REQ-C-018](../requirements/c-018-commands-declare-platform-requirements.md) · [REQ-C-019](../requirements/c-019-subprocess-invoking-commands-declare-argument-sche.md) · [REQ-C-020](../requirements/c-020-resource-id-fields-declare-validation-pattern.md) · [REQ-C-021](../requirements/c-021-auth-commands-declare-headless-mode-support.md) · [REQ-C-022](../requirements/c-022-async-commands-declare-job-descriptor-schema.md) · [REQ-C-023](../requirements/c-023-editor-requiring-commands-declare-non-interactive-.md) · [REQ-C-024](../requirements/c-024-gui-launching-commands-declare-headless-behavior.md) · [REQ-C-025](../requirements/c-025-config-writing-commands-declare-write-scope.md) · [REQ-C-026](../requirements/c-026-commands-declare-conditional-argument-dependencies.md) · [REQ-C-027](../requirements/c-027-commands-declare-option-placement.md) · [REQ-C-029](../requirements/c-029-command-declares-required-scopes.md) · [REQ-F-051](../requirements/f-051-debug-and-trace-mode-secret-redaction.md) · [REQ-F-073](../requirements/f-073-env-var-namespace-prefix.md) · [REQ-F-079](../requirements/f-079-global-option-scope.md) · [REQ-O-004](../requirements/o-004-output-jsonl-stream-flag.md) · [REQ-O-031](../requirements/o-031-dependency-version-matrix-declaration.md) · [REQ-O-042](../requirements/o-042-output-format-env-var-default.md) · [REQ-O-048](../requirements/o-048-destructive-commands-default-dry-run.md) · [REQ-O-049](../requirements/o-049-llm-token-budget-flags.md) · [REQ-F-054](../requirements/f-054-stdin-payload-size-cap-with-input-file-fallback.md) · [REQ-C-031](../requirements/c-031-passthrough-commands-delegate-to-another-parser.md) · [REQ-F-038](../requirements/f-038-verbosity-auto-quiet-in-non-tty-context.md) · [REQ-O-001](../requirements/o-001-output-format-flag.md)
> Returned as the `data` field of a [`ResponseEnvelope`](response-envelope.md).

---

## Purpose

`tool manifest` returns every command, flag, exit code, and declared contract in one response. It replaces the O(N) loop of `--help` calls (§52) and is the only place an agent learns, before calling, whether a command mutates state, needs credentials, prompts, opens an editor, forwards arguments verbatim, or runs asynchronously.

Two decisions shape the type:

- **Flat map, not a tree.** `commands` is keyed by dot-separated path so lookup is O(1); `subcommands` arrays carry hierarchy
- **Closed entries.** `CommandEntry` and `FlagEntry` reject unknown fields. Every field a Command Contract requirement declares is named here, so a manifest that validates is a manifest an agent can fully read

---

## Values

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string `3.MINOR` | yes | Contract version; `3.x` for this schema. From `3.0`, global options live in the root `flags` |
| `framework_version` | string | yes | Version of the tool binary |
| `etag` | string | yes | Deterministic content hash. Changes only when registrations change |
| `commands` | `Record<string, CommandEntry>` | yes | Flat map keyed by dot-separated path such as `"deploy.rollback"` |
| `flags` | `Record<string, FlagEntry>` | no | Global options every command accepts in any position, keyed by name without `--`; only `format` may carry `media_types` (REQ-F-079) |
| `exit_codes` | `Record<string, ExitCodeEntry>` | no | Shared exit-code table every command inherits |
| `dependencies` | `DependencyEntry[]` | no | External runtime dependencies checked by `tool doctor` (REQ-O-031) |
| `env_vars` | `EnvVarEntry[]` | no | Variables the tool reads that back no flag and supply no secret, such as `TOOL_DEBUG` or `TOOL_AUDIT_LOG`; each entry carries `description`. A name without the tool prefix immediately follows the entry for its setting's prefixed name, which wins. Universal names (`NO_COLOR`, `HOME`, ...) are not listed (REQ-F-073) |
| `secret_env_vars` | string[] | no | Variables that supply a secret every command reads, such as a tool-wide API key; names only, never a value or default. A name here appears in no command's `secret_env_vars` and no flag's `env_vars` (REQ-F-073, REQ-C-016) |

### CommandEntry — core

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | One-sentence summary |
| `danger_level` | `"safe"` \| `"mutating"` \| `"destructive"` | yes | Mutation risk level (REQ-C-002) |
| `required_scopes` | string[] | yes | Minimal permission strings, most critical first; empty when no auth is needed (REQ-C-029) |
| `flags` | `Record<string, FlagEntry>` | yes | Command-local flags keyed by name without `--`; never repeats a name or short alias from the root `flags` |
| `positionals` | `PositionalEntry[]` | no | Positional arguments in call order; absent when there are none (REQ-C-015) |
| `exit_codes` | `Record<string, ExitCodeEntry>` | yes | Keyed by integer code as string (REQ-C-001). With a root `exit_codes` table present, holds only the command's additions and overrides; the effective table is root overlaid with this map, and `tool <cmd> --schema` prints it in full |
| `aliases` | string[] | no | Alternative invocation names |
| `output_schema` | object | no | JSON Schema for `data` on success (REQ-C-015) |
| `output_formats` | string[] | no | Formats beyond the framework defaults (REQ-O-049) |
| `output_media_types` | `MediaTypeMap` | no | Media type each `--format` value writes for this command, overriding the root `media_types`; required for an `output_formats` value neither the spec's table nor the root map covers (REQ-O-049) |
| `examples` | `Example[]` | no | Verbatim invocations |
| `subcommands` | string[] | no | Dot-separated paths of direct children |
| `builtin` | boolean | no | `true` when the framework registers the command, not the application; also `true` on a built-in's subcommands, `false` on an application command that replaces a built-in's name. Absent means `false` (REQ-O-041) |

### CommandEntry — declared contracts

Present only when the command declares them.

| Field | Type | Description |
|-------|------|-------------|
| `output_file` | `"formatted"` \| `"binary"` \| `"handler"` \| `"envelope"` | Command registers `--output <path>`. `formatted`: the file gets the `--format` representation; `binary`: the file gets the raw bytes and `data` is `{path, bytes, content_type, sha256}`, and `--output -` exits `2`; `handler`: the handler writes the file, described by the command's documentation; `envelope`: the file gets the final `ResponseEnvelope` as JSON whatever `--format` says (REQ-O-001) |
| `output_file_base` | `"cwd"` \| `"project_root"` \| `"resource"` | Directory a relative `--output` path resolves against; only with `output_file`, absent means `cwd`. An absolute path is used as given (REQ-O-001) |
| `stdin` | `StdinDeclaration` | Command declares stdin input; `--input-file` exists and reads the same way. `mode` is `buffered` (whole, up to `max_bytes`), `lines` (one line at a time, each up to `max_line_bytes`, no total cap), or `records` (lines checked against `record_schema`, ended by a `_summary` line) (REQ-F-054, REQ-O-004) |
| `idempotent` | boolean | A repeat with the same arguments converges on the same state, whatever a previous attempt left behind; a non-retryable exit with `side_effects: "partial"` is recovered by rerunning the identical command. Absent means `false`; redundant on a `safe` command. Not `--idempotency-key`, which deduplicates one request (REQ-C-002) |
| `option_placement` | `"any"` \| `"strict"` | `strict`: every option, global or local, precedes the first positional; absent means `any` (REQ-C-027) |
| `arguments` | `"declared"` \| `"passthrough"` | `passthrough`: every token after the command path goes verbatim to another tool, which owns stdout and the exit code; the envelope is the last line of stderr. Requires `option_placement: "strict"`, empty `flags`, and no `positionals`, and excludes `danger_level: "destructive"`; absent means `declared` (REQ-C-031) |
| `help_argv` | string[] | Passthrough only: the argv forwarded in place of a lone `--help` or `-h` after the command path; absent means the token is forwarded unchanged (REQ-C-031) |
| `stderr` | `"child_log"` | `child_log`: stderr carries a wrapped program's output as plain text, line by line, whatever `--format` and verbosity say; `--quiet` silences it, and stdout carries only the envelope. Absent means stderr carries the framework's own diagnostics only. Never on a passthrough command (REQ-F-038) |
| `interactive` | boolean | Command may prompt in a TTY; `--yes` and `--non-interactive` exist (REQ-C-005) |
| `has_network_io` | boolean | Command performs network or long blocking I/O; `--timeout` exists (REQ-C-012) |
| `steps` | string[] | Ordered step names of a multi-step command (REQ-C-008) |
| `spawns_background_process` | boolean | Command starts a child that outlives it (REQ-C-010) |
| `cleanup_command` | string | Exact command that stops that child (REQ-C-010) |
| `max_lifetime_seconds` | integer | Upper bound on the child's lifetime (REQ-C-010) |
| `filesystem_side_effects` | `FilesystemSideEffect[]` | Paths the command may write, with category and TTL (REQ-C-011) |
| `secret_env_vars` | string[] | Environment variables that supply this command's secrets beyond the root `secret_env_vars` (REQ-C-016); a secret is never a flag value, so these names never appear in a flag's `env_vars` |
| `platform` | string[] | Supported OS names; absent means all (REQ-C-018) |
| `required_tools` | `Record<string, string>` | External binaries and minimum versions (REQ-C-018) |
| `subprocess` | `SubprocessDeclaration` | Child binary and which flags reach its argv (REQ-C-019) |
| `headless_supported` | boolean | Auth command works without a TTY (REQ-C-021) |
| `token_env_vars` | string[] | Pre-acquired token variables; required when `headless_supported` is `false` (REQ-C-021). A name here is not repeated in this command's `secret_env_vars` (REQ-F-073) |
| `async` | boolean | Command returns a job descriptor (REQ-C-022) |
| `job_descriptor_schema` | object | JSON Schema of that job descriptor (REQ-C-022) |
| `requires_editor` | boolean | Command opens `$EDITOR` unless an alternative is given (REQ-C-023) |
| `non_interactive_alternatives` | string[] | Flags that bypass the editor; required with `requires_editor` (REQ-C-023) |
| `gui_operations` | string[] | Display operations performed (REQ-C-024) |
| `headless_behavior` | `"emit_in_output"` \| `"skip"` \| `"error"` | Headless handling of `gui_operations`; required with them (REQ-C-024) |
| `config_write_scope` | `"local"` \| `"global"` \| `"session"` | Scope of config files written (REQ-C-025) |
| `requires` | `ConditionalRule[]` | Conditional argument dependencies (REQ-C-026) |
| `streaming_default` | boolean | Command streams JSONL unless `--no-stream` (REQ-O-004) |
| `safe_default` | boolean | Command dry-runs unless `--live` (REQ-O-048) |
| `confirm_flag` | string | Boolean flag, without `--`, of the command or root that runs the command; without it the command previews (`would_*` effect, `meta.dry_run: true`, exit `0`), and `--dry-run` wins over it. Only on `mutating` or `destructive` commands, never with `safe_default: true` or `arguments: "passthrough"` (REQ-O-048) |

### FlagEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"string"` \| `"integer"` \| `"number"` \| `"boolean"` \| `"array"` \| `"enum"` \| `"object"` | yes | Value type; an `object` value is one argv token of JSON text (REQ-C-015) |
| `required` | boolean | yes | Flag must be present |
| `description` | string | yes | What the flag controls, including range or format |
| `default` | any | no | Omit (do not set `null`) when no default exists |
| `enum_values` | string[] | no | Only when `type` is `"enum"` |
| `short` | string (1 char) | no | Single-character shorthand |
| `pattern` | string | no | Anchored regex the value must match; exclusive with `pattern_type` (REQ-C-020) |
| `pattern_type` | `"alphanumeric_id"` \| `"uuid"` \| `"semver"` \| `"filepath"` \| `"url"` | no | Built-in validation preset (REQ-C-020) |
| `env_vars` | `EnvVarEntry[]` | no | Variables the flag reads when not passed, in precedence order (first set wins); the tool-prefixed name comes first whenever a name without the prefix is listed. Never a secret (REQ-F-073) |
| `schema` | JSON Schema object | when `type` is `"object"` | Draft-07 schema of one value: the object itself for `object`, one item for `array`; never on other types (REQ-C-015) |
| `media_types` | `MediaTypeMap` | when the root `format` flag lists a value outside the spec's table | Root `format` flag only, with `type: "enum"`: media type of each `enum_values` value. Every key is in `enum_values`; a spec value listed here maps to the spec's media type (REQ-O-001) |

### PositionalEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Name shown in help and errors; the caller never types it |
| `type` | `"string"` \| `"integer"` \| `"number"` \| `"enum"` | yes | Value type |
| `required` | boolean | yes | Must be given; an optional positional never precedes a required one |
| `description` | string | yes | What the argument selects, including range or format |
| `enum_values` | string[] | when `type` is `"enum"` | Exhaustive list of accepted values |
| `variadic` | boolean | no | Takes every remaining value; last entry only |

### Supporting types

| Type | Fields |
|------|--------|
| `Example` | `description`, `command` (both required) |
| `FilesystemSideEffect` | `path`, `type` (`cache` \| `log` \| `temp` \| `credential` \| `config` \| `output`) required; `ttl_seconds`, `clearable_with` optional, and never on `output` (the command's product, which `cleanup` never removes) |
| `SubprocessDeclaration` | `binary` required; `user_controlled_args`, `hardcoded_args` optional |
| `ConditionalRule` | One of `{ if_flag, if_value, then_required }`, `{ if_flag, prohibited }`, `{ if_flag, target_flag, default }`, `{ any_of }` (at least one listed flag present), `{ one_of }` (exactly one listed flag present); `any_of` and `one_of` list at least two distinct flags. A declared `default` and a boolean flag given as false (`--no-exact`) are not present; `if_value` compares values, so `if_value: false` matches an explicit false (REQ-C-026) |
| `DependencyEntry` | `name`, `check_command`, `min_version` required; `version_regex`, `fix_command` optional |
| `EnvVarEntry` | `name` required; `deprecated` optional (boolean, absent means `false`); `description` optional in a flag's `env_vars`, required in root `env_vars` |
| `MediaTypeMap` | Map from a `--format` value to a lowercase `type/subtype` media type without parameters, such as `{"html": "text/html"}`; at least one entry |
| `StdinDeclaration` | `mode` (`buffered` \| `lines` \| `records`) required; `max_bytes` (buffered only, absent means `65536`), `max_line_bytes` (lines and records only, absent means `1048576`), `record_schema` (records only, required there) |

---

## Examples

**Valid — two commands with declared contracts**
```json
{
  "schema_version": "3.0",
  "framework_version": "2.1.0",
  "etag": "sha256:a3f9c1",
  "flags": {
    "format": { "type": "enum", "required": false, "enum_values": ["json", "jsonl", "tsv", "plain"], "description": "Output representation; json when stdout is not a terminal, plain in a terminal" }
  },
  "commands": {
    "deploy": {
      "description": "Deploy a build to a target environment",
      "danger_level": "mutating",
      "required_scopes": ["deploy:write"],
      "has_network_io": true,
      "flags": {
        "target":  { "type": "enum", "required": true, "enum_values": ["staging", "prod"], "description": "Target environment" },
        "dry-run": { "type": "boolean", "required": false, "default": false, "short": "n", "description": "Validate without executing" },
        "build-id": { "type": "string", "required": true, "pattern_type": "alphanumeric_id", "description": "Build to deploy" }
      },
      "exit_codes": {
        "0":  { "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" },
        "2":  { "name": "ARG_ERROR", "description": "Invalid target or build id", "retryable": false, "side_effects": "none" },
        "10": { "name": "TIMEOUT", "description": "Deployment timed out; partial writes may have occurred", "retryable": false, "side_effects": "partial" }
      },
      "requires": [{ "if_flag": "target", "if_value": "prod", "then_required": ["build-id"] }],
      "examples": [{ "description": "Preview a staging deploy", "command": "tool deploy --target staging --build-id b42 --dry-run" }],
      "subcommands": ["deploy.rollback"]
    },
    "deploy.rollback": {
      "description": "Roll back the most recent deployment",
      "danger_level": "destructive",
      "required_scopes": ["deploy:write"],
      "safe_default": true,
      "flags": {},
      "positionals": [{ "name": "target", "type": "enum", "required": true, "enum_values": ["staging", "prod"], "description": "Environment to roll back" }],
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Rollback completed or previewed", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```

**Valid — application command next to a built-in**
```json
{
  "schema_version": "3.1",
  "framework_version": "2.1.0",
  "etag": "sha256:c71e08",
  "commands": {
    "deploy": {
      "description": "Deploy a build to a target environment",
      "danger_level": "mutating",
      "required_scopes": ["deploy:write"],
      "flags": {},
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" } }
    },
    "manifest": {
      "description": "Print the full command tree as JSON",
      "danger_level": "safe",
      "required_scopes": [],
      "builtin": true,
      "flags": {
        "etag": { "type": "string", "required": false, "description": "Etag of a cached manifest; returns meta.not_modified when unchanged" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Manifest returned or unchanged", "retryable": false, "side_effects": "none" } }
    }
  }
}
```
`deploy` omits `builtin`, so it is an application command; an agent building a task list keeps it and drops `manifest`.

**Valid — command that needs exactly one identifier flag**
```json
{
  "schema_version": "3.2",
  "framework_version": "2.1.0",
  "etag": "sha256:5d20b4",
  "commands": {
    "quote": {
      "description": "Fetch the latest quote for one instrument",
      "danger_level": "safe",
      "required_scopes": [],
      "has_network_io": true,
      "flags": {
        "isin":   { "type": "string", "required": false, "description": "Instrument ISIN" },
        "figi":   { "type": "string", "required": false, "description": "Instrument FIGI" },
        "symbol": { "type": "string", "required": false, "description": "Instrument ticker symbol" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Quote returned", "retryable": false, "side_effects": "none" } },
      "requires": [{ "one_of": ["isin", "figi", "symbol"] }]
    }
  }
}
```
Each flag is optional on its own; the `one_of` rule makes exactly one of them mandatory. `tool quote --symbol AAPL` passes, while `tool quote` and `tool quote --isin US0378331005 --symbol AAPL` exit `2`.

**Valid — command that writes a binary result to a file**
```json
{
  "schema_version": "3.3",
  "framework_version": "2.2.0",
  "etag": "sha256:4be9a1",
  "commands": {
    "download": {
      "description": "Download a Flex report",
      "danger_level": "safe",
      "required_scopes": [],
      "output_file": "binary",
      "has_network_io": true,
      "flags": {
        "output": { "type": "string", "required": false, "description": "Path that receives the report's raw bytes" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Report written", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
`tool download --output report.xml` writes the XML itself to `report.xml`, and `data` carries `path`, `bytes`, `content_type`, and `sha256`.

**Valid — flags that fall back to environment variables**
```json
{
  "schema_version": "3.4",
  "framework_version": "2.3.0",
  "etag": "sha256:9d02f7",
  "flags": {
    "format": {
      "type": "enum",
      "required": false,
      "enum_values": ["json", "jsonl", "tsv", "plain"],
      "description": "Output representation; json when stdout is not a terminal, plain in a terminal",
      "env_vars": [{ "name": "TOOL_FORMAT" }]
    }
  },
  "commands": {
    "deploy": {
      "description": "Deploy a build to a project",
      "danger_level": "mutating",
      "required_scopes": ["deploy:write"],
      "secret_env_vars": ["TOOL_TOKEN"],
      "flags": {
        "project": {
          "type": "string",
          "required": true,
          "description": "Project to deploy to",
          "env_vars": [{ "name": "TOOL_PROJECT" }, { "name": "CLOUDFALL_PROJECT" }, { "name": "TOOL_PROJECT_ID", "deprecated": true }]
        }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
`--project` wins over every variable; without it the tool reads `TOOL_PROJECT`, then `CLOUDFALL_PROJECT` (shared across the tool family), then the deprecated `TOOL_PROJECT_ID`. The token stays in `secret_env_vars`, never in a flag's `env_vars`. `TOOL_FORMAT` is the `--format` default from REQ-O-042.

**Valid — variables that back no flag**
```json
{
  "schema_version": "3.5",
  "framework_version": "2.4.0",
  "etag": "sha256:e7a412",
  "env_vars": [
    { "name": "TOOL_DEBUG", "description": "1 turns on debug output on stderr, with secrets redacted" },
    { "name": "TOOL_AUDIT_LOG", "description": "1 turns the audit log on, 0 turns it off, an absolute path turns it on at that path" },
    { "name": "TOOL_SESSION_ID", "description": "Agent session id recorded as session_id in each audit log entry" },
    { "name": "TOOL_TRACE_ID", "description": "Trace id propagated to meta.trace_id, logs, and child processes" }
  ],
  "flags": {
    "format": {
      "type": "enum",
      "required": false,
      "enum_values": ["json", "jsonl", "tsv", "plain"],
      "description": "Output representation; json when stdout is not a terminal, plain in a terminal",
      "env_vars": [{ "name": "TOOL_FORMAT" }]
    }
  },
  "commands": {
    "deploy": {
      "description": "Deploy a build to a project",
      "danger_level": "mutating",
      "required_scopes": ["deploy:write"],
      "secret_env_vars": ["TOOL_TOKEN"],
      "flags": {},
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
Every variable the tool reads has one home: `TOOL_FORMAT` backs `--format`, `TOOL_TOKEN` is a secret, and the four that back no flag sit in root `env_vars`, each described because no flag's `description` covers it.

**Valid — a tool's own format values with their media types**
```json
{
  "schema_version": "3.12",
  "framework_version": "2.6.0",
  "etag": "sha256:0b7e19",
  "flags": {
    "format": {
      "type": "enum",
      "required": false,
      "enum_values": ["json", "jsonl", "plain", "html"],
      "description": "Output representation; json when stdout is not a terminal, plain in a terminal",
      "media_types": { "html": "text/html" }
    }
  },
  "commands": {
    "report": {
      "description": "Summarize the ledger for a period",
      "danger_level": "safe",
      "required_scopes": [],
      "output_formats": ["toon", "csv"],
      "output_media_types": { "toon": "text/plain", "csv": "text/csv" },
      "flags": {},
      "exit_codes": {}
    }
  }
}
```
`--format html` writes a page a person reads, so an agent treats it as an opaque artifact; `json`, `jsonl`, and `plain` take the spec's media types without listing them. `report` adds two formats of its own and declares what each writes.

**Invalid — media types on a command-local flag**
```json
{
  "schema_version": "3.12",
  "framework_version": "2.6.0",
  "etag": "sha256:0b7e19",
  "commands": {
    "export": {
      "description": "Export the ledger",
      "danger_level": "safe",
      "required_scopes": [],
      "flags": {
        "style": { "type": "enum", "required": false, "enum_values": ["html", "pdf"], "description": "Rendering of the export", "media_types": { "html": "text/html", "pdf": "application/pdf" } }
      },
      "exit_codes": {}
    }
  }
}
```
Violation: only the root `format` flag carries `media_types`; a command-specific `--format` value declares its media type in the command's `output_media_types`.

**Valid — a tool-wide secret and a setting with an ecosystem name**
```json
{
  "schema_version": "3.13",
  "framework_version": "2.5.0",
  "etag": "sha256:0b93e2",
  "env_vars": [
    { "name": "TOOL_LEDGER", "description": "Path of the ledger file every command reads" },
    { "name": "LEDGER_FILE", "description": "Path of the ledger file, the ecosystem's established name; TOOL_LEDGER overrides it" }
  ],
  "secret_env_vars": ["TOOL_API_KEY"],
  "commands": {
    "login": {
      "description": "Store credentials for the price service",
      "danger_level": "mutating",
      "required_scopes": [],
      "headless_supported": false,
      "token_env_vars": ["TOOL_PRICE_TOKEN"],
      "flags": {},
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Credentials stored", "retryable": false, "side_effects": "complete" } }
    },
    "sync": {
      "description": "Sync prices into the ledger",
      "danger_level": "mutating",
      "required_scopes": [],
      "secret_env_vars": ["TOOL_PRICE_TOKEN"],
      "flags": {},
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Prices synced", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
Every command reads `TOOL_API_KEY`, so it sits once in root `secret_env_vars`. `login` accepts `TOOL_PRICE_TOKEN` as a pre-acquired token, so it names it in `token_env_vars` and not in its own `secret_env_vars`; `sync` reads the same token as a plain secret. `LEDGER_FILE` follows `TOOL_LEDGER`, which the tool reads first.

**Valid — commands whose `--output` is not a `--format` rendering**
```json
{
  "schema_version": "3.6",
  "framework_version": "2.4.0",
  "etag": "sha256:51c8e0",
  "commands": {
    "build": {
      "description": "Compile the project into a single executable written to --output",
      "danger_level": "mutating",
      "required_scopes": [],
      "output_file": "handler",
      "flags": {
        "output": { "type": "string", "required": true, "description": "Path of the compiled executable" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Executable written", "retryable": false, "side_effects": "complete" } }
    },
    "test": {
      "description": "Run the test suite, streaming the runner's own output",
      "danger_level": "safe",
      "required_scopes": [],
      "output_file": "envelope",
      "flags": {
        "output": { "type": "string", "required": false, "description": "Path that receives the final JSON envelope" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "All tests passed", "retryable": false, "side_effects": "none" } }
    }
  }
}
```
`tool build --output app` writes the executable the command describes; `--format` does not change it. `tool test --output result.json --format plain` streams the runner's output to stdout and writes the final envelope to `result.json` as JSON.

**Valid — object flag and project-relative output**
```json
{
  "schema_version": "3.7",
  "framework_version": "2.5.0",
  "etag": "sha256:7a03be",
  "commands": {
    "report": {
      "description": "Render a report for the matching orders into the project's reports directory",
      "danger_level": "mutating",
      "required_scopes": ["orders:read"],
      "output_file": "formatted",
      "output_file_base": "project_root",
      "flags": {
        "filter": {
          "type": "object",
          "required": false,
          "description": "Order filter as JSON text",
          "schema": {
            "type": "object",
            "properties": { "status": { "type": "string" }, "min_total": { "type": "number" } },
            "additionalProperties": false
          }
        },
        "line": {
          "type": "array",
          "required": false,
          "description": "Extra line item as JSON text; repeat for more",
          "schema": {
            "type": "object",
            "required": ["sku", "qty"],
            "properties": { "sku": { "type": "string" }, "qty": { "type": "integer", "minimum": 1 } }
          }
        },
        "output": { "type": "string", "required": true, "description": "Report path, relative to the project root" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Report written", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
`tool report --filter '{"status":"open"}' --output reports/open.json` writes `<project root>/reports/open.json` from any subdirectory. Each `--line` value is one JSON object matching `schema`.

**Invalid — object flag without its schema**
```json
{
  "schema_version": "3.7",
  "framework_version": "2.5.0",
  "etag": "sha256:7a03be",
  "commands": {
    "search": {
      "description": "Search orders",
      "danger_level": "safe",
      "required_scopes": [],
      "flags": {
        "filter": { "type": "object", "required": false, "description": "Order filter as JSON text" }
      },
      "exit_codes": {}
    }
  }
}
```
Violation: an `object` flag requires `schema`; without it an agent cannot build a value the command accepts.

**Valid — a producer piped into a records consumer**
```json
{
  "schema_version": "3.8",
  "framework_version": "2.4.0",
  "etag": "sha256:61c0de",
  "commands": {
    "import": {
      "description": "Import a JSON payload as one batch",
      "danger_level": "mutating",
      "required_scopes": ["data:write"],
      "stdin": { "mode": "buffered" },
      "flags": {
        "input-file": { "type": "string", "required": false, "description": "Read the payload from this path instead of stdin; - is stdin" }
      },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Batch imported", "retryable": false, "side_effects": "complete" } }
    },
    "tag": {
      "description": "Tag each security read from stdin, one record per line",
      "danger_level": "mutating",
      "required_scopes": ["data:write"],
      "stdin": {
        "mode": "records",
        "max_line_bytes": 65536,
        "record_schema": {
          "type": "object",
          "required": ["id", "symbol"],
          "properties": { "id": { "type": "string" }, "symbol": { "type": "string" } }
        }
      },
      "flags": {
        "input-file": { "type": "string", "required": false, "description": "Read the records from this path instead of stdin; - is stdin" }
      },
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "Every record tagged", "retryable": false, "side_effects": "complete" },
        "1": { "name": "GENERAL_ERROR", "description": "A line was too large, a record was invalid, or the upstream stream failed or ended early", "retryable": false, "side_effects": "partial" }
      }
    }
  }
}
```
`import` refuses more than 64 KiB on stdin; a bigger payload goes through `--input-file`. `tool list-securities --stream | tool tag` streams any number of records into `tag`, each line at most 64 KiB, and `tag` stops at the producer's `_summary` line.

**Invalid — records mode without a record schema**
```json
{
  "schema_version": "3.8",
  "framework_version": "2.4.0",
  "etag": "sha256:61c0de",
  "commands": {
    "tag": { "description": "Tag securities", "danger_level": "mutating", "required_scopes": [], "stdin": { "mode": "records" }, "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `records` mode requires `record_schema`; without it an agent cannot tell which producers fit, and a command that checks nothing per line is `lines` mode.

**Valid — passthrough command that wraps another tool's parser**
```json
{
  "schema_version": "3.9",
  "framework_version": "1.4.0",
  "etag": "sha256:c41d07",
  "commands": {
    "ingest": {
      "description": "Run beangulp on bank statements; every argument goes to beangulp",
      "danger_level": "mutating",
      "required_scopes": [],
      "arguments": "passthrough",
      "help_argv": ["extract", "--help"],
      "option_placement": "strict",
      "flags": {},
      "exit_codes": {
        "2":  { "name": "ARG_ERROR", "description": "A framework option before the command path is invalid; the tool did not start", "retryable": false, "side_effects": "none" },
        "10": { "name": "TIMEOUT", "description": "The delegated tool ran past the timeout; partial writes may have occurred", "retryable": false, "side_effects": "partial" }
      }
    }
  }
}
```
`ledger --format json ingest extract a.csv` hands `extract a.csv` to beangulp; beangulp writes stdout and chooses the exit code, and the envelope is the last line of stderr. `ledger ingest --help` runs beangulp with `extract --help`.

**Valid — safe command that writes its product to a declared `output` path**
```json
{
  "schema_version": "3.10",
  "framework_version": "2.5.0",
  "etag": "sha256:0d7e5a",
  "commands": {
    "dashboard.build": {
      "description": "Render the project dashboard to tmp/dashboard",
      "danger_level": "safe",
      "required_scopes": [],
      "filesystem_side_effects": [{ "path": "{project_root}/tmp/dashboard/", "type": "output" }],
      "flags": {},
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Dashboard rendered", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```
`tool status --show-side-effects` lists `tmp/dashboard/`; `tool cleanup` leaves it in place. Writing its own product does not make the command `mutating`.

**Invalid — `output` path with a TTL and a clear command**
```json
{
  "schema_version": "3.10",
  "framework_version": "2.5.0",
  "etag": "sha256:0d7e5a",
  "commands": {
    "dashboard.build": {
      "description": "Render the project dashboard",
      "danger_level": "safe",
      "required_scopes": [],
      "filesystem_side_effects": [{ "path": "{project_root}/tmp/dashboard/", "type": "output", "ttl_seconds": 3600, "clearable_with": "tool cleanup" }],
      "flags": {},
      "exit_codes": {}
    }
  }
}
```
Violation: an `output` path is the command's product; it does not expire and no clear command owns it. A path the framework may delete is `cache` or `temp`.

**Invalid — passthrough command with interspersed options**
```json
{
  "schema_version": "3.9",
  "framework_version": "1.4.0",
  "etag": "sha256:c41d07",
  "commands": {
    "ingest": { "description": "Run beangulp", "danger_level": "mutating", "required_scopes": [], "arguments": "passthrough", "option_placement": "any", "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `arguments: "passthrough"` requires `option_placement: "strict"`; every token after the command path belongs to the delegated tool, so no option can follow it.

**Valid — command that streams a wrapped program's log to stderr**
```json
{
  "schema_version": "3.11",
  "framework_version": "2.1.0",
  "etag": "sha256:5be0a3",
  "commands": {
    "provision": {
      "description": "Run the site playbook against the inventory; ansible-playbook's log streams to stderr",
      "danger_level": "mutating",
      "required_scopes": [],
      "stderr": "child_log",
      "flags": {
        "limit": { "type": "string", "required": false, "description": "Host pattern passed to ansible-playbook as --limit" }
      },
      "exit_codes": {}
    }
  }
}
```
`infra --format json provision` writes ansible-playbook's log to stderr, line by line, as it runs, even without a terminal; stdout holds only the final envelope. `infra --quiet provision` writes nothing to stderr.

**Invalid — child log on a passthrough command**
```json
{
  "schema_version": "3.11",
  "framework_version": "1.4.0",
  "etag": "sha256:c41d07",
  "commands": {
    "ingest": { "description": "Run beangulp", "danger_level": "mutating", "required_scopes": [], "arguments": "passthrough", "option_placement": "strict", "stderr": "child_log", "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `stderr: "child_log"` promises that stdout carries only the envelope, while a passthrough command gives stdout to the delegated tool and puts the envelope on the last line of stderr. A passthrough command's stderr already carries the delegated tool's own stderr ahead of that line.

**Valid — mutating command that previews unless `--yes` is given**
```json
{
  "schema_version": "3.14",
  "framework_version": "1.5.0",
  "etag": "sha256:5e9a12",
  "commands": {
    "migrate": {
      "description": "Apply pending schema migrations",
      "danger_level": "mutating",
      "required_scopes": [],
      "confirm_flag": "yes",
      "flags": {
        "yes": { "type": "boolean", "required": false, "default": false, "description": "Apply the migrations; omit to preview them" },
        "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Preview the migrations even when --yes is given" }
      },
      "exit_codes": {}
    }
  }
}
```
`db migrate` previews with `meta.dry_run: true`; `db migrate --yes` applies the migrations; `db migrate --dry-run --yes` previews.

**Invalid — confirm flag next to `safe_default`**
```json
{
  "schema_version": "3.14",
  "framework_version": "1.5.0",
  "etag": "sha256:5e9a12",
  "commands": {
    "rollback": { "description": "Roll back the last deployment", "danger_level": "destructive", "required_scopes": [], "safe_default": true, "confirm_flag": "yes", "flags": { "yes": { "type": "boolean", "required": false, "description": "Run the rollback" } }, "exit_codes": {} }
  }
}
```
Violation: `confirm_flag` excludes `safe_default: true`; a command has one confirmation mechanism, either the injected `--live` or its own flag.

**Valid — idempotent command whose partial failure is rerun**
```json
{
  "schema_version": "3.15",
  "framework_version": "0.9.0",
  "etag": "sha256:5be2a0",
  "commands": {
    "observe": {
      "description": "Rewrite one snapshot file per server from its live state",
      "danger_level": "mutating",
      "idempotent": true,
      "required_scopes": ["servers:read"],
      "has_network_io": true,
      "flags": {},
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "Every snapshot file is rewritten", "retryable": false, "side_effects": "complete" },
        "3": { "name": "PARTIAL_FAILURE", "description": "Some snapshot files are rewritten and others are not", "retryable": false, "side_effects": "partial" }
      }
    }
  }
}
```
Exit `3` stays `retryable: false` because files were written. `idempotent: true` tells the agent that rerunning `tool observe` unchanged converges on the state a clean run leaves, so the rerun is the recovery and no state inspection comes first.

**Invalid — command entry without required contract fields**
```json
{
  "schema_version": "3.0",
  "framework_version": "2.1.0",
  "etag": "sha256:a3f9c1",
  "commands": {
    "deploy": { "description": "Deploy a build", "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `danger_level` and `required_scopes` are required on every command; an agent cannot tell whether the call is safe.

**Invalid — editor command without alternatives**
```json
{
  "schema_version": "3.0",
  "framework_version": "2.1.0",
  "etag": "sha256:a3f9c1",
  "commands": {
    "commit": { "description": "Record a change", "danger_level": "mutating", "required_scopes": [], "requires_editor": true, "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `requires_editor: true` requires `non_interactive_alternatives`; otherwise the agent has no path that avoids the editor trap (§62).

**Invalid — root variable without a description**
```json
{
  "schema_version": "3.5",
  "framework_version": "2.4.0",
  "etag": "sha256:e7a412",
  "env_vars": [{ "name": "TOOL_DEBUG" }],
  "commands": {}
}
```
Violation: a root `env_vars` entry requires `description`; no flag's `description` explains what `TOOL_DEBUG` accepts or changes.

---

## Common mistakes

- **Emitting `commands` as an array.** The map keyed by dot path is what enables O(1) lookup; arrays force a scan and invite duplicate names
- **Listing a path in `subcommands` without a matching `commands` entry.** Every registered command, including children and built-ins, appears in the flat map
- **Adding ad-hoc fields to `CommandEntry`.** Entries are closed; a new contract field belongs in this schema with a sourcing requirement, not as an undocumented extension
- **Declaring a static `default` for a flag whose default depends on the environment.** `--format` resolves to `json` without a terminal and `plain` in one (REQ-F-003); omit `default` and state the rule in `description`, so an agent passes the value it needs
- **Setting `default: null` for flags without a default.** Omit the key; `null` reads as "the default value is null"
- **Declaring `retryable: true` with partial side effects in `exit_codes`.** The `ExitCodeEntry` invariant rejects it; timeouts that may have written are `retryable: false`
- **Declaring `retryable: true` on a partial exit because the command is idempotent.** `retryable: true` still promises that nothing was written; keep the exit `retryable: false`, `side_effects: "partial"`, and declare `idempotent: true` on the command
- **Declaring `idempotent: true` on a command that only deduplicates.** A command that skips a repeat by its `--idempotency-key` (REQ-C-007) but appends, increments, or sends on every new key does not converge; `idempotent` means the same arguments reach the same state with or without a key
- **Repeating global options in every `CommandEntry.flags`.** A global option appears once, in the root `flags`; a copy inside a command reads as a local flag that happens to share the name, and hides whether it is accepted before the command path
- **Reusing a global short alias for a local flag.** `-f` meaning `--format` at the root and `--force` on one command changes meaning with position; the framework rejects it at registration
- **Generating the manifest from a static file.** It must be computed from live registrations or the `etag` lies
- **Separating built-ins by a hard-coded name list.** Frameworks differ in which built-ins they register (`doctor`, `manifest`, `audit-log`, ...), and an application may replace one with its own command; read `builtin` instead
- **Marking an application command that replaces a built-in's name as `builtin: true`.** The flag follows who registered the command, not its name; the replacement is `false`
- **Marking every flag of an "exactly one of" group `required: true`.** No call can then satisfy the command; keep each flag `required: false` and declare the group as a `one_of` rule
- **Emitting pairwise `prohibited` rules next to a `one_of` group.** `one_of` already forbids combining its members; the extra rules repeat the constraint and let the two drift apart
- **Declaring `output_file: "formatted"` on a command that returns a binary result.** The file would then hold a JSON or plain wrapper around base64, not the file the caller asked for; a binary result is `"binary"`
- **Omitting `output_file` because the handler writes the file itself.** Absence tells the agent the command has no `--output`; declare `"handler"`
- **Declaring a command's product as `cache`.** `tool cleanup` then deletes the report the user asked for; declare it `output`, which `cleanup` never removes
- **Declaring an `output` side effect for the `--output` path.** The caller picks that path per call, and `output_file` already declares it; `type: "output"` is for a location the command chooses itself
- **Leaving `output_file_base` out when `--output` does not resolve against the working directory.** Absence means `cwd`, so the agent looks for the file in the wrong place; declare `project_root` or `resource`
- **Declaring a JSON-valued flag as `type: "string"`.** The agent then has no shape to build and no signal that the value is parsed as JSON; declare `type: "object"` with `schema`
- **Naming a flag's environment variables only in its `description`.** "(read from `$A` or `$B` when not passed)" is prose an agent must parse; list the names in `env_vars`, in precedence order
- **Listing a secret in `env_vars`.** A token or password is not a flag value (REQ-C-016); declare its variable in `secret_env_vars`
- **Declaring `stdin: {mode: "buffered"}` on a command that consumes a record stream.** The 64 KiB total cap then rejects any real pipeline; a command that handles one line at a time declares `lines` or `records`
- **Declaring `max_bytes` on a `lines` or `records` command.** Line mode has no total cap, so the field is rejected; the per-line cap is `max_line_bytes`
- **Marking a passthrough command only through `option_placement: "strict"` and its `description`.** `strict` also fits a command that parses its own options and forwards the rest; only `arguments: "passthrough"` tells an agent that stdout, the exit code, and every token after the path belong to another tool
- **Stating "previews unless `--yes`" only in a flag's `description`.** An agent that reads the manifest then expects a bare call to run; declare `confirm_flag` so the preview default is machine-readable
- **Declaring `confirm_flag` with a name the command does not accept.** The name must be a boolean flag in the command's `flags` or the root `flags`; the framework refuses any other at registration
- **Declaring `help_argv` on a declared command.** The framework answers `--help` itself there; `help_argv` exists only where a lone `--help` would otherwise reach the delegated tool
- **Saying only in `description` that a command streams a wrapped program's log.** An agent cannot match prose before the call; declare `stderr: "child_log"` so it knows stderr will be busy and carries no failure signal
- **Letting auto-quiet or `--verbose` gate a declared child log.** `child_log` streams whatever the verbosity; only `--quiet` silences it, so a log that appears only under `--verbose` is a framework diagnostic, not a child log
- **Listing a borrowed name before the tool-prefixed one.** `CLOUDFALL_PROJECT` ahead of `TOOL_PROJECT` lets a variable set for another tool override the one set for this tool (REQ-F-073)
- **Reading a variable the manifest never names.** `TOOL_DEBUG` or `TOOL_AUDIT_LOG` backs no flag, so it belongs in root `env_vars`; documenting it only in a README leaves an agent unable to see that it changes the tool's behavior
- **Listing one variable in two places.** A name in root `env_vars` appears nowhere else in the manifest; a variable that supplies a flag's value is declared on that flag only; a root secret appears in no command's `secret_env_vars`; an auth command's token sits in its `token_env_vars`, not also in its `secret_env_vars`
- **Repeating a tool-wide secret on every command.** A secret every command reads goes in root `secret_env_vars` once
- **Listing a secret in root `env_vars`.** A root `description` invites a default or an example value; a secret goes in a `secret_env_vars`, which holds names only
- **Listing an ecosystem name in root `env_vars` alone.** `LEDGER_FILE` without `TOOL_LEDGER` right before it lets a variable set for another tool configure this one; the prefixed name comes first and wins (REQ-F-073)
- **Naming a format's media type only in the `--format` `description`.** "html writes text/html" is prose an agent must parse; declare it in the root `format` flag's `media_types`
- **Leaving a tool's own format value out of `media_types`.** An agent can then assume nothing about it and must treat its output as opaque; every value outside the spec's table has an entry
- **Mapping a spec value to another media type.** `json` is always `application/json`; a variant with another shape is a new format value with its own name
- **Listing universal names in root `env_vars`.** `NO_COLOR`, `CI`, `HOME`, `COLUMNS`, the proxy and CA bundle names, and the other REQ-F-073 exceptions are read by every conforming tool; listing them adds noise without telling the agent anything

---

## Agent interpretation

Rules for agents consuming `ManifestResponse` to plan and execute command calls.

**Fetching the manifest**
- Read `schema_version` first. A `3.x` manifest lists global options once in root `flags`; treat any other value as pre-3.0, where global options may repeat inside each `CommandEntry.flags` and root `flags` is absent. Pre-3.0 producers commonly emit `1.0`, the value every 2.x example showed, so never test for a `2.` prefix
- Fetch once per session, not per call — the manifest is expensive to generate and stable between command registrations
- Cache using `etag`: on subsequent fetches pass the previous etag; if `meta.not_modified: true`, reuse the cached manifest
- If `tool manifest` itself is unavailable (exit code `5` or `12`) — fall back to per-command `--help` calls; this is O(N) but safe

**Looking up a command**
- Key format is dot-separated (e.g. `"deploy.rollback"`); split the user-intended subcommand path on spaces and join with `.` to construct the key
- If the key is not in `commands` — do not guess; emit `REDIRECTED` behavior: try `tool manifest` again in case it was stale, then escalate
- Check `aliases` before concluding a command does not exist — the agent may be using an alias that maps to a different primary key

**Separating application commands from built-ins**
- When building a task list, a skill set, or a summary of what the tool does, drop entries with `builtin: true`; they are framework plumbing (`manifest`, `doctor`, `audit-log`) present in every conforming CLI
- Treat an absent `builtin` as `false`. A pre-3.1 manifest never sets it, so every command there reads as an application command
- Keep built-ins in the lookup table: they are still callable, and `doctor` or `audit-log` is the right call when diagnosing a failure

**Writing a result to a file**
- `output_file: "binary"`: pass `--output <path>` to get the file itself; `--format` then shapes only the envelope on stdout. Verify the write with `data.sha256` or `data.bytes` instead of reading the file back. Never pass `--output -`; it exits `2`
- `output_file: "formatted"`: the file holds the `--format` representation of `data`, so choose `--format` for the file's consumer
- `output_file: "handler"`: the command's handler writes the file; read the command's `description` for what it holds, and do not expect `--format` to change it
- `output_file: "envelope"`: the file holds the final `ResponseEnvelope` as JSON whatever `--format` says; read `ok`, `data`, and `error` from the file, not from stdout
- `output_file_base` other than `cwd`: a relative `--output` lands under the project root (`project_root`) or the target resource's directory (`resource`), not the working directory. Pass an absolute path when the file must land in a known place; it is used as given
- `output_file` absent: the command takes no `--output`; a binary result arrives base64-encoded in `data` (REQ-F-017). Treat a pre-3.3 manifest the same way and read `output_schema` for a binary wrapper

**Feeding stdin from `stdin`**
- `mode: "buffered"`: pipe at most `max_bytes` (absent means `65536`); write anything bigger to a file and pass `--input-file <path>`, or the call exits `2` with `STDIN_TOO_LARGE`
- `mode: "lines"` or `"records"`: pipe a stream of any length, each line at most `max_line_bytes` (absent means `1048576`); a longer line exits `1` with `LINE_TOO_LARGE` and `context.line`. When you write stdin and read stdout from the same thread, write the input to a file and pass `--input-file` instead; only a separate writer, such as the producer in a shell pipeline, keeps both pipes draining
- `mode: "records"`: before piping a producer into the command, check the producer's item type against `record_schema`. Feed it a REQ-O-004 stream that ends with a `_summary` line; a stream without one exits `1` with `UPSTREAM_INCOMPLETE`, and an upstream error line exits `1` with `UPSTREAM_FAILED`
- `stdin` absent on a `3.8` or later manifest: the command reads no stdin payload. On a pre-3.8 manifest, absent means unknown; treat a command that accepts `--input-file` as buffered with the 65536-byte cap

**Building a call from `FlagEntry`**
- A command's accepted flags are the root `flags` plus its own `flags`; a name in neither produces `ARG_ERROR (2)`
- Emit tokens in the canonical order `tool <global options> <command path> <local options> [--] <positionals>`; every parser mode and both `option_placement` values accept it
- Give `positionals` in array order; a `required` entry must be present, and only a `variadic` last entry takes more than one value
- Put `--` before any positional that starts with `-`
- Pass each option once; a scalar option repeated with a different value produces `ARG_ERROR (2)`
- `required: true` flags must always be present; absence will produce `ARG_ERROR (2)`
- `type: "enum"` — only values in `enum_values` are accepted; sending any other value produces `ARG_ERROR (2)`
- `type: "object"`: pass one argv token of compact JSON text that validates against `schema` (`--filter '{"status":"open"}'`); text that is not a JSON object, or does not match, produces `ARG_ERROR (2)`. An `array` flag with `schema` takes each item as such a token
- `default` absent — the flag is optional but has no fallback; omitting it changes behavior; include explicitly if the outcome matters
- `short` present — both `--flag-name value` and `-f value` are valid; prefer long form for clarity in agent-constructed calls

**Supplying a flag through the environment from `env_vars`**
- A passed flag beats every variable; pass the flag when the value matters for this call alone
- To set a value for the whole session, export the first name whose `deprecated` is absent or `false`; never export a deprecated name
- A name earlier in the list overrides the one you export, since the first one set wins; check that every earlier name is unset
- `env_vars` absent on a `3.4` or later manifest: the flag reads no environment variable. On a pre-3.4 manifest, absent means unknown, not none; read the flag's `description` and keep that environment clean of guesses
- A required flag with `env_vars` still counts as present when one of its variables is set

**Reading root `env_vars`**
- Root `env_vars` lists the variables that change the tool's behavior without backing a flag; read each `description` before exporting one, and unset any you did not set on purpose, since a leftover `TOOL_DEBUG` or `TOOL_AUDIT_LOG` changes every call
- Root `env_vars` absent on a `3.5` or later manifest: the tool reads no such variable. On a pre-3.5 manifest, absent means unknown, not none
- An entry without the tool prefix, such as `LEDGER_FILE`, follows the prefixed entry for the same setting; set the prefixed one, since it wins, and unset the other if you inherited it

**Supplying secrets**
- A command's secrets are the root `secret_env_vars` plus its own `secret_env_vars`; an auth command also accepts the names in its `token_env_vars`. Export the value from your secret store; never pass it on the command line
- Root `secret_env_vars` absent on a `3.13` or later manifest: no secret is read by every command. On a pre-3.13 manifest, absent means unknown; a tool-wide secret may appear only in a README or in each command's `secret_env_vars`

**Selecting output format from `output_formats`**
- If `output_formats` is absent, treat `json` as the only guaranteed format — do not attempt non-standard values
- Look up a value's media type in the command's `output_media_types`, then the root `format` flag's `media_types`, then the spec's table in REQ-O-001 (`json` → `application/json`, `jsonl` → `application/x-ndjson`, and `tsv`, `plain`, `table`, `id` as text)
- Parse output as JSON only when its media type is `application/json`, `application/x-ndjson` (one value per line), or ends in `+json`; treat any other format's output, such as `text/html`, as an opaque artifact to store or hand to a person
- A value with no media type from any of the three sources (always the case for a non-spec value on a pre-3.12 manifest) is opaque too
- If `output_formats` is present, select the most appropriate format for your consumer: `json` for programmatic parsing, an LLM-optimized value (e.g. `toon`) when the language model is the final reader and token cost matters
- Never assume a format value is valid unless it appears in `output_formats` or is one of the framework defaults

**Pre-planning retries from `exit_codes`**
- Before the first call, read the command's `exit_codes` map and identify which codes are retryable
- Build the retry/rollback plan before calling, not reactively — this avoids ambiguity about whether a retry is safe after a partial failure
- `idempotent: true` — a non-retryable exit whose entry declares `side_effects: "partial"` (such as `PARTIAL_FAILURE (3)`, a `TIMEOUT (10)` that may have written, or `130`/`143` after a signal) is recovered by rerunning the identical command once, without inspecting state. A second failure with the same `error.code` is deterministic: stop and escalate
- The rerun rule never covers `ARG_ERROR (2)` or any error carrying `fix_required` or `fix_command`: the identical call fails until the input changes, so apply the fix first. Exits with `side_effects: "none"` follow `retryable` as usual
- An absent `idempotent` means `false`, including on a pre-3.15 manifest: verify what was committed before rerunning a mutating command

**Reading declared contracts before calling**
- `danger_level` other than `safe` — prefer `--dry-run` first; `safe_default: true` means the command previews until `--live` is passed
- `filesystem_side_effects` with `type: "output"` — the command writes its product there, even when it is `safe`; read the result from that path, and do not run `tool cleanup` expecting it to go. A pre-3.10 manifest cannot mark it and may declare it `cache`
- `confirm_flag` present: a call without `--<confirm_flag>` only previews and exits `0` with `meta.dry_run: true`. Read the `would_*` preview, then repeat the call with the flag to run it; check `meta.dry_run` rather than the exit code to know whether it ran. `--dry-run` wins, so drop it from the confirmed call. On a pre-3.14 manifest an absent `confirm_flag` means unknown; read the flag descriptions
- `option_placement: "strict"` — place every option, global or local, before the first positional argument; anything after it is forwarded to the child process
- `requires` — evaluate each rule against the flags you plan to send before calling; a violated rule produces `ARG_ERROR (2)`
- `any_of` and `one_of` groups — send at least one flag of an `any_of` group and exactly one flag of a `one_of` group, choosing the one whose value you already hold; a declared `default` never satisfies either rule, and neither does a boolean flag given as false (`--no-exact` leaves `exact` absent)
- `interactive: true` or `requires_editor: true` — always pass `--yes` / `--non-interactive` or one of `non_interactive_alternatives`
- `async: true` — the response is a job descriptor; poll with its `status_command` instead of waiting on the call
- `required_scopes` not covered by the active credential — expect `AUTH_REQUIRED (8)`; do not call until credentials change

**Calling a passthrough command (`arguments: "passthrough"`)**
- Put every global option and framework flag (`--format`, `--output`, `--timeout`) before the command path; every token after it goes to the delegated tool, `--help` and `--` included
- Read stdout as the delegated tool's output, not as an envelope. The envelope is the last line of stderr; when that line is not an envelope, the framework rejected its own options before the tool started and the envelope is on stdout
- Classify by `error.code`: `DELEGATED_EXIT` means the tool chose the exit code, and `data.exit_code` repeats it. A delegated `2` is the tool's usage error and does not rule out side effects; decide from `retryable`, which is `false`, not from the code
- For the tool's own help, call `tool <cmd> --help`; the framework forwards `help_argv` when the command declares it
- An absent `arguments` means `declared`, including on a pre-3.9 manifest; such a manifest cannot mark a passthrough command, so treat a `strict` command whose `description` says its arguments go to another tool as one

**Reading stderr from `stderr`**
- `stderr: "child_log"`: expect a wrapped program's log on stderr, as plain text, whatever `--format` and verbosity say. Discard it or keep only its tail for a person; pass `--quiet` to silence it when no one will read it
- Never treat stderr text from such a command as a failure signal, even when it contains words like `ERROR` or `failed`; the exit code and the envelope on stdout stay authoritative
- `stderr` absent: stderr carries only the framework's own diagnostics (REQ-F-006, REQ-F-038). On a pre-3.11 manifest absent means unknown; a command whose `description` says it streams another program's log may still do so

**Manifest staleness**
- If a command call returns `REDIRECTED (13)` for a path that exists in the manifest — the manifest is stale; re-fetch unconditionally and update the cache
- If a call returns `ARG_ERROR (2)` for a flag shown as valid in the manifest — possible version skew; re-fetch manifest before retrying

## Coding agent notes

**Generation strategy**
- Generate the manifest by reflecting over registered commands at startup — do not generate it by hand or from a separate config file
- The `etag` must be a deterministic hash of the serialized command registrations — generate it as `sha256(canonical_json(commands))` where canonical JSON sorts keys

**Type representation**
- Generate `ManifestResponse` as a read-only snapshot type — it reflects the registration state at the moment `enable_manifest()` is called and does not update dynamically
- `commands` keys must be dot-separated strings matching the command's full invocation path — generate the key from the command's registration name, not from its handler function name

**Validation to generate**
- Assert every command in the registry appears in `commands` — missing commands are a silent discovery failure
- Assert every command's effective `exit_codes` table (root table overlaid with the entry's own map) matches its `ExitCodeEntry` declarations exactly — no additions, no omissions
- Assert an entry's own `exit_codes` map never repeats a root-table entry unchanged
- Assert no `CommandEntry.flags` key or `short` value equals a root `flags` key or `short` value
- Assert `positionals` lists every positional the parser accepts, in order, with no required entry after an optional one and `variadic` only on the last
- Assert every command the framework registers, and each of its subcommands, carries `builtin: true`, and no application command does
- Assert `output_file` is present on exactly the commands that register `--output <path>`, and is `"binary"` exactly when the command's result is a binary value, `"handler"` exactly when the handler writes the file, and `"envelope"` exactly when the framework writes the final envelope to it
- Assert `output_file_base` appears only with `output_file`, and that a relative `--output` path lands under the declared base from a working directory other than that base
- Assert every `type: "object"` flag carries a `schema` the parser enforces, and prefer `type: "object"` for every flag whose value the parser reads as a JSON object
- Assert every `arguments: "passthrough"` command has `option_placement: "strict"`, empty `flags`, no `positionals`, and a `danger_level` other than `destructive`, and that `help_argv` appears only on such commands
- Assert every `confirm_flag` names a boolean flag in the command's `flags` or the root `flags`, appears only on `mutating` or `destructive` commands without `safe_default: true` or `arguments: "passthrough"`, and that a call without it previews with `meta.dry_run: true` while `--dry-run` plus the flag still previews
- Assert `idempotent: true` only on commands whose tests show that a rerun after each declared partial exit leaves the state a clean run leaves; accept it on a `safe` command without warning
- Assert every flag's `env_vars` lists exactly the variables its parser reads, in the order it reads them, with the tool-prefixed name first whenever a name without the prefix is listed, and no name from `secret_env_vars`
- Assert root `env_vars` lists every other variable the tool reads outside the universal exceptions, each with a `description` and either the tool prefix or a declared name that immediately follows its setting's prefixed entry, and no name that also appears in a flag's `env_vars`, a `secret_env_vars`, or a `token_env_vars`
- Assert root `secret_env_vars` lists exactly the secrets every command reads, and that none of them repeats in a command's `secret_env_vars` or a flag's `env_vars`; assert no name in an auth command's `token_env_vars` repeats in that command's `secret_env_vars`
- Assert `stderr: "child_log"` appears on exactly the commands that stream a wrapped program's output to stderr, never on a passthrough command, and that `--quiet` leaves stderr empty for them
- Assert the root `format` flag's `media_types` keys are all in its `enum_values`, cover every value outside the spec's media type table, and map each spec value they list to the table's media type; assert no other flag carries `media_types`
- Assert every `output_formats` value covered by neither the spec's table nor the root `media_types` has an `output_media_types` entry, and every `output_media_types` key is a value the command accepts
- Assert `stdin` is present on exactly the commands that declare stdin input, with the `mode` the handler reads in, `record_schema` equal to the registered record type, and no `max_bytes` outside `buffered` mode
- Assert `etag` changes when any command registration changes, and is stable across identical registrations (determinism test)

**Tests to generate**
- A test that `tool manifest` returns all registered commands including built-ins
- A test that `tool manifest --etag <current>` returns `meta.not_modified: true` and `data: null`
- A test that adding a new command changes the `etag`
- A test that an agent can construct a valid call to every command using only the manifest — no `--help` calls

**Anti-patterns**
- Do not generate `exit_codes` in the manifest independently of `ExitCodeEntry` declarations — they must be the same source
- Do not generate the manifest as a static file checked into the repo — it must be computed from live registrations
- Do not use function names or file paths as command keys — use the registered command name

## Implementation notes

- `commands` is a flat map, not a tree. Use `subcommands` arrays for hierarchy — O(1) lookup without recursion
- `etag` must be computed from registrations (names, flags, exit codes, descriptions), not runtime state. Same registrations → same etag
- `exit_codes` keys are strings (`"0"`, `"2"`) because JSON object keys are always strings
- `FlagEntry.default` must be omitted (not `null`) when no default exists, to distinguish "optional without fallback" from "default is null"
- `output_formats` must list only values the command actually accepts; do not list formats that resolve to an error
- `FlagEntry.schema` is a plain draft-07 schema, so a generated MCP `inputSchema` uses it as the property's schema for an `object` flag and as `items` for an `array` flag; the CLI side still takes JSON text on argv

## Related

| Document | Relationship |
|---|---|
| [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) | Consumes: the command that returns this schema |
| [REQ-O-049](../requirements/o-049-llm-token-budget-flags.md) | Sources: `output_formats` and `output_media_types`: command-specific formats and what each writes |
| [REQ-O-001](../requirements/o-001-output-format-flag.md) | Sources: the root `format` flag's `media_types` and the spec's media type table |
| [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) | Sources: `exit_codes` per command |
| [REQ-C-015](../requirements/c-015-commands-declare-input-and-output-schema.md) | Sources: `flags` and `positionals` per command |
| [REQ-C-002](../requirements/c-002-command-declares-danger-level.md) | Sources: `danger_level` and `idempotent` per command |
| [REQ-C-029](../requirements/c-029-command-declares-required-scopes.md) | Sources: `required_scopes` per command |
| [REQ-F-079](../requirements/f-079-global-option-scope.md) | Sources: top-level `flags` (global options) |
| [REQ-F-073](../requirements/f-073-env-var-namespace-prefix.md) | Sources: `FlagEntry.env_vars`, root `env_vars`, root `secret_env_vars`, the four homes of a variable, and the precedence rule for names without the tool prefix |
| [REQ-F-051](../requirements/f-051-debug-and-trace-mode-secret-redaction.md) | Sources: `TOOL_DEBUG` listed in root `env_vars` when no flag backs it |
| [REQ-O-030](../requirements/o-030-opt-in-audit-log.md) | Sources: `TOOL_AUDIT_LOG` and the session variable listed in root `env_vars` |
| [REQ-O-042](../requirements/o-042-output-format-env-var-default.md) | Sources: `TOOL_FORMAT` listed in the root `format` flag's `env_vars` |
| [REQ-C-027](../requirements/c-027-commands-declare-option-placement.md) | Sources: `option_placement` per command |
| [REQ-F-054](../requirements/f-054-stdin-payload-size-cap-with-input-file-fallback.md) | Sources: `stdin` mode and the `max_bytes` and `max_line_bytes` caps |
| [REQ-O-004](../requirements/o-004-output-jsonl-stream-flag.md) | Sources: `streaming_default`, and the `records` mode a stream consumer reads in with its `record_schema` |
| [REQ-C-026](../requirements/c-026-commands-declare-conditional-argument-dependencies.md) | Sources: `requires` conditional rules |
| [REQ-C-031](../requirements/c-031-passthrough-commands-delegate-to-another-parser.md) | Sources: `arguments` and `help_argv` per command |
| [REQ-F-038](../requirements/f-038-verbosity-auto-quiet-in-non-tty-context.md) | Sources: `stderr` per command, the child log that auto-quiet leaves alone |
| [REQ-O-048](../requirements/o-048-destructive-commands-default-dry-run.md) | Sources: `safe_default` and `confirm_flag` per command |
| [REQ-O-031](../requirements/o-031-dependency-version-matrix-declaration.md) | Sources: top-level `dependencies` |
| [schemas/exit-code-entry.md](exit-code-entry.md) | Provides: `ExitCodeEntry` type used in `exit_codes` map |
| [schemas/response-envelope.md](response-envelope.md) | Wraps: manifest is returned as the `data` field of a `ResponseEnvelope` |
