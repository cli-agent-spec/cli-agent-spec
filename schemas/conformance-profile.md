# Schema: ConformanceProfile

**File:** [`conformance-profile.json`](conformance-profile.json)

> **Used by:** [`conformance/run.py`](../conformance/README.md) · [`conformance/profiles/`](../conformance/profiles/democli-good.json)

---

## Purpose

A profile tells the conformance kit how to invoke a CLI and which invocations are safe to probe. The kit cannot guess a tool's subcommands or which of them delete data, so the author of the profile states it once and every run is reproducible.

Key decisions:

- **Probes declare intent.** `kind` says what a correct CLI does with the call: finish without side effects, exit `2`, or refuse until confirmed
- **Confirmation flags never appear in a probe.** Destructive probes run without confirmation and with their declared `dry_run_flag`; the kit never deletes on purpose
- **Paths are relative to the profile.** A committed profile works from any working directory

---

## Values

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `"1.0"` | yes | Profile format version |
| `tool` | string | yes | Display name |
| `command` | string[] | yes | Invocation prefix; a first element containing `/` resolves against the profile directory, a bare name through `PATH` |
| `timeout_seconds` | number `(0, 120]` | yes | Per-run limit; exceeding it counts as a hang |
| `manifest` | string[] | no | Arguments that print the manifest; omit to skip `manifest_valid` |
| `argument_order` | `ArgumentOrder` | no | A read command and a global option to move around it; omit to skip `argument_order` |
| `probes` | `Probe[]` | yes | Invocations to run |

### Probe

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Unique label shown in evidence |
| `argv` | string[] | yes | Arguments after the prefix |
| `kind` | `"read"` \| `"destructive"` \| `"invalid"` | yes | Expected behavior class |
| `dry_run_flag` | string | when destructive | Flag that turns the probe into a preview |

### ArgumentOrder

The kit runs `command_path` with `local_args`, placing `global_flag` before the command path, between the path and the local option, and after the local option. Every placement must exit `0` with the same result; `alternate_value` must change stdout identically in every placement; the flag given twice with `value` and then `alternate_value` must exit `2`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command_path` | string[] | yes | Path of a side-effect-free command |
| `local_args` | string[] | yes | A command-local option and its value |
| `global_flag` | string | yes | Long name of a global option, usually `--format` |
| `value` | string | yes | Value whose stdout is a `ResponseEnvelope`, usually `json` |
| `alternate_value` | string | yes | Another accepted value with different stdout, such as `plain`; must differ from `value` |

---

## Examples

**Valid**
```json
{
  "schema_version": "1.0",
  "tool": "democli",
  "command": ["../../benchmark/harness/cli/good/democli"],
  "timeout_seconds": 5,
  "manifest": ["manifest"],
  "argument_order": { "command_path": ["deployments", "list"], "local_args": ["--limit", "5"], "global_flag": "--format", "value": "json", "alternate_value": "plain" },
  "probes": [
    { "name": "list deployments", "argv": ["deployments", "list"], "kind": "read" },
    { "name": "unknown flag", "argv": ["deployments", "list", "--no-such-flag"], "kind": "invalid" },
    { "name": "delete staging", "argv": ["deployments", "delete", "--filter", "env=staging"], "kind": "destructive", "dry_run_flag": "--dry-run" }
  ]
}
```

**Invalid — destructive probe without a preview flag**
```json
{
  "schema_version": "1.0",
  "tool": "democli",
  "command": ["democli"],
  "timeout_seconds": 5,
  "probes": [
    { "name": "delete staging", "argv": ["deployments", "delete", "--filter", "env=staging"], "kind": "destructive" }
  ]
}
```
Violation: `dry_run_flag` is required when `kind` is `destructive`.

---

## Common mistakes

- **Putting `--yes` or `--force` in a destructive probe.** The kit then executes the deletion for real; confirmation flags never belong in a profile
- **Marking a mutating command as `read`.** Read probes run several times (stdin closed, stdin open, `NO_COLOR`); anything that writes will write repeatedly
- **Pointing a profile at production credentials.** Probes call the real tool; use a sandbox account or a mock
- **Adding `--format json` to probe argv.** The envelope check exists to prove JSON activates in a non-TTY without flags (REQ-F-003); `argument_order` is the one place a profile names the format flag
- **Choosing an `alternate_value` that renders like the default.** The overwrite check compares stdout; an alternate that prints the same bytes as `value` reads as an ignored option

---

## Agent interpretation

- Generate a profile from `tool manifest`: `danger_level: "safe"` commands become `read` probes, `destructive` commands become `destructive` probes with the declared dry-run flag
- Never add a probe for a command whose `danger_level` is `mutating` unless a sandbox is confirmed
- Keep `timeout_seconds` short (5 or less); the hang checks rely on it

---

## Coding agent notes

- Validate the profile against this schema before running anything; `conformance/run.py` exits `2` with `INVALID_PROFILE` otherwise
- Commit profiles next to the CLI they describe and run the kit in that CLI's CI
- Tests: a profile with a destructive probe and no `dry_run_flag` is rejected; duplicate probe names are rejected

---

## Implementation notes

Probe kinds are deliberately few. A mutating kind was left out because the kit cannot undo side effects, and a conformance check that damages state is worse than no check. Commands that mutate are covered by the destructive-refusal and dry-run checks when they declare a preview flag.
