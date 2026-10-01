# REQ-C-031: Passthrough Commands Delegate to Another Tool's Parser

**Tier:** Command Contract | **Priority:** P1

**Source:** [§69 Argument Order Ambiguity](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) · [§1 Exit Codes & Status Signaling](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) · [§3 Stderr vs Stdout Discipline](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Medium

---

## Description

Some commands wrap another tool's own argument parser: an `ingest` command that hands its arguments to beangulp, a `lint` command that runs a linter with whatever flags the caller gives. The wrapped tool owns the arguments, writes its own output to stdout, and chooses its own exit code. A command of this kind MUST declare `arguments: "passthrough"` at registration; every other command is `"declared"`, the default. The rules below apply only to a command whose manifest entry carries `arguments: "passthrough"`; a declared command keeps every requirement this one exempts.

**Arguments.** A passthrough command declares no local flags and no positionals. Every token after its command path reaches the delegated tool verbatim, including `--`, `--help`, and tokens spelled like the framework's own options, so global options and framework flags (`--format`, `--output`, `--timeout`, `--schema`, `--confirm-destructive`) go before the command path. A passthrough command therefore also declares `option_placement: "strict"` (REQ-C-027). When the command declares `help_argv`, a lone `--help` or `-h` after the command path is forwarded as that argv instead, such as `["extract", "--help"]`; without it, the lone token is forwarded unchanged.

**The envelope.** In JSON mode, once the framework's own options pass validation, the delegated tool owns stdout (file descriptor 1 included) and the framework writes the final `ResponseEnvelope` as the last line of stderr, after the tool exits. When `--output <path>` is given before the command path, the same envelope also goes to that file (`output_file: "envelope"`). An error found while validating the framework's own options is reported on stdout as for any command, because no tool has run. On success, `data` is `{"exit_code": 0}`.

**The exit code.** The process exits with the delegated tool's own exit code, unchanged, so scripts and the tool's documentation keep working. A non-zero delegated code gives `ok: false`, `error.code: "DELEGATED_EXIT"`, `data: {"exit_code": n}`, `meta.exit_code: n`, and `retryable: false`. Codes the framework emits itself keep their framework meanings and their own `error.code`: an argument error in the framework's options (`2`, `ARG_ERROR`, `phase: "validation"`), a refused destructive call, the timeout (`10`, `TIMEOUT`), and a signal (`128 + N`). This is the cost of keeping the tool's codes: a delegated `2` is the tool's usage error and promises nothing about side effects. An agent decides on a retry from the envelope's `error.code` and `retryable`, never from the process exit code alone.

**Exemptions, for passthrough commands only:**

- REQ-F-004 and REQ-F-006: the envelope is the last line of stderr, not stdout, which carries the delegated tool's output
- REQ-F-001 and REQ-F-002: the delegated code is outside the framework table's meanings; a delegated `2` carries no zero-side-effect guarantee and no `phase: "validation"`, and the framework neither checks nor rejects it at registration
- REQ-C-001: the command's `exit_codes` lists only the codes the framework emits for it; the delegated tool's codes are not declared
- REQ-C-003: a mutating passthrough command's `data` has no `effect`, because the framework cannot know what the tool changed; only a deduplicated replay adds `effect: "noop"`
- REQ-C-006 and REQ-C-015: no input schema describes the tool's arguments, and the framework validates only its own options in phase 1; `--schema` lists the framework's flags and the passthrough fields

**Still required:**

- `danger_level` (REQ-C-002): a destructive passthrough command is refused before the tool starts unless confirmed (REQ-O-021 when enabled). The framework cannot preview what the tool would change, so the refusal and a `--dry-run` (REQ-C-004) show the argv that would be forwarded, not its effect
- The timeout (REQ-F-011, REQ-F-012) and signal handling (REQ-F-013, REQ-F-069) cover the delegated tool, and their envelope is also the last line of stderr
- Deduplication (REQ-C-007): within a session, a repeat of the same argv is not run again; the replay writes nothing to stdout and returns the original `data` with `effect: "noop"`
- The audit log (REQ-O-030) records the invocation with `args` set to `{"argv": "[OMITTED]"}` plus any framework flags that changed what it did; the forwarded argv cannot be redacted without a schema, so it is never written

## Acceptance Criteria

- `tool manifest` shows `arguments: "passthrough"` and `option_placement: "strict"` on every passthrough command, and omits `arguments` or shows `"declared"` on every other command
- The framework rejects at registration a passthrough command that declares local flags, positionals, or `option_placement: "any"`
- Every token after a passthrough command's path, including `--`, `--help` with other tokens, and `--format`, reaches the delegated tool verbatim and is never parsed by the framework
- With `help_argv` declared, `tool <cmd> --help` forwards exactly `help_argv`; without it, the tool receives `--help`
- In JSON mode the last line of stderr parses as a `ResponseEnvelope`, and stdout holds only what the delegated tool wrote
- With `--output <path>` before the command path, the file holds the same envelope as the last stderr line
- A delegated exit code `n` is the process exit code; when `n` is non-zero the envelope has `error.code: "DELEGATED_EXIT"`, `data.exit_code: n`, `meta.exit_code: n`, and `retryable: false`
- An invalid framework option before the command path exits `2` with `ARG_ERROR` on stdout and the delegated tool does not start
- A destructive passthrough command without confirmation exits before the delegated tool starts
- A timed-out or signalled delegated tool ends with exit `10` or `128 + N` and an envelope on the last line of stderr
- A repeated argv in the same session does not start the delegated tool and returns `effect: "noop"`
- An audit log entry for a passthrough command has `args.argv` equal to `"[OMITTED]"` and contains no forwarded token
- A declared command's behavior under REQ-F-001, REQ-F-002, REQ-F-004, REQ-F-006, REQ-C-003, and REQ-C-015 is unchanged

## Schema

**Types:**

- [`manifest-response.md`](../schemas/manifest-response.md): `arguments` (`"declared"` | `"passthrough"`, absent means `"declared"`) and `help_argv` (string array) on `CommandEntry`. A passthrough entry requires `option_placement: "strict"`, empty `flags`, and no `positionals`; `help_argv` requires `arguments: "passthrough"`
- [`response-envelope.md`](../schemas/response-envelope.md): the final envelope, unchanged in shape, with `error.code: "DELEGATED_EXIT"` on a non-zero delegated code
- [`audit-log-entry.md`](../schemas/audit-log-entry.md): `args.argv` is `"[OMITTED]"`

## Wire Format

Manifest entry:

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
      "exit_codes": {}
    }
  }
}
```

A delegated usage error. stdout carries beangulp's own output; the envelope is the last line of stderr:

```bash
$ ledger --format json ingest extract --bogus statement.csv
```

```json
{"ok": false, "data": {"exit_code": 2}, "error": {"code": "DELEGATED_EXIT", "message": "The delegated tool exited 2", "retryable": false}, "warnings": [], "meta": {"exit_code": 2, "duration_ms": 412}}
```

The process exits `2`, and `error.code` says the code is beangulp's, not the framework's `ARG_ERROR`. A framework option placed after the path is not an error: `ledger ingest --timeout 5 extract x` forwards `--timeout 5` to beangulp.

## Example

```
register command "ingest":
  arguments: passthrough            # implies option_placement: strict
  help_argv: ["extract", "--help"]
  danger_level: mutating
  execute(ctx):
    return run_tool(["bean-ingest", *ctx.argv_rest])   # the tool's exit code

