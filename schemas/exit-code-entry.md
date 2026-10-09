# Schema: ExitCodeEntry

**File:** [`exit-code-entry.json`](exit-code-entry.json)

> **Used by:** [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) · [REQ-C-028](../requirements/c-028-already-exists-response-pattern.md) · [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) · [REQ-C-036](../requirements/c-036-person-only-commands-declare-requires-person.md)

---

## Purpose

`ExitCodeEntry` is the per-code declaration a command makes at registration time. It is the contract an agent reads — before calling the command — to pre-plan retry and rollback strategies without waiting for a failure to occur. The map key identifies which code; each entry answers: what is the human-readable name, what happened to system state, may the identical call be re-run unchanged, and which `error.code` values can the response carry?

---

## Values

The integer exit code is the **map key**, not a field inside the entry. Each entry describes the value at that key.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no† | Named constant for this code (e.g. `"ARG_ERROR"`). For framework codes `0–14`: derived from `ExitCode` enum if omitted. For command-specific codes `79–125`: must be provided — there is no enum to derive from |
| `description` | string ≤ 120 | yes | Present-tense, agent-readable. What state is the system in? |
| `retryable` | boolean | yes | May the identical unchanged re-run succeed? `true` implies no side effects occurred |
| `side_effects` | `"none"` \| `"partial"` \| `"complete"` | yes | How much work was committed before this exit |
| `error_codes` | string[] (unique, each `^[A-Z][A-Z0-9_]+$`) | no | The `error.code` values the command emits under this exit, e.g. `["ALREADY_EXISTS"]` under `CONFLICT (6)`. Absent: not declared. `[]`: the exit carries no `error.code` |

† Required for command-specific codes (`79–125`); optional for framework codes (`0–14`) where the framework derives it from the `ExitCode` enum.

**Invariant (enforced by `if/then` in the schema):** `retryable: true` implies `side_effects: "none"`. Validate at registration, not at runtime.

---

## Examples

In all examples, the integer code is the surrounding map key; entries do not contain a `code` field.

**Valid — success (map key `"0"`)**
```json
{ "name": "SUCCESS", "description": "Deployment completed", "retryable": false, "side_effects": "complete" }
```

**Valid — input error, zero side effects, fix then reissue (map key `"2"`)**
```json
{ "name": "ARG_ERROR", "description": "Invalid target environment", "retryable": false, "side_effects": "none" }
```

**Valid — timeout declared as non-retryable because side effects are possible (map key `"10"`)**
```json
{ "name": "TIMEOUT", "description": "Deployment timed out — partial writes may have occurred", "retryable": false, "side_effects": "partial" }
```

**Valid — timeout declared as retryable because no writes were attempted (map key `"10"`)**
```json
{ "name": "TIMEOUT", "description": "Config read timed out — no writes were attempted", "retryable": true, "side_effects": "none" }
```

**Valid — read-only timeout declared as non-retryable because run length depends on the input (map key `"10"`)**
```json
{ "name": "TIMEOUT", "description": "Scan exceeded --timeout; the same input needs a larger --timeout", "retryable": false, "side_effects": "none" }
```
The identical re-run times out again, so `retryable` stays `false` though nothing was written; the error carries `error.fix_required` naming a larger `--timeout` ([REQ-C-014](../requirements/c-014-error-responses-include-retryable-and-retry-after-.md)).

**Valid — conflict exit that names its `error.code` (map key `"6"`)**
```json
{ "name": "CONFLICT", "description": "A resource with this name already exists; data holds it", "retryable": false, "side_effects": "none", "error_codes": ["ALREADY_EXISTS"] }
```
An agent learns from the manifest that exit `6` carries `error.code: "ALREADY_EXISTS"` and plans its create-or-get branch ([REQ-C-028](../requirements/c-028-already-exists-response-pattern.md)) before the first call.

**Invalid — lowercase `error.code` value**
```json
{ "name": "CONFLICT", "description": "A resource with this name already exists", "retryable": false, "side_effects": "none", "error_codes": ["already_exists"] }
```
Violation: each value must match `^[A-Z][A-Z0-9_]+$`, the pattern `ResponseEnvelope` puts on `error.code`, so a listed value is always one the envelope can carry.

**Invalid — invariant violation**
```json
{ "name": "TIMEOUT", "description": "Deployment timed out", "retryable": true, "side_effects": "partial" }
```
Violation: `retryable: true` with `side_effects: "partial"` violates the schema invariant. Use `retryable: false` or `side_effects: "none"`.

**Invalid — missing required fields**
```json
{ "name": "NOT_FOUND", "description": "Target not found" }
```
Violation: `retryable` and `side_effects` are required.

---

## Common mistakes

