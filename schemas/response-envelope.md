# Schema: ResponseEnvelope

**File:** [`response-envelope.json`](response-envelope.json)

> **Used by:** [REQ-F-004](../requirements/f-004-consistent-json-response-envelope.md) · [REQ-C-013](../requirements/c-013-error-responses-include-code-and-message.md) · [REQ-C-014](../requirements/c-014-error-responses-include-retryable-and-retry-after-.md) · [REQ-C-030](../requirements/c-030-error-responses-include-fix-command.md) · [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) · all commands in JSON output mode

Shape is invariant — `ok`, `data`, `error`, `warnings`, `meta` are always present regardless of success, failure, or result count.

---

## ResponseEnvelope

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Derived from exit code. `true` iff exit code is `SUCCESS (0)`. Never set by command logic |
| `data` | object \| array \| null | Primary output. `null` on failure, never absent |
| `error` | `ErrorDetail` \| null | `null` on success |
| `warnings` | string[] | Non-fatal messages. May be empty, never null |
| `meta` | `ResponseMeta` | Always present |
---

## ErrorDetail

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | yes | Stable machine-readable identifier. Agents branch on this, not `message`. Never changes between versions |
| `message` | string | yes | Human-readable summary. May be localized. Do not parse — use `code` |
| `detail` | string | no | Stack context or raw upstream error |
| `retryable` | boolean | no | `true` = the identical unchanged invocation may succeed and no side effects occurred. Mirrors `ExitCodeEntry.retryable` for the emitted exit code |
| `retry_after_ms` | integer | no | Milliseconds to wait before retrying. Only when `retryable: true` and back-off is known |
| `retry_strategy` | `"immediate"` \| `"linear_backoff"` \| `"exponential_backoff"` | no | Back-off strategy to apply. Only when `retryable: true` |
| `fix_required` | string | no | Condition the caller must correct before reissuing. Only when `retryable: false` and the failure is caller-correctable; absent on terminal failures |
| `fix_command` | string | no | Exact command that resolves `fix_required`, executable verbatim (no placeholders). Read-only or idempotent, never destructive. Only when a single-command remediation exists |
| `phase` | `"validation"` \| `"execution"` \| `"cleanup"` | no | `"validation"` guarantees zero side effects |
| `suggestion` | string | no | Actionable next step for the agent |
| `redirect` | `Redirect` | no | Present only when exit code is `REDIRECTED (13)` |
### error.code values for AUTH_REQUIRED (8)

The exit code intentionally does not distinguish why auth failed — that detail is in `error.code`:

| error.code | Meaning | Agent action |
|------------|---------|-------------|
| `TOKEN_EXPIRED` | Valid token, past expiry | Auto-refresh using refresh token, retry immediately |
| `TOKEN_INVALID` | Malformed or revoked token | Acquire new credentials |
| `TOKEN_MISSING` | No credentials provided | Acquire credentials |

---

## Redirect

Present in `error.redirect` when exit code is `REDIRECTED (13)`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | yes | Exact replacement invocation. Agent uses this verbatim on retry |
| `permanent` | boolean | yes | `true` → memorize, never call the old form again. `false` → use replacement for this request only |
| `reason` | string | no | `"renamed"` \| `"restructured"` \| `"deprecated"` \| `"typo_corrected"` |

---

## ResponseMeta

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `duration_ms` | integer | yes | Wall-clock ms from entry to last byte |
| `request_id` | string | no | Correlation ID for logs and traces |
| `schema_version` | string | no | Envelope schema version e.g. `"1.0"` |
| `not_modified` | boolean | no | `true` on etag cache hit — `data` will be `null` |
| `truncated` | boolean | no | Output was capped. Agent should paginate or narrow the query |
| `cursor` | string | no | Pass as `--cursor` to get the next page |
---

## Examples

**Success**
```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": { "duration_ms": 340, "request_id": "req_abc123" }
}
```

**ARG_ERROR (2) — fix the input, then reissue; zero side effects**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INVALID_ENVIRONMENT",
    "message": "Unknown target environment 'prodution'",
    "retryable": false,
    "fix_required": "Correct the target environment argument",
    "phase": "validation",
    "suggestion": "Valid environments: prod, staging, dev"
  },
  "warnings": [],
  "meta": { "duration_ms": 5 }
}
```

**AUTH_REQUIRED (8) — token expired, agent can auto-refresh**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Access token has expired",
    "retryable": false,
    "fix_required": "Refresh the access token, then reissue the call",
    "fix_command": "tool auth refresh"
  },
  "warnings": [],
  "meta": { "duration_ms": 4 }
}
```

**REDIRECTED (13) — permanent rename, agent must memorize**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "COMMAND_RENAMED",
    "message": "'tool user create' was renamed in v2.0",
    "retryable": false,
    "fix_required": "Reissue using error.redirect.command verbatim",
    "redirect": {
      "command": "tool users add --name alice",
      "permanent": true,
      "reason": "renamed"
    }
  },
  "warnings": [],
  "meta": { "duration_ms": 2 }
}
```

**RATE_LIMITED (11) — retry after**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit reached",
    "retryable": true,
    "retry_after_ms": 30000
  },
  "warnings": [],
  "meta": { "duration_ms": 6 }
}
```

