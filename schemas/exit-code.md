# Schema: ExitCode

**File:** [`exit-code.json`](exit-code.json)

> **Used by:** [REQ-F-001](../requirements/f-001-standard-exit-code-table.md) · [REQ-C-001](../requirements/c-001-command-declares-exit-codes.md) · [REQ-C-013](../requirements/c-013-error-responses-include-code-and-message.md) · [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md)

---

## Purpose

Most CLI tools use only `0` (success) and `1` (failure), forcing agents to parse error messages to understand what went wrong and whether retrying is safe. `ExitCode` replaces this with a fixed table where every code carries two machine-readable guarantees: whether the operation is **retryable** and how far **side effects** progressed. An agent can decide its next action from the exit code alone.

`retryable` answers exactly one question: may the agent re-run the identical invocation, unchanged, with a chance of success? `yes` additionally guarantees no side effects occurred. Conditions the caller must correct first are marked *after fix* and surface in the envelope as `retryable: false` with `fix_required` (or `error.redirect`) present.

Codes are sequential and grouped by category. The group boundaries are visible in this table — they are not encoded in the number itself.

---

## Values

### Success

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 0 | `SUCCESS` | — | complete | Done |

### Execution — operation ran, something went wrong internally

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 1 | `GENERAL_ERROR` | depends | unknown | Inspect `error.detail` — last resort, use a specific code whenever one exists |
| 3 | `PARTIAL_FAILURE` | no | **partial** | Inspect state before retrying — some writes occurred |

### Input — caller's fault; fix the input, then reissue

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 2 | `ARG_ERROR` | after fix* | **none** | Fix the input, then reissue — zero side effects guaranteed |
| 4 | `PRECONDITION` | after fix* | none | Resolve the precondition, then reissue |

### Resource — about the addressed entity

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 5 | `NOT_FOUND` | no | none | Stop, or create the resource first |
| 6 | `CONFLICT` | no | none | Resolve the conflict (delete, rename, or bump version) |

### Auth — identity and access

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 7 | `PERMISSION_DENIED` | no | none | Stop — valid credentials, wrong permissions; escalate or change approach |
| 8 | `AUTH_REQUIRED` | after fix* | none | Read `error.code`: `TOKEN_EXPIRED` → auto-refresh, then reissue; `TOKEN_MISSING` / `TOKEN_INVALID` → acquire credentials |
| 9 | `PAYMENT_REQUIRED` | after fix* | none | Attempt x402 payment if agent has payment permission, then reissue |

### Infrastructure — external systems

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 10 | `TIMEOUT` | depends | partial | Inspect state before retrying; retry directly only when the command declares `side_effects: "none"` |
| 11 | `RATE_LIMITED` | yes | none | Retry after `error.retry_after_ms` milliseconds |
| 12 | `UNAVAILABLE` | yes | none | Service temporarily down — apply exponential back-off, retry |

### Routing — API surface changed

| Code | Constant | Retryable | Side effects | Agent action |
|------|----------|-----------|--------------|-------------|
| 13 | `REDIRECTED` | after fix* | none | Use `error.redirect.command` verbatim; if `error.redirect.permanent` is true, memorize — never call the old form again |

\* *after fix*: the identical invocation fails until the caller corrects the stated condition, then reissues. Declared as `retryable: false` in `ExitCodeEntry`; the envelope carries `fix_required` (or `error.redirect`) with the correction.

**Reserved ranges:**
- `14–63` framework extensions
- `64–78` POSIX sysexits compatibility (optional mapping)
- `79–125` command-specific (declare per REQ-C-001)
- `126–255` shell-reserved — MUST NOT use

---

## Examples

**Valid**
```json
0
3
11
```

**Invalid — and why**

```json
1
```
Violation: `GENERAL_ERROR` is a last resort. If the condition matches any specific code (3–13), use that code instead.

```json
14
```
Violation: code `14` is in the framework extensions range (`14–63`) — reserved for future use. Commands must not emit it.

```json
130
```
Violation: shell-reserved (`128 + SIGINT`). Codes `126–255` MUST NOT be used by framework commands.

---

## Common mistakes

- **Using `GENERAL_ERROR (1)` as the default.** Every condition that maps to a specific code must use that code. `GENERAL_ERROR` should be rare

- **Emitting `ARG_ERROR (2)` after a side effect.** Code `2` carries a hard guarantee of zero side effects. If any write occurred before the error, emit `PARTIAL_FAILURE (3)` instead. The framework phase boundary (validate → execute) makes this automatic — do not bypass it

- **Treating `AUTH_REQUIRED (8)` as terminal.** The identical call fails until credentials are fixed (`retryable: false`), but the condition is correctable: read `error.code`, resolve it, reissue. An agent that gives up on auto-refreshable token expiry wastes the task

- **Confusing `PERMISSION_DENIED (7)` and `AUTH_REQUIRED (8)`.** `PERMISSION_DENIED` means the credentials are valid but insufficient — retrying with the same credentials will never succeed. `AUTH_REQUIRED` means the credentials themselves are the problem

