# Schema: ExitCodeEntry

**File:** [`exit-code-entry.json`](exit-code-entry.json)

> **Used by:** [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) · [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md)

---

## Purpose

`ExitCodeEntry` is the per-code declaration a command makes at registration time. It is the contract an agent reads — before calling the command — to pre-plan retry and rollback strategies without waiting for a failure to occur. The map key identifies which code; each entry answers: what is the human-readable name, what happened to system state, and may the identical call be re-run unchanged?

---

## Values

The integer exit code is the **map key**, not a field inside the entry. Each entry describes the value at that key.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no† | Named constant for this code (e.g. `"ARG_ERROR"`). For framework codes `0–13`: derived from `ExitCode` enum if omitted. For command-specific codes `79–125`: must be provided — there is no enum to derive from |
| `description` | string ≤ 120 | yes | Present-tense, agent-readable. What state is the system in? |
| `retryable` | boolean | yes | May the identical unchanged re-run succeed? `true` implies no side effects occurred |
| `side_effects` | `"none"` \| `"partial"` \| `"complete"` | yes | How much work was committed before this exit |

† Required for command-specific codes (`79–125`); optional for framework codes (`0–13`) where the framework derives it from the `ExitCode` enum.

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

**Valid — timeout declared as retryable because the command is idempotent (map key `"10"`)**
```json
{ "name": "TIMEOUT", "description": "Config read timed out — no writes were attempted", "retryable": true, "side_effects": "none" }
```

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
- **Setting `retryable: true` when side effects may have occurred.** The invariant is a hard guarantee. If any write could have occurred, `side_effects` must be `"partial"` and `retryable` must be `false`
- **Setting `retryable: true` on validation errors.** Safe is not the same as useful: the identical call fails deterministically until the input changes. Declare `retryable: false`; the envelope carries `fix_required` for the correction
- **Using `side_effects: "complete"` on failure codes.** `"complete"` means the intended operation finished — it is only appropriate for `SUCCESS (0)`
- **Declaring only the happy path.** Every code the command may emit must have an entry. An undeclared code emitted at runtime is a contract violation
- **Omitting `name` for command-specific codes (`79–125`).** For framework codes `0–13`, the framework can derive the constant name from the `ExitCode` enum. For command-specific codes, there is no enum — omitting `name` leaves agents with no readable label for the code

---

## Agent interpretation

Rules for agents reading `ExitCodeEntry` values from a command's `--schema` output or manifest before invoking the command.

**Using entries to plan retries**
- If an entry has `retryable: true` and `side_effects: "none"` — the identical call may be re-run directly; no state inspection needed
- If an entry has `retryable: true` and `side_effects: "partial"` — this is a schema violation (see invariant in **Values** above); treat conservatively as non-retryable until state is inspected
- If no entry exists for the received exit code — the command violated its contract; treat as `GENERAL_ERROR` behavior

**Contradiction in received data**
- `retryable: true` with `side_effects: "partial"` or `"complete"` — schema invariant violated by the command; do not retry without inspecting state
- `description` is absent or empty — fall back to the exit code's default description from [`exit-code.md`](exit-code.md)
- `name` is absent — for codes `0–13`, look up the constant name in [`exit-code.json`](exit-code.json) `x-enum-varnames` by index; for codes `79–125`, use the numeric code as a fallback label and log a schema warning

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

**Tests to generate**
- A test that registering a command without `exit_codes` raises a framework error
- A test that registering an entry with `retryable: true, side_effects: "partial"` raises a validation error
- A test that emitting an undeclared exit code in dev mode produces a framework warning with the code value and command name

**Anti-patterns**
- Do not generate `ExitCodeEntry` with `description: "Error"` or `description: "Failed"` — descriptions must be specific enough for an agent to act on
- Do not generate a mutable `exit_codes` map that commands can add entries to after registration
- Do not skip the `SUCCESS` entry — it is required even if the success path is obvious
- Do not add properties beyond `name`, `description`, `retryable`, `side_effects` — the schema uses `additionalProperties: false` and will reject unknown fields
- Do not omit `name` for command-specific codes (`79–125`) — there is no enum to derive it from; the framework cannot fill it in

---

## Implementation notes

- `description` should answer: "Why did I exit here and what should the agent know about system state?" Avoid generic messages like "An error occurred."
- The full set of `ExitCodeEntry` objects for a command must cover every code that command may emit. Warn in development mode if an undeclared code is observed at runtime
