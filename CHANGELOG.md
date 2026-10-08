# Changelog

> Every change that alters a canonical schema, a requirement's acceptance criteria, or the failure mode taxonomy is recorded here.

## Versioning

- **Spec version** (`MAJOR.MINOR.PATCH`, git tag `vX.Y.Z`) versions the corpus as a whole. `MINOR` releases add or change failure modes, requirements, or schemas. `PATCH` releases fix prose, examples, and tooling without changing any contract. `MAJOR` is reserved for restructuring the taxonomy or the tier model
- **Contract version** (`MAJOR.MINOR`, per canonical schema, listed in `schemas/index.md`) versions each wire contract independently. A change that can reject a previously valid instance, or change what a field means, increments the contract's `MAJOR`. Additive optional fields increment `MINOR`
- A contract `MAJOR` increment always ships in a spec `MINOR` release with a migration section in this file
- `meta.schema_version` inside a response is neither: it versions one command's output shape (REQ-F-022)

## Unreleased

### A read-only `TIMEOUT` is not retryable by default

- REQ-C-014: the `TIMEOUT` acceptance criterion no longer says `side_effects: "none"` makes a timeout `retryable: true`. A `TIMEOUT` error's `retryable` equals the command's declared `TIMEOUT` entry; `side_effects: "partial"` forces `false`, and `side_effects: "none"` permits `true` without implying it
- REQ-C-014: new acceptance criterion: a command whose run length depends on its input declares `TIMEOUT` with `retryable: false, side_effects: "none"`, and its error carries `error.fix_required` naming a larger `--timeout`. The wire format and example gain that case beside the retryable timeout
- REQ-F-011: a command whose run length depends on its input declares a per-command default timeout sized for its expected inputs; no new mechanism
- §19: the retry taxonomy no longer lists `TIMEOUT` as `retryable: true`, and the exit code alignment says `side_effects: "none"` is necessary for a retryable timeout, not sufficient
- `exit-code-entry.md` and `exit-code.md` gain the input-dependent read-only timeout as a valid `retryable: false, side_effects: "none"` example and name declaring it retryable as a common mistake; the `TIMEOUT (10)` agent action in `exit-code.md` follows the entry's `retryable` and `fix_required`. No JSON schema changes