- **Omitting the `SUCCESS` entry (map key `"0"`).** Every command must declare it — even if the success path is obvious. The manifest and `--schema` output require it
- **Using vague descriptions like `"Error"` or `"Failed"`.** The description must state the condition specifically so an agent can act without reading message text
- **Setting `retryable: true` when side effects may have occurred.** The invariant is a hard guarantee. If any write could have occurred, `side_effects` must be `"partial"` and `retryable` must be `false`, even when rerunning is safe; declare that on the command as `idempotent: true` ([`manifest-response.md`](manifest-response.md))
- **Setting `retryable: true` on validation errors.** Safe is not the same as useful: the identical call fails deterministically until the input changes. Declare `retryable: false`; the envelope carries `fix_required` for the correction
- **Declaring `TIMEOUT` retryable because the command is read-only.** `side_effects: "none"` permits `retryable: true` but does not imply it. When run length depends on the input, the identical re-run times out again: declare `retryable: false, side_effects: "none"`, and the error carries `fix_required` naming a larger `--timeout`
- **Using `side_effects: "complete"` on failure codes.** `"complete"` means the intended operation finished — it is only appropriate for `SUCCESS (0)`
- **Declaring only the happy path.** Every code the command may emit must have an entry. An undeclared code emitted at runtime is a contract violation
- **Listing an `error.code` the command never emits under that exit.** `error_codes` is a promise about this exit only. A code emitted under a different exit belongs in that exit's entry, and a code the command never emits misleads the agent's branch planning
- **Writing `error_codes` in another case than the envelope.** `"already_exists"` fails the pattern; list the exact `error.code` string the envelope carries
- **Omitting `name` for command-specific codes (`79–125`).** For framework codes `0–14`, the framework can derive the constant name from the `ExitCode` enum. For command-specific codes, there is no enum — omitting `name` leaves agents with no readable label for the code

---

## Agent interpretation

Rules for agents reading `ExitCodeEntry` values from a command's `--schema` output or manifest before invoking the command.

**Using entries to plan retries**
- If an entry has `retryable: true` and `side_effects: "none"` — the identical call may be re-run directly; no state inspection needed
- If an entry has `retryable: true` and `side_effects: "partial"` — this is a schema violation (see invariant in **Values** above); treat conservatively as non-retryable until state is inspected
- If an entry has `retryable: false` and `side_effects: "partial"`, and the command's manifest entry declares `idempotent: true` — rerun the identical command once without inspecting state; it converges on the state a clean run leaves. A second failure with the same `error.code` is deterministic: stop and escalate
- The convergent rerun never applies to `ARG_ERROR (2)`, to an exit with `side_effects: "none"`, or to an error carrying `fix_required` or `fix_command`; those follow `retryable` and the fix fields. Without `idempotent: true`, inspect state before any rerun
- If no entry exists for the received exit code — the command violated its contract; treat as `GENERAL_ERROR` behavior

**Using `error_codes`**
- Branch on the received `error.code`, never on the list. `error_codes` tells the agent in advance which values it may meet under this exit, so it can plan a branch for each (e.g. `ALREADY_EXISTS` under `CONFLICT (6)`: read the existing resource from `data`)
- `error_codes` absent: the command does not declare them, including on any entry written before `ExitCodeEntry` 1.1. It never means "no `error.code`"; read `error.code` from the envelope as usual
- `error_codes: []`: this exit carries no `error.code`
- A received `error.code` missing from a declared list: the command broke its declaration; act on the received `error.code` and log a schema warning

**Contradiction in received data**
- `retryable: true` with `side_effects: "partial"` or `"complete"` — schema invariant violated by the command; do not retry without inspecting state
- `description` is absent or empty — fall back to the exit code's default description from [`exit-code.md`](exit-code.md)
- `name` is absent — for codes `0–14`, look up the constant name in [`exit-code.json`](exit-code.json) `x-enum-varnames` by index; for codes `79–125`, use the numeric code as a fallback label and log a schema warning

**Before invoking a command**
- Fetch the command's `exit_codes` map from the manifest once and cache it for the session
- Use `retryable` and `side_effects` values to pre-plan the retry/rollback strategy before the first call, not reactively after failure

---

## Coding agent notes

**Type representation**
- Generate `ExitCodeEntry` as an immutable value type (frozen dataclass, readonly interface, or struct) — entries are declared once at registration and must not be mutated at runtime
- The registration API must accept `ExitCode` enum values as map keys, not bare integers — the type system must reject `{5: {...}}` and require `{ExitCode.NOT_FOUND: {...}}`
- Keys are serialized to integer strings (`"5"`) in the wire format; the enum value is the source of truth at registration time

**Validation to generate**
- At registration: assert `retryable == true` implies `side_effects == "none"` — this is a hard invariant, not a soft warning
- At registration: assert the exit codes map is non-empty and includes key `"0"` (SUCCESS)
- In dev/test mode: intercept every process exit and assert the emitted code has a matching `ExitCodeEntry` in the command's declared set
- In dev/test mode: when the entry declares `error_codes`, assert the envelope's `error.code` is one of them (or absent when the list is empty)

**Tests to generate**
- A test that registering a command without `exit_codes` raises a framework error
- A test that registering an entry with `retryable: true, side_effects: "partial"` raises a validation error
- A test that emitting an undeclared exit code in dev mode produces a framework warning with the code value and command name

**Anti-patterns**
- Do not generate `ExitCodeEntry` with `description: "Error"` or `description: "Failed"` — descriptions must be specific enough for an agent to act on
- Do not generate a mutable `exit_codes` map that commands can add entries to after registration
- Do not skip the `SUCCESS` entry — it is required even if the success path is obvious
- Do not add properties beyond `name`, `description`, `retryable`, `side_effects`, `error_codes` — the schema uses `additionalProperties: false` and will reject unknown fields
- Do not maintain `error_codes` by hand apart from the code that raises the errors; derive the list from the same declaration the command raises from, so the two cannot drift
- Do not omit `name` for command-specific codes (`79–125`) — there is no enum to derive it from; the framework cannot fill it in

---

## Implementation notes

- `description` should answer: "Why did I exit here and what should the agent know about system state?" Avoid generic messages like "An error occurred."
- The full set of `ExitCodeEntry` objects for a command must cover every code that command may emit. Warn in development mode if an undeclared code is observed at runtime
- `error_codes` is optional; emit it when the command knows its `error.code` values for that exit. Omit it rather than emit a partial list, since an agent reads a present list as complete
