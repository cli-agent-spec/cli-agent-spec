# Changelog

> Every change that alters a canonical schema, a requirement's acceptance criteria, or the failure mode taxonomy is recorded here.

## Versioning

- **Spec version** (`MAJOR.MINOR.PATCH`, git tag `vX.Y.Z`) versions the corpus as a whole. `MINOR` releases add or change failure modes, requirements, or schemas. `PATCH` releases fix prose, examples, and tooling without changing any contract. `MAJOR` is reserved for restructuring the taxonomy or the tier model
- **Contract version** (`MAJOR.MINOR`, per canonical schema, listed in `schemas/index.md`) versions each wire contract independently. A change that can reject a previously valid instance, or change what a field means, increments the contract's `MAJOR`. Additive optional fields increment `MINOR`
- A contract `MAJOR` increment always ships in a spec `MINOR` release with a migration section in this file
- `meta.schema_version` inside a response is neither: it versions one command's output shape (REQ-F-022)

## Unreleased

### Breaking: `--format` selects output representation

- REQ-O-001 makes `--format <format>` the canonical representation flag; `--output` and `-o` must not select a format
- `--output <path>` is reserved for a destination file; a command that registers it must reject a bare format name (`--output json`) with exit `2` and a suggestion naming `--format json`
- With `--output <path>`, `--format` selects the file's representation and stdout carries the `ResponseEnvelope`
- REQ-O-004 (`--format jsonl`) and REQ-O-005 (`--format id`) follow the rename; REQ-O-042 reads `<TOOLNAME>_FORMAT` instead of `<TOOLNAME>_OUTPUT`
- Every example, check, and agent workaround in the corpus uses `--format`; references to real tools (`aws --output json`, `kubectl -o json`) are unchanged

**Why:** `--output` is a format in cloud CLIs (`aws`, `kubectl`, `az`) and a file path in build and transfer tools (`gcc`, `curl`, `sort`, `pandoc`). An agent that passes `--output json` to a path-typed flag gets exit `0`, empty stdout, and a file named `json`. `--format` has one meaning wherever it appears.

**Migration:** rename the framework's global `--output` flag to `--format`; rename `<TOOLNAME>_OUTPUT` to `<TOOLNAME>_FORMAT`; rename any file-destination flag to `--output <path>` and add the format-name guard.

### New failure mode: §78 Output Flag Meaning Collision

- §78 covers an agent passing `--output json` or `-o json` to a tool whose `--output` takes a path: exit `0`, empty stdout, and a stray file named `json`
- Triage row 16 routes the signal (exit `0`, no JSON, a file named after a format value) to §78; the catch-all row becomes 17
- REQ-O-001 lists §78 as a source; its format-name guard on path-typed `--output` is the framework fix

### Breaking: ManifestResponse 3.0

- The root `flags` map lists global options: flags every command accepts, before or after the command path (REQ-F-079)
- `CommandEntry.flags` now means command-local flags only; a global option never appears in it, and no local flag reuses a global name or short alias
- A consumer that reads only `CommandEntry.flags` no longer sees `--format`, `--quiet`, or any other global option; the accepted set for a command is root `flags` plus its own `flags`
- `CommandEntry.positionals` lists positional arguments in call order as `PositionalEntry` objects (`name`, `type`, `required`, `description`, `enum_values`, `variadic`); before 3.0 a manifest had no place for them, so O-041's "construct any call from the manifest alone" could not hold for a command with positionals (REQ-C-015)
- `schema_version` must be `3.x`, so a consumer can tell a 3.0 manifest from an older one before reading `flags`; every example and the good democli mock emit `"3.0"`. Earlier examples emitted `"1.0"` under the 2.x contract, so consumers treat any value other than `3.x` as pre-3.0 rather than looking for a `2.` prefix

**Why:** the field keeps its shape but changes meaning, which the versioning rules above treat as a `MAJOR` change. A 2.x consumer that builds calls from `CommandEntry.flags` alone would conclude that `--format` does not exist.

**Migration:** producers emit `"schema_version": "3.0"`, move framework and application-wide flags from every `CommandEntry.flags` into the root `flags` map, and declare each command's positional arguments in `positionals`, in call order, instead of describing them in `description`. Consumers look a flag up in root `flags` first, then in the command's `flags`, place root flags before the command path, and give `positionals` in array order after the local options.

### Argument order and global options

- New REQ-F-079 (Global Option Scope): global options are listed once in the manifest root `flags`, accepted in any position on every command path, and never overwritten by a subcommand default; a command-local flag that reuses a global option's long name or short alias fails registration
- REQ-F-067 adds two acceptance criteria: `--` ends option parsing, and a scalar option repeated with different values exits `2`. Its framework examples are corrected: argparse and Click already accept options after positionals; their real gap is root options after the subcommand, which `parse_intermixed_args()` does not fix
- REQ-C-027 gives `strict` one meaning: every option, global or local, precedes the first positional and may follow the command path. The criterion that a strict command rejects later options with exit `2` is removed; those tokens are forwarded to the child, which is what `strict` declares
- §69 is rewritten around four modes (global option after the command path, local option before it, option read as a positional, value overwritten or duplicated). The Agent Workaround moves from "front-load every flag", which breaks local flags, to the canonical order `tool <global> <command path> <local> [--] <positionals>`, and from Tier A to Tier B
- The conformance kit adds `argument_order` (level 3, REQ-F-067, REQ-F-079): a profile's optional `argument_order` names a read command and a global option; the kit moves the option around the command path, detects a value overwritten by a subcommand default, and expects exit `2` for a conflicting repeat. An optional `positional` also proves a local option after a positional is parsed, not read as a second positional (§69 Mode 3). The good democli mock parses `--format json|plain` globally, lists it in its manifest root `flags`, and `deployments list` takes an optional environment positional
- `cli-agent-diagnose` routes to §69: a flag error followed by the same tokens succeeding in another order is §69, not §52; exit `2` after a single-value option (`--format`, `--limit`, `--timeout`, and a few more) repeated with different values is §69; `runner.preflight` flags that repeat before the call. Repeatable options such as `--header`, `--env`, and curl's `--output` never count

**Why:** "front-load all flags" traded Mode 1 for Mode 2, and nothing in the manifest told an agent which flags were global. The argparse default-overwrite case exits `0` with the wrong format.

**Migration:** move framework flags from each `CommandEntry.flags` into the root `flags`; register global options with parent parsers using `SUPPRESS` defaults (argparse) or persistent flags (Cobra); rename any local flag that shadows a global name or short alias.

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
