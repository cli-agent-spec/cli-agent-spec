# Schema: ManifestResponse

**File:** [`manifest-response.json`](manifest-response.json)

> **Used by:** [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) · [REQ-O-013](../requirements/o-013-schema-output-schema-flag.md) · [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) · [REQ-C-002](../requirements/c-002-command-declares-danger-level.md) · [REQ-C-005](../requirements/c-005-interactive-commands-must-support-yes-non-interact.md) · [REQ-C-008](../requirements/c-008-multi-step-commands-emit-step-manifest.md) · [REQ-C-010](../requirements/c-010-background-process-commands-declare-metadata.md) · [REQ-C-011](../requirements/c-011-commands-declare-filesystem-side-effects.md) · [REQ-C-012](../requirements/c-012-commands-with-network-i-o-support-timeout.md) · [REQ-C-015](../requirements/c-015-commands-declare-input-and-output-schema.md) · [REQ-C-016](../requirements/c-016-secrets-accepted-only-via-env-var-or-file.md) · [REQ-C-018](../requirements/c-018-commands-declare-platform-requirements.md) · [REQ-C-019](../requirements/c-019-subprocess-invoking-commands-declare-argument-sche.md) · [REQ-C-020](../requirements/c-020-resource-id-fields-declare-validation-pattern.md) · [REQ-C-021](../requirements/c-021-auth-commands-declare-headless-mode-support.md) · [REQ-C-022](../requirements/c-022-async-commands-declare-job-descriptor-schema.md) · [REQ-C-023](../requirements/c-023-editor-requiring-commands-declare-non-interactive-.md) · [REQ-C-024](../requirements/c-024-gui-launching-commands-declare-headless-behavior.md) · [REQ-C-025](../requirements/c-025-config-writing-commands-declare-write-scope.md) · [REQ-C-026](../requirements/c-026-commands-declare-conditional-argument-dependencies.md) · [REQ-C-027](../requirements/c-027-commands-declare-option-placement.md) · [REQ-C-029](../requirements/c-029-command-declares-required-scopes.md) · [REQ-O-004](../requirements/o-004-output-jsonl-stream-flag.md) · [REQ-O-031](../requirements/o-031-dependency-version-matrix-declaration.md) · [REQ-O-048](../requirements/o-048-destructive-commands-default-dry-run.md) · [REQ-O-049](../requirements/o-049-llm-token-budget-flags.md)
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
| `schema_version` | string `MAJOR.MINOR` | yes | Version of this schema |
| `framework_version` | string | yes | Version of the tool binary |
| `etag` | string | yes | Deterministic content hash. Changes only when registrations change |
| `commands` | `Record<string, CommandEntry>` | yes | Flat map keyed by dot-separated path such as `"deploy.rollback"` |
| `dependencies` | `DependencyEntry[]` | no | External runtime dependencies checked by `tool doctor` (REQ-O-031) |

### CommandEntry — core

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | One-sentence summary |
| `danger_level` | `"safe"` \| `"mutating"` \| `"destructive"` | yes | Mutation risk level (REQ-C-002) |
| `required_scopes` | string[] | yes | Minimal permission strings, most critical first; empty when no auth is needed (REQ-C-029) |
| `flags` | `Record<string, FlagEntry>` | yes | Keyed by flag name without `--` |
| `exit_codes` | `Record<string, ExitCodeEntry>` | yes | Keyed by integer code as string (REQ-C-001). With a root `exit_codes` table present, holds only the command's additions and overrides; the effective table is root overlaid with this map, and `tool <cmd> --schema` prints it in full |
| `aliases` | string[] | no | Alternative invocation names |
| `output_schema` | object | no | JSON Schema for `data` on success (REQ-C-015) |
| `output_formats` | string[] | no | Formats beyond the framework defaults (REQ-O-049) |
| `examples` | `Example[]` | no | Verbatim invocations |
| `subcommands` | string[] | no | Dot-separated paths of direct children |

### CommandEntry — declared contracts

Present only when the command declares them.