- **Treating all `TIMEOUT (10)` exits as non-retryable.** For idempotent commands or read-only operations that time out without side effects, declare `retryable: true, side_effects: "none"` in `ExitCodeEntry`. Only declare `retryable: false` when partial writes may have occurred — the `ExitCodeEntry` invariant requires it when `side_effects` is `"partial"`

---

## Agent interpretation

Rules for agents consuming exit codes at runtime. Apply these when the response is ambiguous, contradictory, or outside the known table.

**Unknown code received**
- Code in `14–63` — framework extension; treat as `GENERAL_ERROR (1)` behavior: inspect `error.detail`, do not assume retryability
- Code in `64–78` — POSIX sysexit; look up the POSIX meaning; treat as non-retryable unless the meaning clearly indicates a transient condition
- Code in `79–125` — command-specific; consult that command's `exit_codes` declaration from the manifest before acting
- Code in `126–255` — shell signal or exec error; the command likely never ran; safe to retry after investigating the environment
- Code outside `0–255` — treat as `GENERAL_ERROR (1)`; log for investigation

**Contradictory signals**
- `ok: true` but exit code is non-zero — trust the exit code; discard `ok`
- `ok: false` but exit code is `0` — treat as success; `ok` field is derived and may be stale in proxied responses
- Exit code says retryable but `error.retryable: false` — trust `error.retryable`; it is the more specific signal

**Retry budget**
- Codes marked retryable do not imply infinite retries — apply a retry budget (e.g. 3 attempts) before escalating
- Codes marked *after fix* — apply the fix stated in `error.fix_required` (or `error.redirect`), reissue once; if no fix is stated, treat as terminal
- `RATE_LIMITED (11)` without `error.retry_after_ms` — default to 60 seconds before retrying
- `UNAVAILABLE (12)` — use exponential back-off starting at 1s, cap at 5 minutes

**Side effects under uncertainty**
- Code is `GENERAL_ERROR (1)` (side effects unknown) — treat as `side_effects: "partial"`; inspect state before retrying
- Code is `TIMEOUT (10)` — partial side effects are possible; do not assume the operation is idempotent without checking

---

## Coding agent notes

**Reading `exit-code.json` vendor extensions**
- `x-enum-varnames`: array of constant names parallel to `enum` values — use to generate the enum type (e.g. `ExitCode.SUCCESS = 0`)
- `x-enum-descriptions`: array of descriptions parallel to `enum` values — use as docstrings on each enum member
- `x-groups`: map of group name → list of codes — use to generate helper predicates (e.g. `ExitCode.is_auth(code)`)
- `x-code-ranges`: documentation of reserved ranges — validate against these ranges at registration

**Type representation**
- Generate `ExitCode` as an enum type, not integer constants — the type system must reject bare literals at the call site, not just at runtime
- The enum must be serializable to its integer value for JSON output and process exit; do not serialize the name string

**Validation to generate**
- A registration-time check that rejects any `ExitCode` value outside the declared enum members
- A runtime check in dev/test mode that intercepts `process.exit` / `sys.exit` and asserts the code matches the command's declared set

**Tests to generate**
- For each code: a test that emits the code and asserts the correct integer reaches the process exit
- A negative test: emitting a literal integer (e.g. `5`) at a call site that only accepts `ExitCode` must fail at compile/type-check time, not at runtime
- A test that `ARG_ERROR (2)` is only emitted before any mock side-effect function is called

**Anti-patterns**
- Do not generate `if code == 7` comparisons — always compare against `ExitCode.PERMISSION_DENIED`
- Do not generate a fallback `except: exit(1)` — map every known exception to a specific `ExitCode`
- Do not expose a method that accepts `int` where `ExitCode` is expected

---

## Implementation notes

- Represent as a named constant / enum — never a bare integer at call sites. The framework must reject literal integers at command registration
- `retryable` and `side_effects` values in this table describe the *default* agent behavior when no per-command `ExitCodeEntry` is available. When a command's manifest or `--schema` output includes an `ExitCodeEntry` for the received code, that entry takes precedence — the command may declare a code as non-retryable even if this table marks it retryable (e.g. `TIMEOUT` with partial side effects)
- The hard invariants that commands may not relax: `ARG_ERROR (2)` is always `side_effects: none`; `PARTIAL_FAILURE (3)` is always `retryable: false`; `SUCCESS (0)` is the only code with `side_effects: complete`
- `ARG_ERROR (2)` requires a hard phase boundary between validation and execution. No side effect may begin before this code can be emitted
- `AUTH_REQUIRED (8)` intentionally does not distinguish expired from invalid at the exit code level. The distinction is in `error.code` in the JSON payload — a more controlled channel. See [`response-envelope.json`](response-envelope.json) `ErrorDetail.code` values: `TOKEN_EXPIRED`, `TOKEN_INVALID`, `TOKEN_MISSING`
- `REDIRECTED (13)` requires the `error.redirect` field in the response. See [`response-envelope.json`](response-envelope.json) `Redirect` definition
