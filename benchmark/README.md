# CLI Agent Spec — Benchmark

Measures the real cost of non-compliant CLI tools on AI agent performance: **time**, **token spend**, and **context window usage**.

Each scenario runs an AI agent (Claude) against two CLI implementations of identical functionality:
- **`cli-bad`** — default behavior: plain text output, ANSI colors, inconsistent exit codes, no pagination, no schema
- **`cli-good`** — spec-compliant: JSON envelopes, typed exit codes, pagination, manifest, structured errors

The delta between the two is the overhead the spec eliminates.

---

## Results

<!-- results:start -->
No results recorded with harness version 2 yet. Run the harness, then render:

```bash
uv run benchmark/harness/run.py --all --trials 5 --output benchmark/results/$(date +%Y%m%d).json
uv run benchmark/render_results.py benchmark/results/<file>.json
```
<!-- results:end -->

The three March 2026 files in `results/` predate harness version 2. They ran one trial per cell, graded by substring match, and used a good mock that did not yet conform to envelope 2.0, so they are kept for history and not rendered.

---

## Scenarios

| ID | Name | Primary challenge cluster | Key spec requirements |
|----|------|--------------------------|----------------------|
| [S1](scenarios/s1-list-extract.md) | List & extract IDs | Pagination, context overflow | F-018, F-019, F-052, O-003 |
| [S2](scenarios/s2-retry-safety.md) | Deploy with conflict | Exit codes, retry safety | F-001, F-002, C-013, C-014 |
| [S3](scenarios/s3-discovery.md) | Discover command surface | Schema, manifest, token spend | C-015, O-013, O-041 |
| [S4](scenarios/s4-error-diagnosis.md) | Diagnose a failure | Error quality, structured errors | C-013, F-037, F-063 |
| [S5](scenarios/s5-destructive-ops.md) | Bulk delete with dry-run | Destructive ops, partial failure | C-002, C-004, C-008, C-009 |

---

## Running the benchmark

```bash
# Credentials: ANTHROPIC_API_KEY, or an `ant auth login` profile
uv run benchmark/harness/run.py --all --trials 5 --output benchmark/results/$(date +%Y%m%d).json

# One scenario, one mode
uv run benchmark/harness/run.py --scenario s2 --mode good --trials 3

# Re-grade stored tool logs after changing a grader, without calling the API
uv run benchmark/harness/run.py --regrade benchmark/results/<file>.json

# Render the table above
uv run benchmark/render_results.py benchmark/results/<file>.json
```

Every run spends API credits: `--all --trials 5` is 50 agent loops.

---

## How it works

1. The harness starts an agent loop using the Claude API with tool use
2. The agent is given the scenario task and a single tool: `run_cli(command, args)`
3. The tool executes `cli/bad/<command>` or `cli/good/<command>` (shell scripts returning mock data)
4. The loop runs until the agent produces a final answer or hits the step limit
5. At the end, `usage.input_tokens` and `usage.output_tokens` are summed across all API calls

Metrics collected per run:
- `total_tokens` — input + output tokens across the full agentic loop
- `input_tokens` — context consumed (proxy for context window pressure)
- `output_tokens` — generation cost
- `api_calls` — number of model invocations (each tool call = one roundtrip)
- `time_ms` — wall-clock time
- `success` — graded from the final answer **and** the tool-call log (see methodology)
- `unsafe_retry` — the agent re-ran `deploy` after a failure that did not declare the retry safe
- `tool_calls` — number of CLI invocations, stored with argv, exit code, and output for re-grading

See [`methodology.md`](methodology.md) for scoring details and threat model.
