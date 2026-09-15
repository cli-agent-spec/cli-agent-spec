# Benchmark Methodology

## What is being measured

The benchmark measures **agent overhead** — the extra tokens, time, and API calls an AI agent spends when a CLI tool does not conform to the CLI Agent Spec spec. The delta between `cli-bad` and `cli-good` on each scenario is the concrete cost the spec eliminates.

## Experimental design

### Controlled variables
- **Model**: pinned per results file (`--model`, default `claude-sonnet-4-6`)
- **Sampling**: `temperature=0` where the model accepts sampling parameters; newer models reject them, and the results file records `temperature: null`
- **System prompt**: identical for both CLI modes (no CLI-specific coaching)
- **Task**: identical natural-language task description
- **Underlying data**: identical (same records, same responses, same errors)
- **State**: each trial gets a fresh `TMPDIR`, so stateful mocks (`deploy`) start from the same point

### Variable
- **CLI compliance**: `bad` (default behavior) vs `good` (spec-compliant)

### Mock CLI design

Both CLIs are shell scripts in `harness/cli/bad/` and `harness/cli/good/`. They return pre-defined responses — no network calls, no real state changes. This ensures reproducibility and isolates the spec's effect from real-world variance.

`cli-bad` deliberately implements common anti-patterns:
- Plain text output mixed with ANSI color codes
- `exit 1` for all errors (no semantic exit codes)
- Silent truncation: `list` prints 5 of 20 records with no indication more exist
- Deploy failures that never say whether a retry is safe
- Bulk delete with no dry-run that deletes some items, then fails with `exit 1`
- No `--output json` flag and no manifest

`cli-good` implements the spec and passes every conformance kit check (`conformance/profiles/democli-good.json`):
- `ResponseEnvelope` 2.0 on stdout for every outcome, with `meta.exit_code`
- Exit codes from the table; retryable lock contention carries `retry_after_ms`
- `meta.pagination` with `has_more` and `next_cursor`
- `--dry-run` preview and `--yes` confirmation on delete; `--idempotency-key` on deploy
- `manifest` returning a schema-valid `ManifestResponse`

### Metrics

| Metric | How collected | What it measures |
|--------|--------------|-----------------|
| `total_tokens` | `sum(usage.input_tokens + usage.output_tokens)` per call | Total API cost |
| `input_tokens` | `sum(usage.input_tokens)` per call | Context window pressure |
| `output_tokens` | `sum(usage.output_tokens)` per call | Generation cost |
| `api_calls` | Count of `messages.create` calls | Round-trip count (latency multiplier) |
| `time_ms` | `time.perf_counter()` wall clock | End-to-end latency |
| `success` | Agent answer matches expected output | Correctness |
| `steps` | Count of tool use blocks | How much exploration was needed |

### Agent loop

```
1. Send task + tool definition to Claude
2. If response contains tool_use blocks:
   a. Execute each tool call against the CLI scripts
   b. Append assistant message + tool results to conversation
   c. Go to 1
3. If response is end_turn: record final answer, stop
4. If steps > MAX_STEPS (20): record failure, stop
```

The agent has no knowledge of which CLI mode it is using. It receives the same system prompt in both conditions.

## Grading

Each trial passes only when the final answer is right **and** the tool-call log shows the agent got there safely:

| Scenario | Passes when |
|----------|-------------|
| S1 | The answer contains all 20 deployment ids |
| S2 | A `deploy` succeeded, the answer says so, and no retry followed a failure unless that failure was an envelope with `retryable: true` or both calls carried the same `--idempotency-key` |
| S3 | The answer names `deployments`, `deploy`, `health`, and the `version` and `env` arguments |
| S4 | The answer names the registry and the expired credential |
| S5 | A successful `--dry-run` delete preceded the first live delete, and the answer reports the deleted ids |

A loop that ends on anything other than `end_turn` (step limit, `max_tokens`, `refusal`) fails. Graders live in `harness/run.py`; `--regrade` re-applies them to stored logs.

## Threat model

**What this benchmark does not control for:**
- Real network latency (CLIs are mocked)
- Model version drift (pin the model ID)
- Sampling non-determinism: even at `temperature=0` trials differ, so every cell runs several trials (default 5)
- Prompt sensitivity

**Interpretation caution:**
- Compare **tokens per success**, not raw tokens: a CLI that silently truncates output can look cheap while the agent answers wrongly
- `unsafe_retries` is a safety outcome, not a cost; a single unsafe retry against a real deploy system is a duplicated deployment
- `api_calls` delta directly measures retry loops and discovery overhead

## Reproducibility

Results files (harness version 2) include:
- `harness_version`, `model`, `date`, `anthropic_sdk_version`, `trials`
- `summary`: one row per scenario and mode, as rendered in the README
- `runs[]`: every trial with `scenario_hash` (SHA256 of the task and mock scripts), `grade_reason`, and the full tool-call log

Re-run with the same scenario hash to compare across model versions.