# Agent consults the manifest before calling:
# ledger --format json --output env.json ingest extract a.csv   ✓ framework flags before the path
# ledger ingest extract a.csv --format json                     ✗ --format goes to beangulp
# On exit 2: read the last stderr line; DELEGATED_EXIT → beangulp rejected its arguments,
#            and side effects are not ruled out; ARG_ERROR → the framework rejected its own
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-027](c-027-commands-declare-option-placement.md) | C | Extends: a passthrough command is always `option_placement: "strict"`, with no local options |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Specializes: the envelope keeps its shape but moves to the last line of stderr |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Specializes: stdout belongs to the delegated tool |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Specializes: the delegated exit code passes through as `DELEGATED_EXIT` |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | F | Specializes: a delegated `2` carries no zero-side-effect guarantee |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Specializes: no `effect` except `noop` on a replay |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Specializes: no input schema for the delegated arguments |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Consumes: `danger_level` still gates the call |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Composes: session deduplication keys on the forwarded argv |
| [REQ-F-012](f-012-timeout-exit-code-and-json-error.md) | F | Composes: the timeout covers the delegated tool |
| [REQ-O-030](o-030-opt-in-audit-log.md) | O | Composes: the audit log records the forwarded argv as `[OMITTED]` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `arguments` and `help_argv` appear in the manifest |