---

## Agent interpretation

Rules for agents parsing `ResponseEnvelope` at runtime, including handling malformed, contradictory, or incomplete responses.

**Determining outcome**
- Primary signal: exit code. Secondary signal: `ok`. If they conflict, trust exit code
- `ok: true` + non-zero exit code — command proxy or wrapper may have swallowed the code; treat as failure, inspect `error`
- `ok: false` + exit code `0` — treat as success; `ok` may be stale in a cached or proxied response

**Missing or null fields**
- `error` key absent entirely — malformed response; treat as `GENERAL_ERROR`; do not retry blindly
- `data: null` and `error: null` simultaneously — malformed; log and escalate; do not act on `data`
- `warnings` key absent — treat as empty array; do not fail

**Deciding whether to act on `data`**
- `meta.truncated: true` — `data` is incomplete; do not draw conclusions or trigger downstream actions until all pages are fetched
- `meta.not_modified: true` — `data` is intentionally `null`; use the previously cached response; this is not an error

**Retrying**
- `error.retryable: true` without `error.retry_after_ms` — apply a 1s default back-off before retrying
- `error.retryable: false` with `error.fix_required` or `error.redirect` present — apply the stated fix, then reissue once; with neither, treat as terminal and stop
- `error.fix_command` present — run it verbatim (it is declared safe: read-only or idempotent), then reissue the original call once; if either step fails, stop and escalate
- `error.retryable` absent — fall back to the exit code's retryability from [`exit-code.md`](exit-code.md)
- Never retry more than 3 times on the same error code without a state change

**Auth flow**
- `error.code: "TOKEN_EXPIRED"` — refresh token, replace credential, retry the original call once; if the retry also returns `TOKEN_EXPIRED`, escalate to `TOKEN_INVALID` handling
- `error.code: "TOKEN_INVALID"` or `"TOKEN_MISSING"` — do not retry; acquire new credentials from the appropriate source

**Redirect flow**
- `error.redirect` present — execute `error.redirect.command` verbatim on the next call; do not modify it
- `error.redirect.permanent: true` — record the mapping (old command → new command) before retrying; apply it to all future calls in this session and persist to memory
- `error.redirect.permanent: false` — use replacement for this call only; do not update stored knowledge

**Warnings**
- Non-empty `warnings` on a successful response — log all warnings; complete the current action; surface warnings to the orchestrator for review
- A warning containing words like "deprecated" or "will be removed" — treat as a soft `REDIRECTED`; plan to update the call in a future session

## Coding agent notes

**Type representation**
- Generate `ResponseEnvelope<T>` as a generic type where `T` is the command's declared output schema — do not use `any` or `object` for `data`
- `ok` must be a derived/computed field, not a settable field — generate it as a property that reads the exit code, not as a constructor parameter

**Construction**
- Generate a single `respond()` / `envelope()` factory function that the framework calls after the command handler returns — command handlers must never construct the envelope directly
- The factory derives `ok` from the exit code, sets `meta.duration_ms` from a start timer, and validates that `error` is non-null whenever exit code is non-zero

**Validation to generate**
- A schema validator that runs on every envelope in test mode and asserts all five required fields are present and non-absent
- An assertion that `ok == (exit_code == 0)` — any divergence is a framework bug
- An assertion that `data` and `error` are not both null simultaneously (unless `meta.not_modified: true`)

**Tests to generate**
- Success path: `ok: true`, `data` matches declared output schema, `error: null`
- Failure path: `ok: false`, `data: null`, `error` has `code` and `message`
- Truncation path: `meta.truncated: true` present when output exceeds size limit
- Cache hit path: `meta.not_modified: true`, `data: null`, `error: null`, exit code `0`
- For `REDIRECTED (13)`: `error.redirect` is present with both `command` and `permanent`

**Anti-patterns**
- Do not let command handlers set `ok` directly — it must be derived
- Do not omit `data` on failure or `error` on success — both keys must always be present
- Do not generate separate envelope shapes for success and failure — the shape is invariant

## Implementation notes

- `ok` must be derived from the process exit code, not set by command logic. Prevents a command exiting non-zero with `ok: true`
- `data` must always be present as a key — use `null` rather than omitting it
- `error` must always be present as a key — use `null` rather than omitting it
- `ResponseMeta` uses `additionalProperties: true` to allow framework extensions without breaking existing parsers
- `ErrorDetail` uses `additionalProperties: true` for the same reason — requirements extend it with fields such as `refresh_command` (REQ-F-063) and network context (REQ-F-037)
- `error.redirect` is only meaningful when the exit code is `REDIRECTED (13)`. Parsers should ignore it at other exit codes
- `error.code` is the stable identifier agents act on. `error.message` is for humans and may change between versions
