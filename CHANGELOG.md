# Changelog

> Every change that alters a canonical schema, a requirement's acceptance criteria, or the failure mode taxonomy is recorded here.

## Versioning

- **Spec version** (`MAJOR.MINOR.PATCH`, git tag `vX.Y.Z`) versions the corpus as a whole. `MINOR` releases add or change failure modes, requirements, or schemas. `PATCH` releases fix prose, examples, and tooling without changing any contract. `MAJOR` is reserved for restructuring the taxonomy or the tier model
- **Contract version** (`MAJOR.MINOR`, per canonical schema, listed in `schemas/index.md`) versions each wire contract independently. A change that can reject a previously valid instance, or change what a field means, increments the contract's `MAJOR`. Additive optional fields increment `MINOR`
- A contract `MAJOR` increment always ships in a spec `MINOR` release with a migration section in this file
- `meta.schema_version` inside a response is neither: it versions one command's output shape (REQ-F-022)

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
- REQ-O-030: `audit-log` is a list command. Its default buffered answer carries `data.entries` and `meta.pagination` (REQ-F-018), with `has_more` true when `--limit` left out matching entries; a framework may make it streaming-default under REQ-O-004, and `--no-stream` then returns the buffered envelope
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