| Field | Type | Description |
|-------|------|-------------|
| `option_placement` | `"any"` \| `"strict"` | `strict`: all options precede positionals; absent means `any` (REQ-C-027) |
| `interactive` | boolean | Command may prompt in a TTY; `--yes` and `--non-interactive` exist (REQ-C-005) |
| `has_network_io` | boolean | Command performs network or long blocking I/O; `--timeout` exists (REQ-C-012) |
| `steps` | string[] | Ordered step names of a multi-step command (REQ-C-008) |
| `spawns_background_process` | boolean | Command starts a child that outlives it (REQ-C-010) |
| `cleanup_command` | string | Exact command that stops that child (REQ-C-010) |
| `max_lifetime_seconds` | integer | Upper bound on the child's lifetime (REQ-C-010) |
| `filesystem_side_effects` | `FilesystemSideEffect[]` | Paths the command may write, with category and TTL (REQ-C-011) |
| `secret_env_vars` | string[] | Environment variables that supply secrets (REQ-C-016) |
| `platform` | string[] | Supported OS names; absent means all (REQ-C-018) |
| `required_tools` | `Record<string, string>` | External binaries and minimum versions (REQ-C-018) |
| `subprocess` | `SubprocessDeclaration` | Child binary and which flags reach its argv (REQ-C-019) |
| `headless_supported` | boolean | Auth command works without a TTY (REQ-C-021) |
| `token_env_vars` | string[] | Pre-acquired token variables; required when `headless_supported` is `false` (REQ-C-021) |
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

### FlagEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"string"` \| `"integer"` \| `"number"` \| `"boolean"` \| `"array"` \| `"enum"` | yes | Value type |
| `required` | boolean | yes | Flag must be present |
| `description` | string | yes | What the flag controls, including range or format |
| `default` | any | no | Omit (do not set `null`) when no default exists |
| `enum_values` | string[] | no | Only when `type` is `"enum"` |
| `short` | string (1 char) | no | Single-character shorthand |
| `pattern` | string | no | Anchored regex the value must match; exclusive with `pattern_type` (REQ-C-020) |
| `pattern_type` | `"alphanumeric_id"` \| `"uuid"` \| `"semver"` \| `"filepath"` \| `"url"` | no | Built-in validation preset (REQ-C-020) |

### Supporting types

| Type | Fields |
|------|--------|
| `Example` | `description`, `command` (both required) |
| `FilesystemSideEffect` | `path`, `type` (`cache` \| `log` \| `temp` \| `credential` \| `config`) required; `ttl_seconds`, `clearable_with` optional |
| `SubprocessDeclaration` | `binary` required; `user_controlled_args`, `hardcoded_args` optional |
| `ConditionalRule` | One of `{ if_flag, if_value, then_required }`, `{ if_flag, prohibited }`, `{ if_flag, target_flag, default }` |
| `DependencyEntry` | `name`, `check_command`, `min_version` required; `version_regex`, `fix_command` optional |

---

## Examples

**Valid — two commands with declared contracts**
```json
{
  "schema_version": "1.0",
  "framework_version": "2.1.0",
  "etag": "sha256:a3f9c1",
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
      "flags": { "target": { "type": "string", "required": true, "description": "Target environment" } },
      "exit_codes": { "0": { "name": "SUCCESS", "description": "Rollback completed or previewed", "retryable": false, "side_effects": "complete" } }
    }
  }
}
```

**Invalid — command entry without required contract fields**
```json
{
  "schema_version": "1.0",
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
  "schema_version": "1.0",
  "framework_version": "2.1.0",
  "etag": "sha256:a3f9c1",
  "commands": {
    "commit": { "description": "Record a change", "danger_level": "mutating", "required_scopes": [], "requires_editor": true, "flags": {}, "exit_codes": {} }
  }
}
```
Violation: `requires_editor: true` requires `non_interactive_alternatives`; otherwise the agent has no path that avoids the editor trap (§62).

---

## Common mistakes

- **Emitting `commands` as an array.** The map keyed by dot path is what enables O(1) lookup; arrays force a scan and invite duplicate names
- **Listing a path in `subcommands` without a matching `commands` entry.** Every registered command, including children and built-ins, appears in the flat map
- **Adding ad-hoc fields to `CommandEntry`.** Entries are closed; a new contract field belongs in this schema with a sourcing requirement, not as an undocumented extension
- **Setting `default: null` for flags without a default.** Omit the key; `null` reads as "the default value is null"
- **Declaring `retryable: true` with partial side effects in `exit_codes`.** The `ExitCodeEntry` invariant rejects it; timeouts that may have written are `retryable: false`
- **Generating the manifest from a static file.** It must be computed from live registrations or the `etag` lies

