# REQ-C-032: Protocol Server Commands Declare Their Stdout Protocol

**Tier:** Command Contract | **Priority:** P1

**Source:** [§3 Stderr vs Stdout Discipline](../challenges/04-critical-output-and-parsing/03-high-stderr-stdout.md) · [§2 Output Format](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) · [§50 Stdin Consumption Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) · [§11 Timeouts](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Medium

---

## Description

Some commands run a long-lived protocol server over stdio: `tool mcp serve` speaks the Model Context Protocol, a `tool lsp` command speaks the Language Server Protocol, a `tool debug-adapter` command speaks the Debug Adapter Protocol. A client writes requests to the command's stdin and reads responses from its stdout until it ends the session. Stdout is the protocol channel from the first byte, so it never carries a `ResponseEnvelope`. A command of this kind MUST declare `stdout: "protocol"` at registration and MUST name its protocol in `protocol`. Absent `stdout` means stdout carries envelopes, as for every other command. The rules below apply only to a command whose manifest entry carries `stdout: "protocol"`; every other command keeps every requirement this one exempts.

**The protocol name.** `protocol` is a lowercase kebab-case name, present exactly when `stdout` is `"protocol"`. The spec documents three values: `mcp-stdio` (Model Context Protocol over stdio), `lsp` (Language Server Protocol), and `dap` (Debug Adapter Protocol). A tool that serves another protocol names it in the same form; an agent that does not recognize the name does not start the command as a server it can speak to.

**Before serving.** The command starts in two phases. In the first, the framework parses and validates the command's flags, and the handler prepares what it serves (opens a database, loads a configuration). Serving begins when the framework hands stdin and stdout to the protocol loop. The framework writes nothing to stdout in the first phase, not even an error: a failure there is reported on stderr and the process exits with the matching code from the command's declared `exit_codes`. In JSON mode the report is one `ResponseEnvelope` on the last line of stderr; in any other format it is the plain-text error that format gives. An invalid flag exits `2` with `ARG_ERROR` and the server never starts. `tool <cmd> --help` and `tool <cmd> --schema` print to stdout as for any command and never begin serving.

**While serving.** Once serving begins, stdout belongs to the protocol until the process exits, and stdin carries the client's messages. The framework's own diagnostics stay on stderr as plain text (REQ-F-006, REQ-F-038). A malformed or failing request is answered inside the protocol, such as with a JSON-RPC error response, and never ends the process with `2`.

**Exit codes.** Exit `0` means a clean shutdown: stdin reached end-of-file, or the client completed the protocol's own shutdown sequence (an LSP `shutdown` request followed by the `exit` notification). A clean shutdown writes no envelope. Any other exit ends with the envelope on the last line of stderr in JSON mode and a code from the command's declared `exit_codes`. A fatal error after serving began is never `2`, since requests may already have changed state; a signal exits `128 + N` (REQ-F-013, REQ-F-069) with its envelope on the last line of stderr. A client that ends a session with `SIGTERM` therefore expects `143`.

**Lifetime.** A protocol server is a foreground process: it lives exactly as long as the invocation and is neither a background process (REQ-C-010) nor an async job (REQ-C-022). The wall-clock timeout (REQ-F-011, REQ-F-012, and `--timeout` where REQ-C-012 registers it) covers only the time before serving begins; after that the client bounds the session by closing stdin or sending a signal. Every child process the server starts ends when it exits.

**Fields that do not combine with it.** The framework refuses at registration a protocol command that also declares any of the following, and the manifest schema rejects the same combinations:

- `arguments: "passthrough"` (REQ-C-031): a passthrough command gives stdout to a delegated tool, not to a protocol the manifest names
- `stderr: "child_log"` (REQ-F-038): stderr is the only channel left for the framework's diagnostics and the failure envelope
- `stdin` (REQ-F-054) or `interactive: true` (REQ-C-005): stdin carries the protocol, so the command reads no payload from it and never prompts
- `streaming_default: true` (REQ-O-004), `output_file` (REQ-O-001), `output_schema` (REQ-C-015), `output_formats`, or `output_media_types` (REQ-O-049): the command has no result on stdout to stream, format, or write to a file
- `async: true` (REQ-C-022) or `spawns_background_process: true`, `cleanup_command`, and `max_lifetime_seconds` (REQ-C-010): the server runs in the foreground until the client ends the session
- `confirm_flag` or `safe_default: true` (REQ-O-048): there is no single action to preview or confirm

**Commands kept off the tool's MCP server.** A tool that serves its commands as MCP tools, such as through an `mcp-stdio` protocol command, builds the tool list from its manifest. Some commands must never be a tool: an approval a person gives, a project-creating `init`, a watch loop that never returns. Such a command MUST declare `mcp: false` at registration. The field is present only when `false`; absent means the tool's MCP server may offer the command as a tool, and the manifest schema rejects `mcp: true`. A server built from the manifest never lists a command marked `mcp: false`, and a call naming it is refused inside the protocol as an unknown tool. An agent runs such a command through the CLI, or hands it to a person. `mcp` is independent of `stdout`: it applies to any command, and it says nothing about MCP servers other than the tool's own.

**Exemptions, for protocol commands only:**

- REQ-F-004 and REQ-F-006: stdout carries the protocol; the only envelope is the failure envelope on the last line of stderr
- REQ-C-003: a clean shutdown has no envelope, so no `effect`; what each request changed is reported inside the protocol
- REQ-C-004 and REQ-O-021: `danger_level` states the most severe effect any request the server answers can have, including `destructive`, but the command offers no `--dry-run` and takes no `--confirm-destructive`; confirming a single request is the protocol's concern (an MCP tool's `destructiveHint` annotation, for example)
- REQ-C-007: the command MUST NOT accept `--idempotency-key`, because a session answers many requests and has no single result to replay
- REQ-F-011: the default timeout stops at the start of serving

