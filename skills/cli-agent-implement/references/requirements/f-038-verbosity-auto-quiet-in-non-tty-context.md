# REQ-F-038: Verbosity Auto-Quiet in Non-TTY Context

**Tier:** Framework-Automatic | **Priority:** P2

**Source:** [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Low / Context: High

---

## Description

When stdout is not a TTY or when `CI` is set, the framework MUST automatically suppress all non-essential prose from stderr (equivalent to `--quiet`). Only the structured JSON output on stdout and explicit errors on stderr MUST remain. Command authors MUST NOT need to check TTY state themselves; the framework's `log()` and `progress()` primitives respect this mode automatically.

**Child log exception.** A command that runs another program whose log is the output a person reads later (`ansible-playbook`, `terraform apply`) MAY stream that program's output to stderr as plain text, line by line, regardless of `--format`, auto-quiet, and `--verbose`. Such a command MUST declare `stderr: "child_log"` at registration, and the manifest shows it. `--quiet` (REQ-O-008) still silences the child log, and stdout still carries only the envelope (REQ-F-006). A command without the declaration keeps every rule above, so its stderr carries the framework's own diagnostics only. A passthrough command (REQ-C-031) never declares `child_log`: its stdout belongs to the delegated tool and its envelope is the last line of stderr, so the promise that stdout holds only the envelope cannot hold.

## Acceptance Criteria

- In a non-TTY context, `progress()` calls produce no output
- In a non-TTY context, `log()` calls at level INFO and below produce no stderr output
- Error-level `log()` calls are always emitted regardless of TTY state
- Explicitly passing `--verbose` overrides auto-quiet mode
- A command that declares `stderr: "child_log"` streams the wrapped program's output to stderr line by line in a non-TTY context, and stdout holds only the envelope
- With `--quiet`, a `child_log` command writes zero bytes to stderr
- In a non-TTY context, a command without `stderr: "child_log"` writes no wrapped program's output to stderr
- The framework rejects at registration a passthrough command that declares `stderr: "child_log"`

---

## Schema

**Type:** [`manifest-response.md`](../schemas/manifest-response.md)

`CommandEntry.stderr` (`"child_log"`, absent means framework diagnostics only) declares the child log exception. The schema rejects it on an entry with `arguments: "passthrough"`.

---

## Wire Format

A command that declares the child log exception:

```json
{
  "schema_version": "3.11",
  "framework_version": "2.1.0",
  "etag": "sha256:5be0a3",
  "commands": {
    "provision": {
      "description": "Run the site playbook against the inventory; ansible-playbook's log streams to stderr",
      "danger_level": "mutating",
      "required_scopes": [],
      "stderr": "child_log",
      "flags": {},
      "exit_codes": {}
    }
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework checks `isatty(stdout)` and the `CI` environment variable at startup. In non-TTY or CI contexts, the `progress()` and `log()` primitives are silenced automatically.

```
$ tool build --target all | cat   (stdout is a pipe → non-TTY)
→ no progress bars on stderr
→ no INFO-level log lines on stderr
→ only the JSON response on stdout
→ ERROR-level log lines still appear on stderr

$ CI=true tool build --target all
→ same suppression as non-TTY mode

$ tool build --target all   (interactive terminal)
→ progress bars and INFO logs appear normally on stderr

$ tool build --target all --verbose | cat
→ --verbose overrides auto-quiet; INFO logs are restored

$ infra --format json provision | cat   (provision declares stderr: "child_log")
→ ansible-playbook's log streams to stderr line by line despite auto-quiet
→ only the JSON response on stdout

$ infra --format json --quiet provision | cat
→ zero bytes on stderr
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-interactive mode detection reused to trigger auto-quiet |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: this requirement governs what is emitted on stderr in non-TTY mode |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Composes: ANSI color suppression also activates in non-TTY contexts |
| [REQ-F-029](f-029-auto-update-suppression-in-non-interactive-mode.md) | F | Composes: auto-update suppression applies the same non-TTY detection |
| [REQ-O-008](o-008-quiet-verbose-debug-verbosity-flags.md) | O | Composes: `--quiet` silences a declared child log too |
| [REQ-C-031](c-031-passthrough-commands-delegate-to-another-parser.md) | C | Composes: a passthrough command never declares `stderr: "child_log"` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `stderr` appears in the manifest |
