# REQ-O-041: tool manifest Built-In Command

**Tier:** Opt-In | **Priority:** P1

**Source:** [§52 Recursive Command Tree Discovery Cost](../challenges/01-critical-ecosystem-runtime-agent-specific/52-medium-command-tree-discovery.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MUST provide a `tool manifest` built-in command that returns the complete command tree — every subcommand, flag, type, description, and example — as a single JSON response. This replaces the O(N) pattern of calling `tool <cmd> --help` for each subcommand individually. The manifest MUST include: all command names and aliases, all flags per command with type, default, required status, and description, all exit codes per command, schema version, and the framework version. The manifest MUST be cacheable; `tool manifest --etag <prev>` returns 304-equivalent (`exit 0`, `data: null`, `meta.not_modified: true`) if unchanged.

## Acceptance Criteria

- `tool manifest` returns a single JSON object containing all commands and their full flag schemas
- The manifest includes exit code tables for every command
- `tool manifest --etag <hash>` returns `meta.not_modified: true` when the manifest is unchanged
- An agent can construct a valid call to any subcommand using only the manifest output, without calling `--help` on any subcommand

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) · [`exit-code-entry.md`](../schemas/exit-code-entry.md) · [`exit-code.md`](../schemas/exit-code.md) · [`response-envelope.md`](../schemas/response-envelope.md)

Requirement-specific constraints:

- `commands` must include every registered command, including built-ins
- `exit_codes` per command must be sourced from REQ-C-001 declarations — never hand-written in the manifest
- `etag` must be deterministic: identical registrations always produce the same value

---

## Wire Format

```bash
$ tool manifest
```

```json
{
  "ok": true,
  "data": {
    "schema_version": "1.0",
    "framework_version": "2.1.0",
    "etag": "sha256:a3f9c1...",
    "commands": {
      "deploy": {
        "description": "Deploy a build to a target environment",
        "flags": {
          "target":  { "type": "string",  "required": true,  "description": "Target environment name" },
          "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Validate without executing" },
          "timeout": { "type": "integer", "required": false, "default": 300,   "description": "Seconds before timeout" }
        },
        "exit_codes": {
          "0": { "name": "SUCCESS",   "description": "Deployment completed",       "retryable": false, "side_effects": "complete" },
          "2": { "name": "ARG_ERROR", "description": "Invalid target environment", "retryable": false, "side_effects": "none"     },
          "7": { "name": "TIMEOUT",   "description": "Deployment timed out",       "retryable": true,  "side_effects": "partial"  }
        },
        "examples": [
          { "description": "Deploy to staging", "command": "tool deploy --target staging" }
        ],
        "subcommands": ["deploy.rollback"]
      }
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 12 }
}
```

Etag cache hit:

```bash
$ tool manifest --etag sha256:a3f9c1...
```
```json
{ "ok": true, "data": null, "error": null, "warnings": [], "meta": { "not_modified": true } }
```

---

## Example

Opt-in is a single call at application startup. The framework introspects all registered commands automatically — no per-command manifest code.

```
app = Framework("tool")
app.enable_manifest()

# tool manifest  →  full JSON tree, no --help iteration needed
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Sources: `exit_codes` per command from REQ-C-001 declarations |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Sources: `flags` per command from REQ-C-015 declarations |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Sources: `ExitCode` names in `exit_codes` map |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Wraps: manifest output uses `ResponseEnvelope` |
| [REQ-F-021](f-021-data-meta-separation-in-response-envelope.md) | F | Composes: `schema_version` and `etag` align with per-response versioning |
