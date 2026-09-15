# Schema: ResponseEnvelope

**File:** [`response-envelope.json`](response-envelope.json)

> **Used by:** [REQ-F-004](../requirements/f-004-consistent-json-response-envelope.md) · [REQ-F-018](../requirements/f-018-pagination-metadata-on-list-commands.md) · [REQ-C-009](../requirements/c-009-multi-step-commands-report-completed-failed-skippe.md) · [REQ-C-013](../requirements/c-013-error-responses-include-code-and-message.md) · [REQ-C-014](../requirements/c-014-error-responses-include-retryable-and-retry-after-.md) · [REQ-C-028](../requirements/c-028-already-exists-response-pattern.md) · [REQ-C-030](../requirements/c-030-error-responses-include-fix-command.md) · [REQ-O-041](../requirements/o-041-tool-manifest-built-in-command.md) · [REQ-O-050](../requirements/o-050-tool-exec-built-in-command.md) · all commands in JSON output mode

---

## Purpose

Every command in JSON mode writes exactly one `ResponseEnvelope` to stdout. The shape is invariant: `ok`, `data`, `error`, `warnings`, and `meta` are always present regardless of success, failure, or result count, so an agent parses one structure for every command.

Three design decisions shape the type:

- **Self-describing outcome.** `meta.exit_code` repeats the process exit code. Pipelines (§56), wrappers, and log collectors routinely lose the real exit code; an agent holding only stdout can still classify the result
- **Codes, never prose.** Errors and warnings both carry a stable `code` plus structured `context`. Agents branch on codes; `message` is for humans and may be localized
- **One place per concern.** Pagination lives in `meta.pagination`, byte-cap truncation in `meta.truncated`, exec correlation in `meta._cmd` and `meta._line`. The five top-level keys never change

---

## ResponseEnvelope

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | `true` iff `meta.exit_code` is `0`. Derived, never set by command logic |
| `data` | object \| array \| null | Primary output on success. On failure, `null` unless the command declares a failure payload: partial results (REQ-C-009), the conflicting resource (REQ-C-028), or a failed check report (REQ-O-026). Never absent |
| `error` | `ErrorDetail` \| null | `null` when `meta.exit_code` is `0`; an `ErrorDetail` otherwise |
| `warnings` | `WarningDetail[]` | Non-fatal diagnostics. May be empty, never null |
| `meta` | `ResponseMeta` | Always present |

---

## ErrorDetail

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | yes | Stable domain identifier matching `^[A-Z][A-Z0-9_]+$`. May equal an `ExitCode` name (`NOT_FOUND`) or be more specific (`TOKEN_EXPIRED`). Agents branch on this, not `message` |
| `message` | string | yes | Human-readable summary. May be localized. Do not parse |
| `detail` | string | no | Extended explanation or raw upstream error text |
| `cause` | string | no | Underlying system error, such as `Connection refused (ECONNREFUSED)` |
| `context` | object | no | Structured facts about the failure: host, port, missing scopes, affected ids |
| `docs_url` | string | no | Documentation for this error code |
| `retryable` | boolean | no | `true` = the identical unchanged invocation may succeed and no side effects occurred. Mirrors `ExitCodeEntry.retryable` for the emitted exit code |
| `retry_after_ms` | integer | no | Milliseconds to wait before retrying. Only when `retryable: true` and back-off is known |
| `retry_strategy` | `"immediate"` \| `"linear_backoff"` \| `"exponential_backoff"` | no | Back-off strategy to apply. Only when `retryable: true` |
| `fix_required` | string | no | Condition the caller must correct before reissuing. Only when `retryable: false` and the failure is caller-correctable |
| `fix_command` | string | no | Exact command that resolves `fix_required`, executable verbatim. Read-only or idempotent, never destructive |
| `phase` | `"validation"` \| `"execution"` \| `"cleanup"` | no | `"validation"` guarantees zero side effects |
| `suggestion` | string | no | Actionable next step for the agent |
| `redirect` | `Redirect` | no | Present only when exit code is `REDIRECTED (13)` |

`ErrorDetail` allows additional properties; requirements extend it with fields such as `network_context` (REQ-F-037) and `corrected_input` (REQ-F-059).

### error.code values for AUTH_REQUIRED (8)

The exit code intentionally does not distinguish why auth failed; that detail is in `error.code`:

