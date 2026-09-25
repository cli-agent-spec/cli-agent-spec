# REQ-F-079: Global Option Scope

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§69 Argument Order Ambiguity](../challenges/01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

A global option is a flag every command accepts: framework flags such as `--format`, `--quiet`, and `--schema`, plus any flag the application registers at the root. The framework MUST register each global option once and MUST make it behave identically on every command path, in any position: before the command path, after it, or among positionals. Flags the framework adds only to some commands (`--timeout` via REQ-C-012, `--yes` via REQ-C-005) are command-local, not global.

Three rules keep a global option unambiguous for an agent that cannot see the parser:

1. **Declared once.** `tool manifest` lists global options in the root `flags` map. A `CommandEntry.flags` map lists only the command's local flags, so an agent builds a call from two lookups: root `flags` plus the command's `flags`
2. **Reserved names.** A command-local flag MUST NOT reuse a global option's long name or short alias. The framework rejects such a registration at startup, before any command runs, so `-f` never means `--format` on one command and `--force` on another
3. **Position-independent value.** A global option's value is the value the caller passed, wherever it appeared. A subcommand's defaults MUST NOT overwrite a value given before the command path. This is the default behavior of argparse subparsers that copy the parent's options, which turns `tool --format json list` into plain text with exit `0`

## Acceptance Criteria

- Every global option appears in the manifest's root `flags` map and in no `CommandEntry.flags` map
- `tool --format json <cmd>` and `tool <cmd> --format json` produce identical output and exit code for every command path, including nested ones
- `tool --format json <cmd>` with no other `--format` emits JSON; no subcommand default replaces the value
- Registering a command-local flag whose long name or short alias equals a global option's fails at startup with a message naming both flags
- A test registry that registers the colliding flag `-f/--force` next to a global `-f/--format` fails to start

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md) — the root `flags` map holds global options as `FlagEntry` values; `CommandEntry.flags` holds command-local flags only

## Wire Format

```bash
$ tool manifest --format json
```

```json
{
  "ok": true,
  "data": {
    "schema_version": "1.0",
    "framework_version": "2.1.0",
    "etag": "sha256:4b7e21",
    "flags": {
      "format": { "type": "enum", "required": false, "default": "json", "enum_values": ["json", "jsonl", "tsv", "plain"], "description": "Output representation" },
      "quiet":  { "type": "boolean", "required": false, "default": false, "short": "q", "description": "Suppress warnings on stderr" }
    },
    "commands": {
      "list": {
        "description": "List items",
        "danger_level": "safe",
        "required_scopes": [],
        "flags": {
          "limit": { "type": "integer", "required": false, "default": 20, "description": "Maximum items returned" }
        },
        "exit_codes": { "0": { "name": "SUCCESS", "description": "Items listed", "retryable": false, "side_effects": "none" } }
      }
    }
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 9 }
}
```

## Example

```python
# argparse: share global options through a parent parser whose defaults are SUPPRESS,
# so the subparser never overwrites a value parsed before the command path
common = argparse.ArgumentParser(add_help=False)
common.add_argument("--format", choices=["json", "text"], default=argparse.SUPPRESS)

root = argparse.ArgumentParser(parents=[common])
sub = root.add_subparsers(dest="command", required=True)
sub.add_parser("list", parents=[common])

args = root.parse_args()
fmt = getattr(args, "format", "json")   # default applied once, after parsing

# Cobra (Go): register on the root as a persistent flag
# rootCmd.PersistentFlags().String("format", "json", "Output representation")
```

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-067](f-067-interspersed-option-parsing.md) | F | Composes: interspersed parsing places global options anywhere; this requirement makes them resolve the same everywhere |
| [REQ-O-001](o-001-output-format-flag.md) | O | Specializes: `--format` is the canonical global option |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: the manifest's root `flags` map lists global options |
| [REQ-C-027](c-027-commands-declare-option-placement.md) | C | Extends: strict placement applies to global options too |