**Why:** REQ-C-014 defines `retryable` as "the identical invocation, unchanged, may succeed", yet its criterion made every side-effect-free timeout retryable, though a read-only command whose run length depends on its input times out again on the identical re-run (#82).

## 1.13.0 — 2026-10-06

### ExitCodeEntry 1.1: `error_codes` names the `error.code` values under each exit

- `ExitCodeEntry` gains optional `error_codes`: a unique array of the `error.code` values the command emits under that exit, each matching `^[A-Z][A-Z0-9_]+$`, the pattern `ResponseEnvelope` puts on `error.code`. Absent means the command does not declare them, never "none"; an empty array means the exit carries no `error.code`
- REQ-C-001: each entry SHOULD list its `error.code` values in `error_codes`. New acceptance criterion (a response under a declared list carries a listed code, or none for `[]`), and the `CONFLICT (6)` entry in the wire format and example lists `ALREADY_DEPLOYED`
- REQ-C-028: the `CONFLICT (6)` entry SHOULD list `ALREADY_EXISTS` in `error_codes`. New acceptance criterion and an `exit_codes` table in the wire format
- `exit-code-entry.md` gains the field row, a valid and an invalid example, common mistakes, the agent interpretation (branch on the received `error.code`; the list says in advance which values to plan for), and generated assertions; `manifest-response.md` gains a `3.19` example and the agent interpretation; `tests/test_manifest_schema.py` pins the schema behaviour
- `ManifestResponse` becomes 3.19, since its `exit_codes` maps carry `ExitCodeEntry`. A producer that lists `error_codes` emits `schema_version` `3.19`; earlier manifests stay valid, and on them an exit's `error.code` values can appear only in its `description`

**Why:** an `ExitCodeEntry` named the exit code (`6` `CONFLICT`) but not the `error.code` an agent branches on, and its closed schema left a REQ-C-028 command no way to publish `ALREADY_EXISTS` in its manifest (#78).

## 1.12.0 — 2026-10-05

### `tool doctor` exits `4` when a check fails

- REQ-O-026: the Description now says `tool doctor` exits `4` (`PRECONDITION`) with `error.code: "DOCTOR_CHECKS_FAILED"` when any check fails, as its acceptance criteria and wire format already did; it no longer says exit `1`

**Why:** the Description and the acceptance criteria named different exit codes for a failed check, so an agent branching on doctor's exit code could not tell which to expect (#71).

### ResponseEnvelope 2.3: numbered stream lines

- REQ-O-004: a stream MAY number its item lines with the reserved key `_seq`, `1` on the first and one more on each next line. A numbered stream numbers every item line, never a heartbeat or terminal line, puts `"_count": N` (the number of item lines) on its summary line, and ends a failure on an error envelope with `meta.items_emitted` (the last `_seq`, `0` before the first item). A line's `_seq` is never item data: an item type with its own `_seq` field does not number its stream, and a records consumer removes `_seq` before validating a record. New Description paragraph, three acceptance criteria, and numbered wire-format lines
- `ResponseMeta.items_emitted` (optional, non-negative integer) makes `ResponseEnvelope` 2.3; `response-envelope.md` gains the field row, a numbered-stream failure example, and the agent interpretation. Earlier instances stay valid, and a stream without `_seq` keeps its meaning
- §76 gains numbered lines as an optional enhancement against silent truncation; the streaming guide gains a "Numbering Stream Lines" section
- Conformance kit: `stream_contract` checks a stream whose first item line carries `_seq`: `_seq` on every item line counting up from `1`, none on heartbeat or terminal lines, `_count` equal to the number of item lines, and `meta.items_emitted` equal to the last `_seq` on an error terminal envelope; a later `_seq` in an unnumbered stream fails. The good democli mock numbers its `deployments list --stream` lines, including `meta.items_emitted` on its SIGINT envelope, and `streamcli` gains a passing numbered stream and failure, plus eight failing cases

**Why:** a REQ-O-004 stream gave an agent no way to tell a complete short stream from one that lost lines in a pipe, a log, or a truncating runtime, nor which item a failed stream stopped after (#67).

### A cancelled or partial run flags `data.partial` and names its signal in `error.context`

- REQ-F-013 and REQ-F-069: the Description and Example now put the partial flag at `data.partial: true` and REQ-F-069's signal name at `error.context.signal`, as both wire formats already did. A top-level `partial` or `error.signal` fails `ResponseEnvelope`, which admits no extra properties at either level
- §11, §13, and §16 examples move `partial` and the other partial-result fields (`completed_steps`, `resume_from`, `resume_token`, `results`, `summary`) into `data` and become complete envelopes; §13's agent workaround reads them from `data`. `comparison-matrix.md`'s REQ-F-013 sentence says the same
- Conformance kit: `stream_sigint` also requires the terminal `CANCELLED` envelope to carry `data.partial: true`. The good democli mock's `--stream` cancellation now emits it, and `streamcli` gains a failing `int-no-partial` case. The process-leak test looks only for sleeps from its own run, so concurrent runs in other checkouts no longer fail it
- No contract changes; generated reports under `evaluations/` are records of past runs and stay as they were

**Why:** REQ-F-013's and REQ-F-069's prose and examples put `partial` at the top level and the signal on `ErrorDetail`, which the envelope schema rejects, while their own wire formats used `data.partial` and `error.context.signal`, so an implementer had two answers and only one of them validated (#68).

### A declared dependency is needed at any version

- REQ-O-031: a `DependencyEntry.min_version` value is a minimum version or `"*"`, meaning any version, presence only. `tool doctor` runs the dependency's `check_command` and passes when it exits `0`, skipping `version_regex` and the version comparison; a dependency with no `--version` flag uses a presence command such as `command -v bean-format`. New acceptance criterion, and a `"*"` dependency in the wire format and example
- REQ-O-026: the `required_tools` `"*"` rule and the declared dependency rule read as one: `"*"` is a presence check, by `PATH` lookup for a `required_tools` entry and by `check_command` for a dependency, reported as `min_version: "*"` with no `found_version` in `data.dependencies`. New acceptance criterion
- `manifest-response.md` and the `min_version` description in `manifest-response.json` say the same. The field stays a required string, so `ManifestResponse` stays 3.18 with a description change only

**Why:** `min_version` was a required "minimum supported version" with no way to declare a dependency needed at any version, so a program with no `--version` flag could not be declared without inventing a version `doctor` could never check; `required_tools` gained `"*"` for the same reason in #58 (#63).

### `required_tools` declares a program needed at any version

- REQ-C-018: a `required_tools` value is a minimum version or `"*"`, meaning any version; the program need only resolve on `PATH` and is never run to read a version. New acceptance criterion and a `"*"` entry in the wire format and example
- REQ-O-026: `tool doctor` checks a `"*"` entry by `PATH` lookup only, never runs the program, and reports `required: "*"` with no `version`. New acceptance criterion and a passing `"*"` check in the wire format
- `manifest-response.md` and the `required_tools` description in `manifest-response.json` say the same. The value type stays a string, so `ManifestResponse` stays 3.16 with a description change only

**Why:** `required_tools` mapped each program to a minimum version with no way to declare one needed at any version, so a program with no `--version` flag, such as `bean-format`, could not be declared without inventing a version `doctor` could never check (#58).

### ManifestResponse 3.18: integer `enum_values`

- REQ-C-015: a flag or positional whose valid values are a few integers declares `type: "integer"` and lists them in `enum_values` as integers (`[0, 1, 2]`), with the same membership rule as a `type: "enum"` entry: every value a caller may pass, and nothing else. A value outside the list exits `2` with `ARG_ERROR` before any side effect
- `FlagEntry.enum_values` and `PositionalEntry.enum_values` are string arrays on `type: "enum"` entries, as before, and integer arrays on `type: "integer"` entries. The schema rejects a string list on an integer entry and an integer list on an enum entry; the `media_types` rule still requires `type: "enum"`
- REQ-C-015's wire format and example gain an integer flag with `enum_values`, and a new acceptance criterion; `manifest-response.md` gains the field rows, a valid and an invalid example, common mistakes, the agent interpretation (agents and shell completion read the integers as data), and a generated assertion; `tests/test_manifest_schema.py` pins the schema behaviour
- A producer that lists integer `enum_values` emits `schema_version` `3.18`. A 3.17 manifest whose `type: "integer"` entry carried string `enum_values` passed the schema though the prose forbade it; the schema now rejects it. The bump stays minor because it enforces a rule the prose already stated, and no corpus example is affected. On a pre-3.18 manifest an integer entry's allowed values can appear only in its `description`

**Why:** an integer flag such as `--sig-type 0|1|2` either lost its values to the description, where agents and shell completion cannot read them, or listed them as strings on a `type: "enum"` entry while the JSON routes take numbers (#59).

### ManifestResponse 3.17: commands kept off the MCP server

- REQ-C-032: a command the tool's own MCP server must never offer as a tool (an approval a person gives, a project-creating `init`, a watch loop that never returns) declares `CommandEntry.mcp: false`. The field is present only when `false`; absent means the tool's MCP server may offer the command, and the schema rejects `mcp: true`
- A server built from the manifest never lists a command marked `mcp: false`, and a call naming one is refused inside the protocol; an agent runs such a command through the CLI or hands it to a person
- REQ-O-035: `tool mcp-validate` never reports a command marked `mcp: false` as `missing_from_mcp`
- `manifest-response.md` gains the field row, a valid and an invalid example, the agent interpretation, and a generated assertion; `tests/test_manifest_schema.py` pins the schema behaviour
- A producer that sets `mcp` emits `schema_version` `3.17`; a pre-3.17 manifest stays valid, and on it an absent `mcp` cannot mark a command kept off the server

**Why:** a tool can serve its commands as MCP tools, yet `CommandEntry` took no extra properties and had no field to keep a command off that server, so a manifest could say so only in the description (#55).

### Conformance kit: `stream` probes check a streaming command's JSONL contract

- `ConformanceProfile` adds probe kind `stream`, with optional `deadline_seconds` (defaults to `timeout_seconds`) and optional `signal: "INT"` plus `after_lines`, which require each other. The schema and `conformance/run.py` reject either field on a non-`stream` probe, and `dry_run_flag` on a `stream` probe. Existing profiles stay valid
- A `stream` probe runs once, outside the single-envelope checks. The kit reads stdout line by line until the process exits; at the deadline it kills the probe's process group and fails the run instead of hanging
- New check `stream_contract` (level 3, REQ-O-004, §5, §76): every line is one JSON object, the stream ends on exactly one terminal line (the `"_summary": true` line or an error `ResponseEnvelope` with `ok: false`), a summary line exits `0`, an error envelope's `meta.exit_code` matches the exit code, and the process exits before the deadline
- New check `stream_sigint` (level 3, REQ-O-004, §16): with `signal`, the kit sends SIGINT after `after_lines` lines and requires exit `130` and a terminal error envelope with `error.code` `CANCELLED` (REQ-F-069). It is skipped on Windows
- A profile without a `stream` probe now reports both checks as `skip`, so its `level_3` verdict is `incomplete` instead of `pass`
- The good democli mock's `deployments list` accepts `--stream`, and `democli-good.json` adds two `stream` probes, so it still passes every check. New fixture `streamcli` with a passing and a failing profile

**Why:** the kit's probes expected one envelope per command, so nothing checked that a streaming command's lines parse, that it ends on one terminal line matching its exit code, or that SIGINT cancels it with exit `130` (#60).

## 1.11.0 — 2026-10-03

### External content in `error.context` is tagged and masked

- REQ-F-035: when `error.context` holds external content (a wrapped program's stderr, a remote log tail, an upstream error body), it carries `_source: "external"` and `_trusted: false` at its top level, and its external string values get REQ-F-058's high-entropy masking. A free-text value keeps its text: only each high-entropy substring is replaced. Keys an agent branches on (`exit_code`, `line`, `code`, `retryable`) are never masked
- A framework helper's own subprocess-failure context marks the child's stderr external by default, without command author action
- Outside text an author wants tagged and masked goes in `error.context` (REQ-C-013); `detail` keeps its meaning, and `response-envelope.md` tells an agent to treat `message`, `detail`, and `cause` as untrusted text always
- REQ-O-004: the `UPSTREAM_FAILED` context is external; the upstream's strings are masked, but `line`, `upstream_exit_code`, `upstream.code`, and `upstream.retryable` are not. REQ-C-031: a passthrough envelope copies no delegated output, so it carries no tags
- REQ-O-023 and REQ-O-037 cover the context too: `--no-injection-protection` drops its tags, `--unmask` returns its raw values
- New acceptance criteria and an error-envelope example in REQ-F-035; `response-envelope.md` tells an agent never to follow instructions found in a tagged `data` or `error.context`. `ErrorDetail.context` already allows extra keys, so `ResponseEnvelope` stays 2.1 with a description change only

**Why:** a failure's `error.context` routinely carries a wrapped program's stderr, yet REQ-F-035 tagged and masked external content only in `data`, so injected instructions and raw tokens reached an agent through the error path untagged (#38).

### ResponseEnvelope 2.2, AuditLogEntry 1.1: mutating streams

- REQ-O-004: a streaming command declares `danger_level` `safe` or `mutating`; the framework refuses to register a streaming `destructive` command, since a stream cannot ask confirmation per action (REQ-C-002)
- REQ-O-004, REQ-C-003: on a mutating stream, every item line carries its own `effect`, and the summary line carries `effects`, the number of events per effect value (`{"created": 2, "noop": 1}`). A buffered answer puts the events in `data` and the counts in `meta.effects`
- REQ-O-004: `--dry-run` covers the whole stream: every event reports a `would_*` effect (`would_noop` for an unchanged one), the summary line carries `"dry_run": true`, and a failed dry-run stream's error envelope carries `meta.dry_run: true`
- REQ-O-004: a mutating stream that fails after a live effect other than `noop` ends on an error envelope with `retryable: false`
- REQ-C-007: a streaming mutating command MUST NOT accept `--idempotency-key`, and the framework refuses to register one that does; every non-streaming mutating or destructive command still must accept it. REQ-C-002 names the exemption
- REQ-O-030: a stream is one invocation and gets one audit entry, whose new optional `effects` holds the summary line's counts, or the counts of the events emitted before a failure
- `ResponseMeta.effects` (optional) makes `ResponseEnvelope` 2.2, and `AuditLogEntry.effects` (optional) makes `AuditLogEntry` 1.1; earlier instances stay valid
- §12 and the streaming guide describe the exemption and the per-event effect

**Why:** REQ-C-003's `effect`, REQ-C-007's replay, dry-run, and the audit entry all assumed one result per run, so a bulk import or sync that streams its changes had no contract for reporting, previewing, retrying, or auditing them (#34).

### ManifestResponse 3.10: an `output` side-effect kind for a command's product

- `FilesystemSideEffect.type` gains `"output"`: a path the command writes as its product (a generated report, a rendered dashboard, collected evidence). The schema rejects `ttl_seconds` and `clearable_with` on an `output` entry
- REQ-C-011: `tool status --show-side-effects` lists an `output` path; `tool cleanup` never removes it, under any `--scope` including `all` (REQ-O-027, REQ-O-028)
- REQ-C-011 and REQ-C-002: `cache`, `log`, `temp`, and `output` writes are not state changes, so a command whose only writes are of these kinds stays `danger_level: "safe"`; `credential` and `config` writes make it at least `mutating`
- REQ-C-011 and REQ-O-001: `type: "output"` declares a location the command chooses itself; a path the caller names per call with `--output` is declared by `output_file` and is not repeated as an `output` entry. A default location used when `--output` is absent is an `output` entry
- A producer that declares an `output` side effect emits `schema_version` `3.10`; the other five kinds are unchanged, so earlier manifests stay valid

**Why:** a command that writes its product to a path it chooses had no fitting kind: declaring it `cache` let `cleanup` delete what the user asked for, leaving it undeclared broke REQ-C-011, and `mutating` over-declared a read-only command (#39).

### ManifestResponse 3.11: child log on stderr

- `CommandEntry.stderr` (optional, `"child_log"`; absent means the framework's own diagnostics only) marks a command that streams a wrapped program's output (`ansible-playbook`, `terraform apply`) to stderr as plain text, line by line, regardless of `--format` and verbosity
- REQ-F-038 names the exception: auto-quiet, `--verbose`, and `--debug` leave a declared child log streaming, `--quiet` (REQ-O-008) still silences it, and stdout still carries only the envelope. A command without the declaration is unchanged
- The schema and REQ-C-031 reject `child_log` on a passthrough command, whose stdout belongs to the delegated tool and whose envelope is the last line of stderr
- An agent may discard stderr for such a command and never reads stderr text as a failure signal; the exit code and the envelope stay authoritative
- A producer that sets `stderr` emits `schema_version` `3.11`; earlier manifests stay valid

**Why:** a command that wraps a tool whose log a person reads later had to break auto-quiet silently or hide the log, and the closed `CommandEntry` left only its `description` to warn an agent that stderr would be busy (#35).

### ManifestResponse 3.12: media types of format values

- REQ-O-001 fixes a media type for each spec format value: `json` → `application/json`, `jsonl` → `application/x-ndjson`, `tsv` → `text/tab-separated-values`, `plain`, `table`, and `id` → `text/plain`
- `FlagEntry.media_types` (optional, root `format` flag only): a map from format value to lowercase `type/subtype` media type. Required for every value outside the spec's table; a spec value listed there maps to the table's media type, and every key is one of `enum_values`. The schema rejects it on any other flag and on a non-`enum` flag
- `CommandEntry.output_media_types` (optional) is the same map beside REQ-O-049's `output_formats`, which keeps its type; it is required for a command-specific value that neither the table nor the root map covers, and overrides the root map for that command
- An agent parses only output whose media type is `application/json`, `application/x-ndjson`, or a `+json` type, and treats every other format's output as an opaque artifact
- A producer that sets either map emits `schema_version` `3.12`; earlier manifests stay valid

**Why:** a tool can register its own `--format` values beside the spec's (`html` for a page a person reads), and an agent had no way to learn from the manifest that such a value is not JSON, short of parsing the flag's `description` (#36).

### ManifestResponse 3.13: every environment variable has a home

- Root `secret_env_vars` (optional, a string array of names, never a value or default) lists the secrets every command reads, such as a tool-wide API key. A name there appears in no command's `secret_env_vars` and no flag's `env_vars`; a command's secrets are the root list plus its own
- REQ-F-073 names four homes in order: an auth command's `token_env_vars`, a `secret_env_vars` (root or command), a flag's `env_vars`, and root `env_vars`. When a variable fits two, the first wins: a token an auth command accepts is not repeated in that command's `secret_env_vars`, a secret never backs a flag's `env_vars`, and a flag-backed variable never sits in root `env_vars`. This replaces the "exactly one of three" wording
- Root `env_vars` follows the `FlagEntry.env_vars` rule: an entry without the tool prefix, such as an ecosystem's `LEDGER_FILE`, is allowed only right after the entry for the same setting's prefixed name, which the tool reads first. The criterion that every root entry carries the prefix is replaced; new acceptance criteria cover the order and the root secret list
- The universal exceptions gain `PWD`, `COLUMNS`, `ALL_PROXY`, the lowercase `http_proxy`, `https_proxy`, `no_proxy`, and `all_proxy`, `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `GITHUB_ACTIONS`, and `JENKINS_URL`; the naming guide's table lists them
- A producer that sets root `secret_env_vars` emits `schema_version` `3.13`; a pre-3.13 manifest stays valid, and on it an absent root `secret_env_vars` means unknown, not none

**Why:** implementing ManifestResponse 3.5 left a tool-wide secret with no home, forbade a root setting's established unprefixed name that a flag could declare, left `token_env_vars` out of the "three homes", and made tools that read `COLUMNS` or a CA bundle variable non-conforming (#37).

### ManifestResponse 3.14: a command's own flag confirms execution

- `CommandEntry.confirm_flag` (optional string) names a boolean flag of the command or root, such as `yes`. Without that flag the command previews under the dry-run contract (`would_*` effect, `meta.dry_run: true`, exit `0`, no side effects) and prompts for nothing; with it the command runs, with `meta.dry_run: false` and `meta.confirmed: true` (REQ-O-048)
- `--dry-run` wins: `--dry-run --yes` previews, and `tool exec --dry-run` previews a dispatched `confirm_flag` command even when its line passes the flag (REQ-O-050)
- The framework refuses `confirm_flag` at registration on a `safe` command, next to `safe_default: true`, on a passthrough command (REQ-C-031), on a command without a dry-run path, and when it names no declared boolean flag. The schema rejects the first three
- With REQ-O-021 enabled, a destructive command's `confirm_flag` is `confirm-destructive`, and without it the command previews and exits `0` instead of exiting `2` with `CONFIRMATION_REQUIRED`. REQ-C-005's `--yes` stays a no-op on commands that never prompt, except where `confirm_flag` is `yes`
- REQ-O-048 is retitled "High-Stakes Commands Default to Dry-Run Mode" and covers both `safe_default` and `confirm_flag`; `safe_default` is unchanged
- A producer that sets `confirm_flag` emits `schema_version` `3.14`; a pre-3.14 manifest stays valid, and on it an absent `confirm_flag` means unknown, not "runs without a flag"

**Why:** a mutating command that previews unless its own `--yes` is given could state that only in the flag's `description`, because `safe_default` is a boolean, destructive-only, and names `--live`. An agent reading the manifest expected a bare call to run (#40).

### ManifestResponse 3.15: idempotent commands

- `CommandEntry.idempotent` (optional boolean, absent means `false`): a repeat with the same arguments converges on the same state, whatever a previous attempt left behind. A delete of a named resource qualifies as much as a file rewrite; on a `safe` command the field is redundant and accepted without warning (REQ-C-002)
- The `ExitCodeEntry` invariant is unchanged: a partial-failure exit of an idempotent command stays `retryable: false`, `side_effects: "partial"`, because `retryable: true` still promises that nothing was written
- New agent rule: on a non-retryable exit whose entry declares `side_effects: "partial"` from a command declared `idempotent: true`, rerun the identical command once without inspecting state, and stop if it fails with the same `error.code`. The rule never covers `ARG_ERROR (2)` or an error carrying `fix_required` or `fix_command`. `guides/recoverable-errors.md` gains a convergent rung, and `exit-code-entry.md`, `exit-code.md`, `manifest-response.md`, §12, and `challenges/triage.md`'s default retry policy state the rule
- REQ-C-002 and REQ-C-007 separate `idempotent` from `--idempotency-key`, which deduplicates one request and returns `effect: "noop"`; a command declared `idempotent` still accepts the key
- A producer that sets `idempotent` emits `schema_version` `3.15`; a pre-3.15 manifest stays valid

**Why:** a mutating command that is safe to rerun after a partial failure (a snapshot writer that rewrites one file per server) had nowhere to say so, and its only honest exit declaration, `retryable: false` with `side_effects: "partial"`, sent agents to inspect state before every rerun (#41).

### A boolean flag given as false is not present

- REQ-C-026: a boolean flag is present only when its value is true. An explicit false (`--no-exact`, or false through any other explicit input channel) is the same as leaving the flag out, for `if_present`, `default_when_absent`, `any_of`, and `one_of` alike
- `if_value` compares values, so `if_value: false` still matches an explicit false
- New acceptance criterion: with `one_of: ["exact", "fuzzy"]`, `--no-exact --fuzzy` passes Phase 1, and `--no-exact` alone exits 2
- `ConditionalRule` descriptions in `manifest-response.json` and `manifest-response.md` state the definition; `ManifestResponse` stays 3.15 with a description change only

**Why:** REQ-C-026 defined a flag as present when the caller supplies it, so `--no-exact` could be read as choosing `exact` in a `one_of(exact, fuzzy)` group, and two conforming frameworks could accept and reject the same call (#50).

### ManifestResponse 3.16: protocol servers on stdout

- New REQ-C-032: a command that serves a long-lived protocol over stdio (`tool mcp serve`, a language server) declares `CommandEntry.stdout: "protocol"` and names the protocol in `CommandEntry.protocol`, a lowercase kebab-case string with documented values `mcp-stdio`, `lsp`, and `dap`. Each field requires the other; absent `stdout` means stdout carries envelopes, as before
- Stdout is the protocol channel from the first byte and never carries an envelope. A failure before serving begins writes nothing to stdout: it exits with a declared code, and in JSON mode the envelope is the last line of stderr. An invalid flag exits `2` and the server never starts
- Exit `0` is a clean shutdown (stdin end-of-file or the protocol's own shutdown sequence) and writes no envelope; any other exit ends stderr with the envelope in JSON mode, and a signal exits `128 + N`. A malformed request is answered inside the protocol, never by exit `2`
- A protocol server is a foreground process, not a background process (REQ-C-010) or an async job (REQ-C-022). The wall-clock timeout covers only the time before serving begins; the client ends the session by closing stdin or sending a signal
- The schema and the framework reject `stdout: "protocol"` next to `arguments: "passthrough"`, `stderr`, `stdin`, `interactive: true`, `streaming_default: true`, `output_file`, `output_schema`, `output_formats`, `output_media_types`, `async: true`, the REQ-C-010 fields, `confirm_flag`, or `safe_default: true`. A protocol command takes no `--idempotency-key` (REQ-C-007) and, even when `destructive`, no `--dry-run` (REQ-C-004)
- An agent that sees `stdout: "protocol"` starts the command only as a client of the named protocol and never parses its stdout as an envelope
- A producer that sets `stdout` emits `schema_version` `3.16`; a pre-3.16 manifest stays valid, and on it an absent `stdout` cannot mark a protocol command

**Why:** a tool can ship its own protocol server as a command, such as an MCP server over stdio, yet `CommandEntry` had no way to say that its stdout is not an envelope, so an agent could try to parse one from MCP messages (#51).

## 1.10.0 — 2026-10-01

### ManifestResponse 3.2: group rules in requires

- `ConditionalRule` gains two shapes: `{ "any_of": [...] }` (at least one listed flag is present) and `{ "one_of": [...] }` (exactly one listed flag is present). Each lists at least two distinct flag names (REQ-C-026)
- REQ-C-026 defines "present": the caller supplies the flag on the command line or through another explicit input channel the framework treats as supplied; a declared default does not count. New acceptance criteria: an `any_of` group with no flag present and a `one_of` group with two or more present exit 2 before any I/O, a `one_of` group with exactly one present passes, and the `ARG_ERROR` message and details name every flag in the group
- A `one_of` group replaces pairwise `prohibited` rules between its members
- A producer that emits a group rule emits `schema_version` `3.2`; the three existing shapes are unchanged, so a `3.0` or `3.1` manifest stays valid

**Why:** a command that takes one identifier from several flags (`--isin`, `--figi`, `--symbol`) could not declare that one is needed, so `--schema` did not reveal every required flag and REQ-C-026's own criterion failed for it (#14).

### Cursor errors and audit-log paging are defined

- REQ-O-003: a `--cursor` the framework cannot honor (malformed or expired) exits `2` (`ARG_ERROR`) with error code `INVALID_CURSOR`, `retryable: false`, and a `fix_required` to rerun without `--cursor`, the same on every list command. New wire example and acceptance criteria
- REQ-O-003: a token binds the query that produced it (filters and sort order); reusing it with a different query fails as `INVALID_CURSOR`. `--limit` is not part of the query and may change between pages
- REQ-O-030: the `audit-log` cursor anchors on the last returned entry's `timestamp` plus `request_id`, never a file offset or rotated-file index. After pruning, the next page returns the older matches that remain, without error, and `total` may shrink; entries appended after the first page never appear on later pages. The invalid-cursor criterion now names exit `2` and `INVALID_CURSOR`, and new criteria cover a token reused with other filters, pruning between pages, and an entry appended between pages

**Why:** both requirements said an invalid cursor "fails with a structured error" without an exit or error code, and left undefined what a token means under different filters or after rotation removes entries between pages, so frameworks would diverge and an agent could not branch on the failure (#15).
### `--output` writes a binary result's raw bytes

- REQ-O-001: when a command's result is a single binary value (REQ-F-017) and `--output <path>` is given, the file gets the raw bytes through the atomic write (REQ-F-070), and `--format` selects only the representation of the response on stdout
- The envelope's `data` describes the write: `{path, bytes, content_type, sha256}`; `content_type` is present only when the command declares one
- `--output -` on a binary result exits `2` and writes nothing; without `--output`, the payload stays base64-encoded in the envelope as before
- Commands whose result is not binary are unchanged: `--format` still selects the file's representation

**Why:** a downloader, exporter, or renderer's result is a file. Writing it "in the `--format` representation" produced a JSON or plain wrapper around base64, so such commands rolled their own path flag and file write and lost the atomic write, the no-file-on-failure guarantee, and a uniform envelope (#19).

### ManifestResponse 3.3: file output is marked

- `CommandEntry.output_file` (optional, `"formatted"` or `"binary"`) is present on every command that registers `--output <path>`, so an agent knows before the call whether the file gets the `--format` representation or the raw bytes (REQ-O-001)
- A producer that sets `output_file` emits `schema_version` `3.3`; a `3.2` manifest stays valid

### ManifestResponse 3.4: a flag declares the environment variables it reads

- `FlagEntry.env_vars` (optional, an array of `{name, deprecated?}`) lists the variables a flag reads when it is not passed, in precedence order: the first one set wins, and a passed flag beats them all. Root `flags` use it too, so `--format` lists `TOOL_FORMAT` (REQ-O-042)
- Agents set the first non-deprecated name instead of parsing the flag's `description`; on a pre-3.4 manifest an absent `env_vars` means unknown, not none
- `secret_env_vars` keeps its meaning: a secret is never a flag value (REQ-C-016), so its variable never appears in `env_vars`
- A producer that sets `env_vars` emits `schema_version` `3.4`; a `3.3` manifest stays valid

### Declared environment variables without the tool prefix

- REQ-F-073: a flag may read a variable outside the tool prefix and the universal exceptions, such as a service's established name or one shared across a tool family (`CLOUDFALL_PROJECT`), only when the manifest declares it in that flag's `env_vars` and the tool-prefixed name is listed first. The framework rejects a registration that reads an undeclared one
- REQ-F-073's promise that the manifest lists every recognized variable now points at `env_vars` and `secret_env_vars`; its wire format no longer shows an `environment` field the schema never had

**Why:** frameworks wrote "(read from `$A` or `$B` when not passed)" into flag descriptions because `FlagEntry` allowed no other place, and REQ-F-073 forbade the borrowed names outright. Contamination comes from variables a tool reads without saying so; a declared name is visible to the agent (#20).

### ManifestResponse 3.5: variables that back no flag are declared

- Root `env_vars` (optional, an array of `{name, deprecated?, description}`) lists every variable the tool reads that backs no flag and supplies no secret, such as `<TOOLNAME>_DEBUG`, `<PREFIX>AUDIT_LOG`, and `<PREFIX>SESSION_ID`. Each entry requires `description`; universal names such as `NO_COLOR` and `HOME` are not listed
- `EnvVarEntry` gains an optional `description`, which stays optional in a flag's `env_vars`
- REQ-F-073: every recognized variable appears in exactly one of root `env_vars`, a flag's `env_vars`, or `secret_env_vars`. New acceptance criteria; the wire example shows root `env_vars`
- REQ-F-051 and REQ-O-030 declare their variables in root `env_vars` when no flag backs them, with new acceptance criteria
- A producer that sets root `env_vars` emits `schema_version` `3.5`; a `3.4` manifest stays valid, and on it an absent root `env_vars` means unknown, not none

**Why:** REQ-F-073 promises that `tool manifest` lists every variable the tool recognizes, but after 3.4 the manifest had homes only for flag-backed variables and secrets, and its root rejects unknown fields, so `<TOOLNAME>_DEBUG` and the audit log's variables could not appear anywhere (#23).

### ManifestResponse 3.6: handler-written and envelope `--output` files

- `CommandEntry.output_file` gains two values: `"handler"` (the command handler writes the file; the command's own documentation describes its contents and `--format` does not select it) and `"envelope"` (the framework writes the final `ResponseEnvelope` as JSON to the file whatever `--format` selects; `--format` shapes only stdout) (REQ-O-001)
- The key stays on every command that registers `--output <path>`, so absence still means the command has no `--output`. New acceptance criterion: an `"envelope"` command given `--format plain` still writes a JSON envelope to the file
- A producer that emits either value emits `schema_version` `3.6`; earlier manifests stay valid

**Why:** `"formatted"` and `"binary"` both assume the framework renders the result into the file, so a command whose handler owns the path, or whose stdout carries something other than an envelope and saves the envelope to `--output`, fit neither and had to mislabel itself or omit the key, which reads as "no `--output`" (#27).

### ManifestResponse 3.7: object flags and the base of a relative `--output`

- `FlagEntry.type` gains `"object"`: the value is one argv token of JSON text, as `--raw-payload` takes it (REQ-O-032). The new `FlagEntry.schema` holds the draft-07 schema of one value: the object for an `object` flag (required there), one item for an `array` flag of objects; it appears on no other type (REQ-C-015)
- REQ-C-015: a JSON-object flag should declare `type: "object"` rather than `type: "string"` with the shape in prose (a `string` declaration stays conforming); for an `object` flag the framework validates the value against `schema` in Phase 1 and exits `2` (`ARG_ERROR`) on text that is not JSON or does not match. New acceptance criteria cover both
- `CommandEntry.output_file_base` (optional, `"cwd"`, `"project_root"`, or `"resource"`) names the directory a relative `--output` path resolves against; it appears only with `output_file`, and absence means `cwd`. An absolute path is used as given. A command whose base is not `cwd` must declare it (REQ-O-001)
- A producer that sets either field emits `schema_version` `3.7`; earlier manifests stay valid

**Why:** a flag that takes a JSON object had to declare itself a `string` and describe the shape in prose, and an agent writing to a project-relative `--output` from a subdirectory looked for the file under its working directory (#24).

### ManifestResponse 3.8: line-mode stdin and records consumers

- REQ-F-054: the 65536-byte cap (`TOOL_MAX_STDIN_BYTES`, exit `2` `STDIN_TOO_LARGE`) now names buffered stdin, and is unchanged there. A command that declares line mode (`stdin_input: "lines"` or `"records"`) reads nothing before the handler runs and gets one line at a time, with no total cap and a per-line cap (default 1048576 bytes). A longer line exits `1` with `LINE_TOO_LARGE` and `context.line`: `1`, not `2`, because the handler has already started (REQ-F-002)
- REQ-F-054 and §61: line mode avoids the pipe deadlock only when a separate process writes stdin, as in a shell pipeline; a caller that writes stdin and reads stdout from one thread still uses `--input-file`
- REQ-O-039: `--input-file` is registered on line-mode commands too and reads the file as lines with the same per-line cap; `--input-file -` reads stdin as lines
- REQ-O-004: a stream ends with one terminal line, the `_summary` line on success or the error `ResponseEnvelope` (`ok: false`) when the command fails after its first line
- REQ-O-004: a records consumer skips blank and heartbeat lines (REQ-O-038), validates each other line against its record type, and stops at the `_summary` line. An upstream error envelope exits `1` with `UPSTREAM_FAILED` (`context.line`, `upstream`, `upstream_exit_code`), end of stdin without a terminal line exits `1` with `UPSTREAM_INCOMPLETE` (`context.line`, `records`), and an invalid line exits `1` with `RECORD_INVALID` (`context.line`, `field`); all carry `retryable: false`. Read through `--input-file <path>`, end of file ends the input without a `_summary` line
- `CommandEntry.stdin` (optional, `{mode, max_bytes?, max_line_bytes?, record_schema?}`) declares how a command reads stdin: `buffered` with `max_bytes`, `lines` with `max_line_bytes`, or `records` with `max_line_bytes` and a required `record_schema`. An agent picks a pipe or `--input-file` and matches a producer's items to `record_schema` before the call
- REQ-F-065 links to REQ-O-004 for pipelines the caller's shell runs, and §56 names the records consumer errors as a framework defense
- A producer that sets `stdin` emits `schema_version` `3.8`; older manifests stay valid

**Why:** REQ-F-054 capped every stdin read at 64 KiB, so an NDJSON pipeline of 300 records of 320 bytes failed with `STDIN_TOO_LARGE`, and a consumer of another command's stream could not tell a failed or truncated upstream run from short valid input (#26).

### ManifestResponse 3.9: passthrough commands

- `CommandEntry.arguments` (optional, `"declared"` or `"passthrough"`; absent means `"declared"`) marks a command that hands every token after its path to another tool's parser. The schema requires `option_placement: "strict"`, empty `flags`, and no `positionals` on a passthrough command, and rejects `danger_level: "destructive"` on it
- `CommandEntry.help_argv` (optional, passthrough only) is the argv forwarded in place of a lone `--help` or `-h` after the command path
- New REQ-C-031 collects the passthrough rules. Framework options go before the command path. In JSON mode the final envelope is the last line of stderr, and the `--output` file when given; stdout belongs to the delegated tool. The process exits with the tool's own code, and a non-zero one gives `error.code: "DELEGATED_EXIT"`, `data.exit_code`, and `retryable: false`
- REQ-F-001, REQ-F-002, REQ-F-004, REQ-F-006, REQ-C-001, REQ-C-003, REQ-C-006, and REQ-C-015 each name their exemption for passthrough commands only; declared commands are unchanged. A passthrough command MUST NOT be destructive, and the framework refuses that registration: it cannot preview what the delegated tool would change, so it cannot offer the dry run or confirmation preview a destructive command owes. The timeout, signal handling, session deduplication, and the audit log still apply
- REQ-O-030 and `AuditLogEntry.args`: a passthrough command records its forwarded argv as `"argv": "[OMITTED]"`. Descriptions only, so `AuditLogEntry` stays 1.0
- A delegated `2` does not promise "no side effects": `challenges/triage.md` row 6, §14's workaround, `exit-code.md`, and `response-envelope.md` tell an agent to decide from `error.code` and `retryable`, not from the process exit code
- A producer that sets `arguments` or `help_argv` emits `schema_version` `3.9`; earlier manifests stay valid, and an absent `arguments` reads as `"declared"`

**Why:** a command wrapping another tool's parser (beangulp's `ingest`) cannot put the envelope on stdout or map the tool's exit codes onto the framework table without breaking the tool's own scripts and documentation, and the manifest had no way to say so beyond `option_placement: "strict"` and a sentence in `description` (#25).

## 1.9.0 — 2026-09-30

### Audit log and logger rotation defaults are recommendations

- REQ-O-030: configuring the maximum size, rotated file count, and maximum age stays MUST; the default values (10 MB, 5 files, 30 days) become SHOULD. A framework may ship smaller defaults, but its default size bound `max_size × (max_rotated_files + 1)` should not exceed 60 MB. New acceptance criterion: the application can set all three bounds
- REQ-F-042: the same wording for the framework logger's defaults (100 MB, 5 files, 30 days); it states the derived bound and that its defaults do not apply to the audit log

**Why:** both requirements put the defaults in parentheses inside a MUST sentence and no criterion tested them, so a framework could not tell whether smaller defaults conformed. Frameworks also read REQ-F-042's defaults (600 MB bound) as the audit log's (#7).

### ManifestResponse 3.1: built-in commands are marked

- `CommandEntry.builtin` (optional boolean, default `false`) is `true` for commands the framework registers itself, such as `manifest`, `doctor`, and `audit-log`, and for their subcommands; an application command that replaces a built-in's name is `false` (REQ-O-041)
- Agents filter on `builtin` when building a task list or skill set instead of matching a hard-coded list of built-in names
- A producer that sets `builtin` emits `schema_version` `3.1`; a `3.0` manifest stays valid and reads as having no marked built-ins (#9)

### Audit log accepts framework conventions

- REQ-O-030: an entry's `command` equals `meta.command` exactly, space-separated (`config set`) or dot-separated (`config.set`) as the framework spells it consistently; `audit-log --command` accepts both spellings and keeps the whole-word prefix rule in each. New acceptance criteria cover the dot form and `command` matching `meta.command`
- REQ-O-030: `audit-log` is a list command. Its default buffered answer carries `data.entries` and `meta.pagination` (REQ-F-018); `total` is the matched count or `null`. It accepts `--cursor`: when `--limit` leaves out older matching entries, `truncated` and `has_more` are `true` and `next_cursor` returns the next-older page, oldest first within it; the last page has `next_cursor: null`. A framework may make it streaming-default under REQ-O-004, and `--no-stream` then returns the buffered envelope; streamed output carries the pagination on its final summary line
- REQ-O-030: `session_id` comes from the framework's one session variable, a prefixed variable it already reads for the agent session id (for example for REQ-C-007 idempotency keys), else `<PREFIX>SESSION_ID`; the framework documents its name
- `AuditLogEntry` changes descriptions only (`command`, `session_id`): no instance valid before becomes invalid, so its contract version is unchanged

**Why:** a framework implementing REQ-O-030 (treaty) already spells `meta.command` as a dot path, streams list output, and reads a session id for idempotency keys. REQ-F-024 never pins `meta.command`'s separator, so requiring the space form forced two spellings of one command in one CLI, and a second session variable would record a different value from the one the framework already trusts (#12).

## 1.8.0 — 2026-09-30

### Breaking: `--format` selects output representation

- REQ-O-001 makes `--format <format>` the canonical representation flag; `--output` and `-o` must not select a format
- `--output <path>` is reserved for a destination file; a command that registers it must reject a bare format name (`--output json`) with exit `2` and a suggestion naming `--format json`
- With `--output <path>`, `--format` selects the file's representation and stdout carries the `ResponseEnvelope`
- REQ-O-004 (`--format jsonl`) and REQ-O-005 (`--format id`) follow the rename; REQ-O-042 reads `<TOOLNAME>_FORMAT` instead of `<TOOLNAME>_OUTPUT`
- Every example, check, and agent workaround in the corpus uses `--format`; references to real tools (`aws --output json`, `kubectl -o json`) are unchanged

**Why:** `--output` is a format in cloud CLIs (`aws`, `kubectl`, `az`) and a file path in build and transfer tools (`gcc`, `curl`, `sort`, `pandoc`). An agent that passes `--output json` to a path-typed flag gets exit `0`, empty stdout, and a file named `json`. `--format` has one meaning wherever it appears.

**Migration:** rename the framework's global `--output` flag to `--format`; rename `<TOOLNAME>_OUTPUT` to `<TOOLNAME>_FORMAT`; rename any file-destination flag to `--output <path>` and add the format-name guard.

### Breaking: ManifestResponse 3.0

- The root `flags` map lists global options: flags every command accepts, before or after the command path (REQ-F-079)
- `CommandEntry.flags` now means command-local flags only; a global option never appears in it, and no local flag reuses a global name or short alias
- A consumer that reads only `CommandEntry.flags` no longer sees `--format`, `--quiet`, or any other global option; the accepted set for a command is root `flags` plus its own `flags`
- `CommandEntry.positionals` lists positional arguments in call order as `PositionalEntry` objects (`name`, `type`, `required`, `description`, `enum_values`, `variadic`); before 3.0 a manifest had no place for them, so O-041's "construct any call from the manifest alone" could not hold for a command with positionals (REQ-C-015)
- `schema_version` must be `3.x`, so a consumer can tell a 3.0 manifest from an older one before reading `flags`; every example and the good democli mock emit `"3.0"`. Earlier examples emitted `"1.0"` under the 2.x contract, so consumers treat any value other than `3.x` as pre-3.0 rather than looking for a `2.` prefix

**Why:** the field keeps its shape but changes meaning, which the versioning rules above treat as a `MAJOR` change. A 2.x consumer that builds calls from `CommandEntry.flags` alone would conclude that `--format` does not exist.

**Migration:** producers emit `"schema_version": "3.0"`, move framework and application-wide flags from every `CommandEntry.flags` into the root `flags` map, and declare each command's positional arguments in `positionals`, in call order, instead of describing them in `description`. Consumers look a flag up in root `flags` first, then in the command's `flags`, place root flags before the command path, and give `positionals` in array order after the local options.

### Breaking: the audit log is opt-in (REQ-F-026 retired)

- REQ-F-026 (append-only audit log) is merged into REQ-O-030 and its ID is retired; the corpus has 158 requirements (78 REQ-F)
- As a Framework-Automatic requirement, the log made every CLI append to the user's home directory on every invocation, unbounded and without the author knowing. REQ-O-030 keeps it off by default, enabled by the application or by the operator through `<PREFIX>AUDIT_LOG`

**Migration:** stop writing the audit log unconditionally; write it only when the application calls `enable_audit_log()` or the operator sets `<PREFIX>AUDIT_LOG`.

### New failure mode: §78 Output Flag Meaning Collision

- §78 covers an agent passing `--output json` or `-o json` to a tool whose `--output` takes a path: exit `0`, empty stdout, and a stray file named `json`
- Triage row 16 routes the signal (exit `0`, no JSON, a file named after a format value) to §78; the catch-all row becomes 17
- REQ-O-001 lists §78 as a source; its format-name guard on path-typed `--output` is the framework fix

### Argument order and global options

- New REQ-F-079 (Global Option Scope): global options are listed once in the manifest root `flags`, accepted in any position on every command path, and never overwritten by a subcommand default; a command-local flag that reuses a global option's long name or short alias fails registration
- REQ-F-067 adds two acceptance criteria: `--` ends option parsing, and a scalar option repeated with different values exits `2`. Its framework examples are corrected: argparse and Click already accept options after positionals; their real gap is root options after the subcommand, which `parse_intermixed_args()` does not fix
- REQ-C-027 gives `strict` one meaning: every option, global or local, precedes the first positional and may follow the command path. The criterion that a strict command rejects later options with exit `2` is removed; those tokens are forwarded to the child, which is what `strict` declares
- §69 is rewritten around four modes (global option after the command path, local option before it, option read as a positional, value overwritten or duplicated). The Agent Workaround moves from "front-load every flag", which breaks local flags, to the canonical order `tool <global> <command path> <local> [--] <positionals>`, and from Tier A to Tier B
- The conformance kit adds `argument_order` (level 3, REQ-F-067, REQ-F-079): a profile's optional `argument_order` names a read command and a global option; the kit moves the option around the command path, detects a value overwritten by a subcommand default, and expects exit `2` for a conflicting repeat. An optional `positional` also proves a local option after a positional is parsed, not read as a second positional (§69 Mode 3). The good democli mock parses `--format json|plain` globally, lists it in its manifest root `flags`, and `deployments list` takes an optional environment positional
- `cli-agent-diagnose` routes to §69: a flag error followed by the same tokens succeeding in another order is §69, not §52; exit `2` after a single-value option (`--format`, `--limit`, `--timeout`, and a few more) repeated with different values is §69; `runner.preflight` flags that repeat before the call. Repeatable options such as `--header`, `--env`, and curl's `--output` never count

**Why:** "front-load all flags" traded Mode 1 for Mode 2, and nothing in the manifest told an agent which flags were global. The argparse default-overwrite case exits `0` with the wrong format.

**Migration:** move framework flags from each `CommandEntry.flags` into the root `flags`; register global options with parent parsers using `SUPPRESS` defaults (argparse) or persistent flags (Cobra); rename any local flag that shadows a global name or short alias.

### REQ-O-030 audit log: gaps closed, AuditLogEntry 1.0, ResponseEnvelope 2.1

- `<PREFIX>AUDIT_LOG` accepts only `1`, `0`, or an absolute path; any other value exits `2` with `INVALID_AUDIT_LOG_SETTING`. `1` keeps the application's path and falls back to the default; an absolute path overrides both
- `tool audit-log` is registered on every CLI; with the log disabled it exits `4` with `AUDIT_LOG_DISABLED` instead of returning an empty list
- Every invocation that resolves to a command is logged, including argument errors after resolution, `--validate-only`, `--dry-run`, and refused destructive commands; unresolved commands are not
- `operator` becomes `session_id`, read verbatim from `<PREFIX>SESSION_ID`; `trace_id` is present only when `TOOL_TRACE_ID` is set; a new `warnings` field records warning codes, so REQ-O-023 and REQ-O-047 events are queryable
- Entries are capped at 16 KiB (oversized `args` values become `[TRUNCATED]`, with `truncated: true`); the maximum age applies to the active file as well as rotated ones; `tool cleanup` never removes the log
- The log file is created `0600` and its directory `0700`; existing modes are left unchanged
- `AUDIT_LOG_UNAVAILABLE` goes to stderr when the output has no envelope; the entry is written before the response is emitted
- `audit-log` returns entries oldest first, `--limit n` keeps the newest `n`, `--since` accepts `<n>s|m|h|d` or an ISO 8601 datetime, and `--command` matches a space-separated path or a whole-word prefix
- New canonical schema `AuditLogEntry` 1.0 (`schemas/audit-log-entry.json`); `ResponseEnvelope` 2.1 adds the optional `meta.audit_log_path`
- REQ-O-023 emits an `INJECTION_PROTECTION_DISABLED` warning whenever `--no-injection-protection` is used; it and `AUDIT_LOG_UNAVAILABLE` join the standard warning codes

**Why:** two conforming frameworks could disagree on every point above, the size and age bounds did not hold for large arguments or rarely used tools, and the log was readable by every local user under a default umask.

### ResponseMeta declares its REQ-F fields

- `tool_version`, `update_available` (REQ-F-023), `trace_id`, `command`, and `timestamp` (REQ-F-024) are declared as optional `ResponseMeta` fields; examples using them are now type-checked. Part of `ResponseEnvelope` 2.1

### Validation

- The example validator and the conformance kit enforce draft-07 `format` keywords (`date-time` via `rfc3339-validator`) and fail when the checker is unavailable, instead of passing any string
- The example validator checks meta-only envelope fragments, standalone `ErrorDetail` objects, failure mode index entries, and exit-code entries that lack required fields; field sets for classification are read from the schema files
- Corpus counters in report templates, the website, mkdocs, and the requirements index footer are checked by `validate_links.py`
- Skill reference bundles sync by checksum, not size and mtime

### Tooling

- `cli-agent-diagnose` detects the §78 template echo: `--format <value>` exits `0` and every stdout line is that literal value
- The preflight hook splits compound commands without surrounding spaces, reads `#` as a comment only at the start of a word, strips trailing comments and backslash-newline continuations, and is checked against bash word splitting by a differential test
- `cli-agent-readiness` scores a pre-3.0 manifest as an older contract, not as schema-invalid
- `ManifestResponse` 3.0 adds an optional root `exit_codes` table that every command inherits; `CommandEntry.exit_codes` then holds only additions and overrides
- Benchmark harness: scenarios S6 to S8 with graders, `--cli-dir` and free-form `--mode` for builds outside the repo, and fixed S2 and S5 graders that counted argument errors and `--help` as live calls

### Comparison matrix

- §75–78 rows and rationale notes added; Part 2 score tables are recomputed from all 75 Part 1 cells
- Part 3 has one analysis section per matrix row, including §69–78

## 1.7.0 — 2026-09-15

### Breaking: ResponseEnvelope 2.0

- `meta.exit_code` is required and must equal the process exit code; `ok` is derived from it and the schema enforces the relationship
- `warnings` items are `WarningDetail` objects (`code`, `message`, optional `context`) instead of strings
- `meta.pagination` (`total`, `returned`, `truncated`, `has_more`, `next_cursor`) replaces the top-level `pagination` object and `meta.cursor`
- `tool exec` output lines carry `_cmd` and `_line` in `meta`, not at the top level
- `ErrorDetail` declares `cause`, `context`, and `docs_url`; structured facts move from `detail` objects to `context`
- `error.code` is a domain code that may reuse an `ExitCode` name; the exit code travels in `meta.exit_code`
- `data` on failure is `null` unless the command declares a failure payload (REQ-C-009, REQ-C-028, REQ-O-026)

**Migration:** set `meta.exit_code` in the envelope factory; wrap each warning string as `{ "code": "...", "message": "<old string>" }`; move `pagination` and `cursor` under `meta.pagination`; move `_cmd`/`_line` into `meta`; rename object-valued `error.detail` to `error.context`.

### Breaking: ManifestResponse 2.0

- `CommandEntry.required_scopes` is required (the doc already said so; the JSON did not)
- `CommandEntry` and `FlagEntry` declare every field the Command Contract and Opt-In requirements add; unknown fields remain rejected
- `exit_codes` keys must be integer strings

**Migration:** emit `required_scopes: []` for commands without auth; rename any undeclared extension fields to the names in `schemas/manifest-response.md`.

### Schema mechanics

- Every schema `$id` equals its filename, so `$ref` by filename resolves in ajv and jsonschema
- `DispatchRequest._opts` values use `anyOf`; integer overrides validate
- New tooling schemas: `FailureModeIndex`, `ConformanceProfile`, `ConformanceResult`

### Contract fixes

- Framework signal handlers may exit `130` (SIGINT) and `143` (SIGTERM); commands still may not use `126–255`
- `exit-code.md` no longer calls `126–255` safe to retry; signal exits require state inspection
- On any disagreement between envelope and process exit code, failure wins (resolves a contradiction with triage row 2)
- REQ-F-045 rejects hallucinated input with exit `2`, not `3`
- REQ-C-028 uses `CONFLICT (6)` with `error.code: "ALREADY_EXISTS"`
- REQ-O-041 example moves `TIMEOUT` to code `10` with `retryable: false`
- REQ-F-022 `meta.schema_version` is `MAJOR.MINOR`
- IMPLEMENTING.md Path A no longer calls timeouts retryable
- README exit code example names the right codes

### Added

- `requirements/levels.md`: conformance levels 1 (12 requirements), 2 (all `P0`), 3 (all)
- `conformance/run.py`: deterministic conformance kit with eleven checks and level verdicts
- `challenges/index.json`: generated machine-readable failure mode taxonomy
- CI gate: link, section, counter, snippet, level, schema, and example validation; skill bundle drift check; tests; ajv compile
- Benchmark harness v2: trials per cell, tool-log grading, per-trial state isolation, `--regrade`, rendered results
- `cli-agent-diagnose`: classifier reads `challenges/index.json` and a rule table (`signal_rules.py`) covering 31 failure modes, one or more rules per triage row; trace capture and analysis scripts (`filter.py`, `analyze.py`, `stats.py`, `traj.py`); OpenRouter models for `--llm`

### Changed

- `cli-agent-diagnose` classifies a shell `command not found` as §20 (missing dependency) per triage row 4, not §52

### Known gaps

- §70 (single-argument arity) has no requirement

## 1.6.0

Baseline before this changelog: 74 failure modes, 158 requirements, triage and recovery layer (Signature, Tier, Fallback lines; `fix_command`; `extract_envelope`).