| error.code | Meaning | Agent action |
|------------|---------|-------------|
| `TOKEN_EXPIRED` | Valid token, past expiry | Auto-refresh using refresh token, retry immediately |
| `TOKEN_INVALID` | Malformed or revoked token | Acquire new credentials |
| `TOKEN_MISSING` | No credentials provided | Acquire credentials |

---

## WarningDetail

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | yes | Stable identifier matching `^[A-Z][A-Z0-9_]+$`, such as `DEPRECATED_FLAG` or `FIELD_TRUNCATED` |
| `message` | string | yes | Human-readable summary. Do not parse |
| `context` | object | no | Structured facts: field path, byte counts, versions, intercepted text |

Standard warning codes defined by requirements: `THIRD_PARTY_STDOUT` (REQ-F-060), `FIELD_TRUNCATED` (REQ-F-064), `GLOBAL_CONFIG_MODIFIED` (REQ-C-025), `SCHEMA_DEPRECATED` (REQ-O-014), `CREDENTIAL_OVER_PRIVILEGED` (REQ-O-047).

---

## Redirect

Present in `error.redirect` when exit code is `REDIRECTED (13)`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | yes | Exact replacement invocation. Agent uses this verbatim on retry |
| `permanent` | boolean | yes | `true`: memorize, never call the old form again. `false`: use replacement for this request only |
| `reason` | string | no | `"renamed"` \| `"restructured"` \| `"deprecated"` \| `"typo_corrected"` |

---

## ResponseMeta

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `exit_code` | integer `0–255` | yes | Process exit code of this invocation, identical to the code the process returns |
| `duration_ms` | integer | yes | Wall-clock ms from entry to last byte |
| `request_id` | string | no | Correlation ID for logs and traces |
| `schema_version` | string `MAJOR.MINOR` | no | Version of this command's output contract (REQ-F-022) |
| `not_modified` | boolean | no | `true` on etag cache hit; `data` is `null` |
| `truncated` | boolean | no | The framework byte cap cut the output (REQ-F-052). Narrow the query or paginate |
| `pagination` | `Pagination` | list commands | Present on every list response, including complete result sets (REQ-F-018) |
| `_cmd` | string | exec only | Dispatched command path echoed from the request (REQ-O-050) |
| `_line` | integer | exec only | 1-based input line this response answers (REQ-O-050) |

`ResponseMeta` allows additional properties for framework extensions such as `retries` (REQ-F-078) and `dry_run` (REQ-O-048).

