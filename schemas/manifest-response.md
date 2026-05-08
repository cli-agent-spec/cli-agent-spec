# Schema: ManifestResponse

**File:** [`manifest-response.json`](manifest-response.json)

> **Used by:** [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md)
> Returned as the `data` field of a [`ResponseEnvelope`](response-envelope.md).

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Version of this schema (e.g. `"1.0"`) |
| `framework_version` | string | Version of the tool binary |
| `etag` | string | Deterministic content hash. Changes only when registrations change |
| `commands` | `Record<string, CommandEntry>` | Flat map keyed by dot-separated path (e.g. `"deploy.rollback"`) |
### CommandEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | One-sentence summary |
| `aliases` | string[] | no | Alternative invocation names |
| `danger_level` | `"safe"` \| `"mutating"` \| `"destructive"` | yes | Mutation risk level of the command. Sourced from REQ-C-002 |
| `required_scopes` | string[] | yes | Minimal permission strings needed from the active credential. Empty array if no auth required. Sourced from REQ-C-029 |
| `flags` | `Record<string, FlagEntry>` | yes | Keyed by flag name without `--` |
| `exit_codes` | `Record<string, ExitCodeEntry>` | yes | Keyed by code as string (e.g. `"0"`). Sourced from REQ-C-001 |
| `examples` | `Example[]` | no | Ready-to-use invocation strings |
| `subcommands` | string[] | no | Dot-separated paths of direct children. Resolve via top-level `commands` |
### FlagEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"string"` \| `"integer"` \| `"number"` \| `"boolean"` \| `"array"` \| `"enum"` | yes | |
| `required` | boolean | yes | |
| `description` | string | yes | |
| `default` | any | no | Omit (do not set `null`) when no default exists |
| `enum_values` | string[] | no | Only when `type` is `"enum"` |
| `short` | string (1 char) | no | Single-character shorthand |
### Example

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | What this example demonstrates |
| `command` | string | Full invocation an agent can use verbatim |
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
- `required: true` flags must always be present; absence will produce `ARG_ERROR (3)`
- `type: "enum"` — only values in `enum_values` are accepted; sending any other value produces `ARG_ERROR (3)`
- `default` absent — the flag is optional but has no fallback; omitting it changes behavior; include explicitly if the outcome matters
- `short` present — both `--flag-name value` and `-f value` are valid; prefer long form for clarity in agent-constructed calls

**Pre-planning retries from `exit_codes`**
- Before the first call, read the command's `exit_codes` map and identify which codes are retryable
- Build the retry/rollback plan before calling, not reactively — this avoids ambiguity about whether a retry is safe after a partial failure

**Manifest staleness**
- If a command call returns `REDIRECTED (13)` for a path that exists in the manifest — the manifest is stale; re-fetch unconditionally and update the cache
- If a call returns `ARG_ERROR (3)` for a flag shown as valid in the manifest — possible version skew; re-fetch manifest before retrying

## Coding agent notes

**Generation strategy**
- Generate the manifest by reflecting over registered commands at startup — do not generate it by hand or from a separate config file
- The `etag` must be a deterministic hash of the serialized command registrations — generate it as `sha256(canonical_json(commands))` where canonical JSON sorts keys

**Type representation**
- Generate `ManifestResponse` as a read-only snapshot type — it reflects the registration state at the moment `enable_manifest()` is called and does not update dynamically
- `commands` keys must be dot-separated strings matching the command's full invocation path — generate the key from the command's registration name, not from its handler function name

**Validation to generate**
- Assert every command in the registry appears in `commands` — missing commands are a silent discovery failure
- Assert every `exit_codes` entry in the manifest matches the corresponding command's `ExitCodeEntry` declarations exactly — no additions, no omissions
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