---

## Agent interpretation

Rules for agents consuming `ManifestResponse` to plan and execute command calls.

**Fetching the manifest**
- Fetch once per session, not per call — the manifest is expensive to generate and stable between command registrations
- Cache using `etag`: on subsequent fetches pass the previous etag; if `meta.not_modified: true`, reuse the cached manifest
- If `tool manifest` itself is unavailable (exit code `5` or `12`) — fall back to per-command `--help` calls; this is O(N) but safe

**Looking up a command**
- Key format is dot-separated (e.g. `"deploy.rollback"`); split the user-intended subcommand path on spaces and join with `.` to construct the key
- If the key is not in `commands` — do not guess; emit `REDIRECTED` behavior: try `tool manifest` again in case it was stale, then escalate
- Check `aliases` before concluding a command does not exist — the agent may be using an alias that maps to a different primary key

**Building a call from `FlagEntry`**
- `required: true` flags must always be present; absence will produce `ARG_ERROR (2)`
- `type: "enum"` — only values in `enum_values` are accepted; sending any other value produces `ARG_ERROR (2)`
- `default` absent — the flag is optional but has no fallback; omitting it changes behavior; include explicitly if the outcome matters
- `short` present — both `--flag-name value` and `-f value` are valid; prefer long form for clarity in agent-constructed calls

**Selecting output format from `output_formats`**
- If `output_formats` is absent, treat `json` as the only guaranteed format — do not attempt non-standard values
- If `output_formats` is present, select the most appropriate format for your consumer: `json` for programmatic parsing, an LLM-optimized value (e.g. `toon`) when the language model is the final reader and token cost matters
- Never assume a format value is valid unless it appears in `output_formats` or is one of the framework defaults

**Pre-planning retries from `exit_codes`**
- Before the first call, read the command's `exit_codes` map and identify which codes are retryable
- Build the retry/rollback plan before calling, not reactively — this avoids ambiguity about whether a retry is safe after a partial failure

**Reading declared contracts before calling**
- `danger_level` other than `safe` — prefer `--dry-run` first; `safe_default: true` means the command previews until `--live` is passed
- `option_placement: "strict"` — place every option before the first positional argument
- `requires` — evaluate each rule against the flags you plan to send before calling; a violated rule produces `ARG_ERROR (2)`
- `interactive: true` or `requires_editor: true` — always pass `--yes` / `--non-interactive` or one of `non_interactive_alternatives`
- `async: true` — the response is a job descriptor; poll with its `status_command` instead of waiting on the call
- `required_scopes` not covered by the active credential — expect `AUTH_REQUIRED (8)`; do not call until credentials change

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

## Related

| Document | Relationship |
|---|---|
| [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) | Consumes: the command that returns this schema |
| [REQ-O-049](../requirements/o-049-llm-token-budget-flags.md) | Sources: `output_formats` field — LLM-optimized formats are declared here |
| [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) | Sources: `exit_codes` per command |
| [REQ-C-002](../requirements/c-002-command-declares-danger-level.md) | Sources: `danger_level` per command |
| [REQ-C-029](../requirements/c-029-command-declares-required-scopes.md) | Sources: `required_scopes` per command |
| [REQ-C-027](../requirements/c-027-commands-declare-option-placement.md) | Sources: `option_placement` per command |
| [REQ-C-026](../requirements/c-026-commands-declare-conditional-argument-dependencies.md) | Sources: `requires` conditional rules |
| [REQ-O-031](../requirements/o-031-dependency-version-matrix-declaration.md) | Sources: top-level `dependencies` |
| [schemas/exit-code-entry.md](exit-code-entry.md) | Provides: `ExitCodeEntry` type used in `exit_codes` map |
| [schemas/response-envelope.md](response-envelope.md) | Wraps: manifest is returned as the `data` field of a `ResponseEnvelope` |
