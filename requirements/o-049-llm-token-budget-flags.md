# REQ-O-049: LLM Token Budget Flags

**Tier:** Opt-In | **Priority:** P2

**Source:** [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) · [§43 Tool Output Result Size Unboundedness](../challenges/01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md)

**Addresses:** Severity: Medium–Critical / Token Spend: High / Time: Low / Context: High

---

## Description

The framework MUST provide three flags that let an LLM caller manage how much output lands in its context window:

- `--token-limit <n>`: truncate output to the first `n` tokens and emit `meta.truncated: true` with `meta.token_limit: n` in the response envelope. The truncation MUST be clean (never mid-token or mid-field) and MUST be indicated by a truncation sentinel appended to the data.
- `--token-count`: instead of emitting the command output, emit only the token count that the output would consume (`meta.token_count: n`, `data: null`). The command MUST execute fully to produce the count, but MUST NOT write the payload to stdout.
- `--token-offset <n>`: skip the first `n` tokens of output before beginning emission. When combined with `--token-limit`, this enables sliding-window access over output that exceeds the caller's context budget.

Token counting MUST use the same tokenizer as the primary consumer (typically `cl100k_base` or the framework's declared default). If the tokenizer is configurable, `--tokenizer <name>` selects it.

These flags are distinct from `--fields` (which filters by key) and the framework's byte-level hard cap (REQ-F-052). They operate on the token dimension, which is what LLM callers actually spend.

## Acceptance Criteria

- `--token-limit 500` produces output that, when tokenized, contains ≤500 tokens; `meta.truncated: true` and `meta.token_limit: 500` are present in the envelope
- `--token-count` returns `data: null` and `meta.token_count: N` without writing the payload
- `--token-offset 200 --token-limit 200` returns the second window of 200 tokens
- All three flags are available on every command without per-command implementation
- `meta.token_count` is present in every response when `--token-count` is passed, regardless of `--output` format

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

Requirement-specific `meta` fields:

| Field | Type | When present |
|---|---|---|
| `meta.truncated` | boolean | When `--token-limit` truncated the payload |
| `meta.token_limit` | integer | When `--token-limit` was passed |
| `meta.token_count` | integer | When `--token-count` was passed |
| `meta.token_offset` | integer | When `--token-offset` was nonzero |

---

## Wire Format

```bash
$ tool list-events --token-limit 500 --output json
```

```json
{
  "ok": true,
  "data": ["...first 500 tokens of events...", "[TRUNCATED]"],
  "error": null,
  "warnings": [],
  "meta": {
    "truncated": true,
    "token_limit": 500,
    "token_offset": 0,
    "duration_ms": 84
  }
}
```

```bash
$ tool list-events --token-count --output json
```

```json
{
  "ok": true,
  "data": null,
  "error": null,
  "warnings": [],
  "meta": {
    "token_count": 4217,
    "duration_ms": 61
  }
}
```

Sliding window over large output:

```bash
$ tool list-events --token-offset 500 --token-limit 500 --output json
# Returns tokens 500–999 of the full output
```

---

## Example

Opt-in at the framework level; token counting uses the declared tokenizer.

```
app = Framework("tool")
app.enable_token_budget(tokenizer="cl100k_base")

# Agent decides whether to fetch before committing context budget:
count_result = run("tool list-events --token-count --output json")
if count_result["meta"]["token_count"] > context_budget:
    # Fetch in windows instead
    run(f"tool list-events --token-offset 0 --token-limit {context_budget} --output json")
else:
    run("tool list-events --output json")
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-052](f-052-response-size-hard-cap-with-truncation-indicator.md) | F | Provides: byte-level hard cap; token budget flags operate on the token dimension instead |
| [REQ-O-002](o-002-fields-selector.md) | O | Composes: `--fields` reduces the key space before token limiting reduces the token count |
| [REQ-O-001](o-001-output-format-flag.md) | O | Composes: token budget flags apply after format selection, not before |
| [schemas/manifest-response.md](../schemas/manifest-response.md) | Exposes: `output_formats` field in `CommandEntry` declares when LLM-optimized formats are available alongside token budget flags |