### Pagination

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total` | integer \| null | yes | Items across all pages, or `null` when uncountable |
| `returned` | integer | yes | Items in this response |
| `truncated` | boolean | yes | A limit cut the result set short |
| `has_more` | boolean | yes | At least one further page exists |
| `next_cursor` | string \| null | yes | Pass as `--cursor` for the next page; `null` when `has_more` is `false` |

---

## Examples

**Success**
```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 340, "request_id": "req_abc123" }
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
  "meta": { "exit_code": 2, "duration_ms": 5 }
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
  "meta": { "exit_code": 8, "duration_ms": 4 }
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
  "meta": { "exit_code": 13, "duration_ms": 2 }
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
  "meta": { "exit_code": 11, "duration_ms": 6 }
}
```

---

**List page with a warning**
```json
{
  "ok": true,
  "data": [{ "id": "d1" }, { "id": "d2" }],
  "error": null,
  "warnings": [
    { "code": "DEPRECATED_FLAG", "message": "--page-size is deprecated; use --limit", "context": { "flag": "--page-size", "replacement": "--limit" } }
  ],
  "meta": {
    "exit_code": 0,
    "duration_ms": 55,
    "pagination": { "total": 47, "returned": 2, "truncated": true, "has_more": true, "next_cursor": "eyJwYWdlIjoyfQ" }
  }
}
```

**PARTIAL_FAILURE (3) — failure payload in `data`**
```json
{
  "ok": false,
  "data": { "partial": true, "summary": { "total": 3, "succeeded": 2, "failed": 1 } },
  "error": { "code": "PARTIAL_FAILURE", "message": "1 of 3 items failed", "retryable": false },
  "warnings": [],
  "meta": { "exit_code": 3, "duration_ms": 812 }
}
```

**Invalid — `ok` contradicts `meta.exit_code`**
```json
{
  "ok": true,
  "data": null,
  "error": { "code": "NOT_FOUND", "message": "Cluster not found" },
  "warnings": [],
  "meta": { "exit_code": 5, "duration_ms": 8 }
}
```
Violation: `ok` must be `false` and `error` non-null whenever `meta.exit_code` is non-zero.

**Invalid — prose warning**
```json
{
  "ok": true,
  "data": {},
  "error": null,
  "warnings": ["Flag --page-size is deprecated"],
  "meta": { "exit_code": 0, "duration_ms": 4 }
}
```
Violation: warnings are `WarningDetail` objects with a `code`; agents cannot branch on prose.

---

## Common mistakes

- **Omitting `meta.exit_code` because the process already returns it.** The process code is lost in pipelines, subprocess wrappers, and trace logs; the envelope copy is what survives
- **Setting `ok` in command code.** `ok` is derived from the exit code by the framework; a handler that sets it can publish `ok: true` next to a non-zero exit
- **Putting list metadata at the top level.** `pagination`, `cursor`, or `total` beside `data` breaks the invariant five-key shape; use `meta.pagination`
- **Emitting warnings as strings.** A string warning forces agents back to substring matching; emit `{ code, message, context }`
- **Returning the requested result in `data` on failure.** On failure `data` holds only a declared failure payload; a half-built success object misleads agents that skip `error`
- **Stuffing structured facts into `error.detail`.** `detail` is a string; key-value facts belong in `error.context`

---

## Agent interpretation

Rules for agents parsing `ResponseEnvelope` at runtime, including handling malformed, contradictory, or incomplete responses.

**Determining outcome**
- Classify from the process exit code when you have it, otherwise from `meta.exit_code`
- Process exit code and envelope disagree in either direction — treat the call as failed; the side reporting failure wins
- `ok: false` with process exit code `0` — a pipeline or wrapper masked the code (§56); classify by `meta.exit_code`
- `ok: false` with non-null `data` — `data` is a declared failure payload (partial results, conflicting resource, check report); read `error` first and never treat `data` as the requested result

**Missing or null fields**
- `error` key absent entirely — malformed response; treat as `GENERAL_ERROR`; do not retry blindly
- `meta.exit_code` absent — the tool predates envelope 2.0; fall back to the process exit code
- `data: null` and `error: null` with a non-zero `meta.exit_code` — malformed; log and escalate
- `warnings` key absent — treat as empty array; do not fail

**Deciding whether to act on `data`**
- `meta.truncated: true` — the byte cap cut `data`; narrow the query before drawing conclusions
- `meta.pagination.has_more: true` — more pages exist; pass `meta.pagination.next_cursor` as `--cursor` before concluding a list is complete
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
- Branch on `warnings[].code`, never on `message` text
- `DEPRECATED_FLAG` or `SCHEMA_DEPRECATED` — treat as a soft `REDIRECTED`; use `context.replacement` in future calls
- `FIELD_TRUNCATED` — the field named in `context.field` is incomplete; do not act on it as a full value

## Coding agent notes

**Type representation**
- Generate `ResponseEnvelope<T>` as a generic type where `T` is the command's declared output schema — do not use `any` or `object` for `data`
- `ok` must be a derived/computed field, not a settable field — generate it as a property that reads the exit code, not as a constructor parameter

**Construction**
- Generate a single `respond()` / `envelope()` factory function that the framework calls after the command handler returns — command handlers must never construct the envelope directly
- The factory sets `meta.exit_code`, derives `ok` from it, sets `meta.duration_ms` from a start timer, and validates that `error` is non-null whenever the exit code is non-zero

**Validation to generate**
- A schema validator that runs on every envelope in test mode and asserts all five required fields are present and non-absent
- An assertion that `ok == (meta.exit_code == 0)` and that `meta.exit_code` equals the process exit code; any divergence is a framework bug
- An assertion that `data` and `error` are not both null simultaneously (unless `meta.not_modified: true`)

**Tests to generate**
- Success path: `ok: true`, `data` matches declared output schema, `error: null`
- Failure path: `ok: false`, `data` is `null` or the declared failure payload, `error` has `code` and `message`, `meta.exit_code` is non-zero
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
- `WarningDetail` is closed (`additionalProperties: false`); extra facts go in `context`, which keeps the three-field shape predictable for agents
- Envelope 2.0 is a breaking change from 1.x: `meta.exit_code` became required, `warnings` became objects, and `meta.cursor` was replaced by `meta.pagination`
- `error.redirect` is only meaningful when the exit code is `REDIRECTED (13)`. Parsers should ignore it at other exit codes
- `error.code` is the stable identifier agents act on. `error.message` is for humans and may change between versions