**Still required:**

- `danger_level` (REQ-C-002) and `required_scopes` (REQ-C-029), covering every request the server can answer
- `exit_codes` (REQ-C-001), listing every code the command can exit with, `0` for a clean shutdown included
- Input validation before serving (REQ-C-006, REQ-F-002): every flag is checked before the protocol loop starts, so an exit `2` means the server never ran

## Acceptance Criteria

- `tool manifest` shows `stdout: "protocol"` and a `protocol` name on every protocol server command, and neither field on any other command
- The framework rejects at registration a command that declares `stdout: "protocol"` without `protocol`, or `protocol` without `stdout: "protocol"`
- The framework rejects at registration a protocol command that declares any field in the list of fields that do not combine with it
- An invalid flag exits `2` with stdout empty; in JSON mode the last line of stderr parses as a `ResponseEnvelope` with `error.code: "ARG_ERROR"`
- A failure while preparing to serve exits with a code from the command's declared `exit_codes`, writes nothing to stdout, and in JSON mode ends stderr with the envelope
- `tool <cmd> --help` prints help to stdout, exits `0`, and does not read stdin
- Once serving begins, every byte on stdout is a protocol message: a client that speaks the declared protocol reads the server's first response without skipping any line
- A malformed request is answered with a protocol error and the server keeps running
- Closing the server's stdin ends the process with exit `0` and no envelope on stderr
- `SIGTERM` while serving ends the process with `143`, and in JSON mode the last line of stderr is an envelope
- A server that stays idle past the default timeout after serving begins is not terminated by the framework
- A protocol command does not accept `--idempotency-key`, `--dry-run`, `--output`, or `--confirm-destructive`
- A command without `stdout` behaves exactly as before under REQ-F-004, REQ-F-006, REQ-F-011, and REQ-C-007
- `tool manifest` shows `mcp: false` on every command the tool's MCP server leaves out, and no `mcp` field on any other command
- The tool's MCP server lists no command marked `mcp: false` in its tool list, and a call naming one is answered with a protocol error, not run
- A manifest with `mcp: true` on any command fails validation against the manifest schema

## Schema

**Types:**

