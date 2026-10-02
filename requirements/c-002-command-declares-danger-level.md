# REQ-C-002: Command Declares Danger Level

**Tier:** Command Contract | **Priority:** P0

**Source:** [§23 Side Effects & Destructive Operations](../challenges/03-critical-security/23-critical-destructive-ops.md) · [§12 Idempotency & Safe Retries](../challenges/02-critical-execution-and-reliability/12-critical-idempotency.md)

**Addresses:** Severity: Critical / Token Spend: Medium / Time: High / Context: Medium

---

## Description

Every command MUST declare a `danger_level` as part of its registration metadata, chosen from: `safe` (read-only, no side effects on state), `mutating` (creates or modifies state), or `destructive` (permanently deletes or irreversibly modifies state). The framework MUST refuse to register a command without this declaration. The framework MUST use this declaration to enforce related behaviors (e.g., requiring `--dry-run` for destructive commands per REQ-C-004). A streaming command (REQ-O-004) MUST NOT declare `destructive`, and the framework refuses to register one that does.

Writes of declared `cache`, `log`, `temp`, and `output` paths (REQ-C-011) are not state changes: a command whose only writes are of those kinds stays `safe`. A report generator that writes its product to a declared `output` path is `safe`, not `mutating`. Writing a `credential` or `config` path, or any undeclared path, is a state change.

A command MAY also declare `idempotent: true`: a repeat with the same arguments converges on the same state, whatever a previous attempt left behind. A rewrite of one snapshot file per server, a `PUT` of a full resource, and a delete of a named resource (`danger_level: "destructive"`) all qualify; an append, a counter increment, and a message send do not. Absent means `false`. The declaration does not change any `ExitCodeEntry`: an exit after some writes stays `retryable: false` with `side_effects: "partial"`, because `retryable: true` still guarantees that nothing was written (REQ-C-001). What it adds is an agent rule: on a non-retryable exit whose entry declares `side_effects: "partial"`, rerunning the identical command is the recovery, without inspecting state first. The rule never covers `ARG_ERROR (2)` or an error that carries `fix_required` or `fix_command`, which fail until the caller changes something. `idempotent` on a `safe` command is redundant (a read-only command converges trivially) and the framework accepts it without warning.

`idempotent` is distinct from `--idempotency-key` ([REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md)), which deduplicates one request so that its repeat does nothing and returns `effect: "noop"` ([REQ-C-003](c-003-mutating-commands-declare-effect-field.md)). A command can deduplicate without converging (each new key creates another order) and converge without deduplicating (each rerun rewrites the same files); declaring `idempotent` does not exempt a mutating command from accepting `--idempotency-key`.

## Acceptance Criteria

- Attempting to register a command without `danger_level` raises a framework error
- The `--schema` output for every command includes `danger_level`
- Commands with `danger_level: "destructive"` trigger framework-level dry-run enforcement (REQ-C-004)
- Commands with `danger_level: "safe"` do not require `--idempotency-key` (REQ-C-007)
- Commands with `danger_level: "mutating"` require `--idempotency-key` unless they stream, and a streaming one that accepts it raises a registration error (REQ-C-007)
- Registering a streaming command with `danger_level: "destructive"` raises a framework error (REQ-O-004)
- A command whose only declared filesystem writes are `cache`, `log`, `temp`, or `output` paths may register as `safe`
- A command registered with `idempotent: true` shows `"idempotent": true` in `--schema` output and the manifest; a command registered without it omits the field or shows `false`
- Registering `idempotent: true` with any `danger_level`, including `safe` and `destructive`, succeeds and leaves every declared `ExitCodeEntry` unchanged
- For a command declared `idempotent: true`, a rerun of the identical invocation after each declared exit with `side_effects: "partial"` exits `0` and leaves the state a single clean run leaves

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

The `danger_level` field appears on every command entry in `--schema` output and in the manifest. Allowed values: `"safe"` · `"mutating"` · `"destructive"`. The optional `idempotent` field appears when the command declares it; absent means `false`.

```json
{
  "danger_level": {
    "type": "string",
    "enum": ["safe", "mutating", "destructive"],
    "description": "Indicates the mutation risk level of the command"
  },
  "idempotent": {
    "type": "boolean",
    "default": false,
    "description": "A repeat with the same arguments converges on the same state, whatever a previous attempt left behind"
  }
}
```

---

## Wire Format

```bash
$ tool delete-account --schema
```

```json
{
  "command": "delete-account",
  "danger_level": "destructive",
  "reversible": false,
  "requires_confirmation": true,
  "flags": {
    "user": { "type": "integer", "required": true, "description": "User ID to delete" },
    "dry-run": { "type": "boolean", "required": false, "default": false, "description": "Validate without deleting" }
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "User account deleted",    "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Invalid user ID",         "retryable": false, "side_effects": "none"     },
    "5": { "name": "NOT_FOUND", "description": "User not found",          "retryable": false, "side_effects": "none"     }
  }
}
```

---

## Example

A command declares its danger level at registration time. The framework uses this declaration to enforce related behaviors automatically.

```
register command "delete-account":
  danger_level: destructive
  exit_codes:
    SUCCESS (0): description: "User account deleted", retryable: false, side_effects: complete
    NOT_FOUND(5): description: "User not found",      retryable: false, side_effects: none

register command "list-users":
  danger_level: safe
  exit_codes:
    SUCCESS(0): description: "User list returned", retryable: false, side_effects: none

register command "observe":
  danger_level: mutating
  idempotent: true
  exit_codes:
    SUCCESS        (0): description: "Every snapshot file is rewritten",                    retryable: false, side_effects: complete
    PARTIAL_FAILURE(3): description: "Some snapshot files are rewritten and others are not", retryable: false, side_effects: partial
  → after exit 3, the agent reruns "tool observe" unchanged; no state inspection first

register command "update-email":
  (no danger_level)
  → framework error: danger_level declaration is required
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-001](c-001-command-declares-exit-codes.md) | C | Composes: `danger_level` and `idempotent` are part of the same `--schema` output as `exit_codes`; `idempotent` leaves the `retryable` ⇒ `side_effects: "none"` invariant unchanged |
| [REQ-C-003](c-003-mutating-commands-declare-effect-field.md) | C | Extends: `danger_level: mutating/destructive` triggers `effect` field requirement |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | C | Enforces: `danger_level: destructive` requires `--dry-run` support |
| [REQ-C-007](c-007-mutating-commands-accept-idempotency-key.md) | C | Enforces: `danger_level: mutating/destructive` requires `--idempotency-key` on every non-streaming command, which `idempotent` does not replace |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Enforces: a streaming command is never `destructive` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Aggregates: manifest exposes `danger_level` for every registered command |