- [`manifest-response.md`](../schemas/manifest-response.md): `stdout` (`"protocol"`, absent means stdout carries envelopes) and `protocol` (lowercase kebab-case name, documented values `mcp-stdio`, `lsp`, `dap`) on `CommandEntry`. Each requires the other, and a protocol entry carries none of the fields that do not combine with it. `mcp` (`false` only; absent means the tool's MCP server may offer the command) on any `CommandEntry`
- [`response-envelope.md`](../schemas/response-envelope.md): the failure envelope on the last line of stderr, unchanged in shape

## Wire Format

Manifest entry:

```json
{
  "schema_version": "3.16",
  "framework_version": "2.0.0",
  "etag": "sha256:7d1f40",
  "commands": {
    "mcp.serve": {
      "description": "Serve the tool's commands as MCP tools over stdio until stdin closes",
      "danger_level": "mutating",
      "required_scopes": [],
      "stdout": "protocol",
      "protocol": "mcp-stdio",
      "flags": {
        "read-only": { "type": "boolean", "required": false, "default": false, "description": "Expose only the tool's safe commands" }
      },
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "The client closed stdin and the server shut down cleanly", "retryable": false, "side_effects": "complete" },
        "2": { "name": "ARG_ERROR", "description": "A flag is invalid; the server did not start", "retryable": false, "side_effects": "none" },
        "5": { "name": "NOT_FOUND", "description": "The configuration file the server loads at startup does not exist; the server did not start", "retryable": false, "side_effects": "none" }
      }
    }
  }
}
```

A failure before serving. Stdout is empty; the envelope is the last line of stderr:

```bash
$ tool --format json mcp serve --read-only=maybe
```

```json
{"ok": false, "data": null, "error": {"code": "ARG_ERROR", "message": "--read-only expects a boolean, got 'maybe'", "retryable": false, "phase": "validation"}, "warnings": [], "meta": {"exit_code": 2, "duration_ms": 9}}
```

The process exits `2`. Started correctly, the same command writes only MCP messages to stdout and exits `0` when its client closes stdin.

A command kept off the MCP server. `tool mcp serve` never lists `release.approve` as a tool:

```json
{
  "schema_version": "3.17",
  "framework_version": "2.1.0",
  "etag": "sha256:91c3e7",
  "commands": {
    "release.approve": {
      "description": "Record a person's approval of a pending release",
      "danger_level": "mutating",
      "required_scopes": ["releases:approve"],
      "mcp": false,
      "flags": {},
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "The approval is recorded", "retryable": false, "side_effects": "complete" }
      }
    }
  }
}
```

## Example

```
register command "mcp.serve":
  stdout: protocol
  protocol: mcp-stdio
  danger_level: mutating
  execute(ctx):
    config = load_config()            # a failure here: envelope on stderr, declared exit code
    return serve_mcp(ctx.stdin, ctx.stdout, config)   # returns on stdin EOF → exit 0

# Agent consults the manifest before calling:
# stdout: "protocol", protocol: "mcp-stdio" → register it as an MCP server, never parse its stdout as an envelope
# Exit 2 before any MCP message arrives → read the last stderr line; the server never started
# Exit 143 after the agent sent SIGTERM → expected end of the session

register command "release.approve":
  mcp: false                          # a person approves; never an MCP tool
  danger_level: mutating

# mcp.serve builds its tool list from the manifest and leaves out release.approve
# An agent that needs the approval asks a person to run `tool release approve <id>`
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Specializes: the only envelope is the failure envelope on the last line of stderr |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Specializes: stdout belongs to the declared protocol |
| [REQ-C-031](c-031-passthrough-commands-delegate-to-another-parser.md) | C | Composes: a protocol command is never passthrough, and both put their failure envelope on the last line of stderr |
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Composes: a protocol command never declares `stderr: "child_log"` |
| [REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md) | F | Composes: a protocol command declares no `stdin`, because stdin carries the protocol |
| [REQ-F-011](f-011-default-timeout-per-command.md) | F | Specializes: the default timeout covers only the time before serving begins |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: `SIGTERM` while serving exits `143` with the envelope on stderr |
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Consumes: the declared `exit_codes`, including `0` for a clean shutdown |
| [REQ-C-002](c-002-command-declares-danger-level.md) | C | Consumes: `danger_level` covers every request the server can answer |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Specializes: a destructive protocol command offers no `--dry-run` |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Specializes: a protocol command does not accept `--idempotency-key` |
| [REQ-C-010](c-010-background-process-commands-declare-metadata.md) | C | Composes: a protocol server runs in the foreground and is not a background process |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `stdout`, `protocol`, and `mcp` appear in the manifest |
| [REQ-O-035](o-035-tool-mcp-validate-built-in-command.md) | O | Composes: a command marked `mcp: false` is never reported as missing from the MCP schema |
