# Conformance Kit

> Deterministic checks for the parts of the CLI Agent Spec a machine can verify. No LLM, no network, one JSON result.

The kit runs the probes a profile declares against a real CLI. It reports every check as pass, fail, or skip, with the exact argv needed to reproduce a failure. Checks map to failure modes, requirements, and conformance levels (see [`requirements/levels.md`](../requirements/levels.md)).

## Run it

```bash
uv run conformance/run.py conformance/profiles/democli-good.json
```

Output is a `ResponseEnvelope` whose `data` is a [`ConformanceResult`](../schemas/conformance-result.md).

| Exit code | Meaning |
|-----------|---------|
| `0` | Every check that ran passed |
| `2` | The profile is missing or invalid; nothing ran |
| `4` | At least one check failed; `data.checks` has the evidence |

## Write a profile

A profile names the command prefix and the probes to run. See [`conformance-profile.md`](../schemas/conformance-profile.md) for the format. Probes call the real tool, so point profiles at a sandbox or a mock.

## Checks

| Check | Level | Verifies | Detects |
|-------|-------|----------|---------|
| `no_hang_stdin_closed` | 1 | REQ-F-009, REQ-F-010 | §10, §11 |
| `no_hang_stdin_open` | 1 | REQ-F-009 | §50, §10 |
| `json_envelope` | 1 | REQ-F-003, REQ-F-004, REQ-F-006, REQ-C-013 | §2, §3, §18 |
| `exit_code_contract` | 1 | REQ-F-001 | §1 |
| `stdout_no_ansi` | 1 | REQ-F-007 | §8 |
| `no_color_honored` | 1 | REQ-F-008 | §8 |
| `help_off_stdout` | 1 | REQ-F-048 | §3 |
| `invalid_input_exit_2` | 1 | REQ-F-002 | §14, §1 |
| `dry_run_preview` | 1 | REQ-C-004 | §23 |
| `destructive_refuses_unconfirmed` | 2 | REQ-C-005, REQ-O-021 | §23, §10 |
| `manifest_valid` | 3 | REQ-O-041 | §52, §21 |
| `argument_order` | 3 | REQ-F-067, REQ-F-079 | §69 |
| `stream_contract` | 3 | REQ-O-004 | §5, §76 |
| `stream_sigint` | 3 | REQ-O-004 (REQ-F-069's cancellation on a stream) | §16 |

## Stream probes

A `stream` probe runs a command whose stdout is a JSONL stream (REQ-O-004) once, instead of the single-envelope checks. The kit reads stdout line by line until the process exits or the probe's `deadline_seconds` (default `timeout_seconds`) passes; at the deadline it kills the whole process group and fails the run, so a stream that never ends cannot hang the kit. `stream_contract` checks that:

- Every line is one JSON object; blank and non-JSON lines fail. Heartbeat lines (`"heartbeat": true`, REQ-O-038) count as lines like items
- The stream ends on exactly one terminal line: the summary line (`"_summary": true`) or an error `ResponseEnvelope` (an `ok` boolean beside an `error` key), which must validate with `ok: false`. A line after it fails
- A summary line exits `0`; an error envelope's `meta.exit_code` equals the process exit code
- The process exits after its terminal line, before the deadline
- When the first item line carries `_seq`, the stream is numbered: every item line carries `_seq`, `1` on the first and one more on each next; heartbeat lines and the terminal line carry none; the summary line's `_count` equals the number of item lines; an error terminal envelope's `meta.items_emitted` equals the last `_seq`. In a stream whose first item line has no `_seq`, no line may carry it

With `signal: "INT"` and `after_lines: N`, the kit sends SIGINT to the process after reading `N` lines. `stream_sigint` then requires exit `130` and a terminal error envelope with `error.code` `CANCELLED` and `data.partial` `true` (REQ-F-069). A stream that ends before `N` lines fails, since the signal was never sent. Signals need POSIX; on Windows the kit skips `stream_sigint` and does not run signal probes.

The stream checks are level 3 because streaming is opt-in (REQ-O-004): a profile without a `stream` probe leaves `level_3` `incomplete`, as one without a `manifest` command does.

## Fixtures

The benchmark mocks double as fixtures. [`democli-good.json`](profiles/democli-good.json) passes every check; [`democli-bad.json`](profiles/democli-bad.json) fails the output and safety checks. `tests/fixtures/conformance/hangcli` covers hangs and illegal exit codes; `lastwinscli` lets a subcommand default replace a global option given before the command path and keeps the last of two conflicting values. `posixcli` stops option parsing at the first positional, so an option after it is silently ignored. `streamcli` writes JSONL streams: `tests/fixtures/conformance/streamcli-good.json` passes both stream checks, numbered streams included, and `streamcli.json` breaks each one (no terminal line, a line after it, a prose line, a wrong exit code, a stall, numbering that skips, starts at `0`, misses a line, numbers a heartbeat, starts late, or miscounts in `_count` or `meta.items_emitted`, and SIGINT that exits `1`, reports another code, omits `data.partial`, is ignored, or hangs). `tests/test_conformance.py` asserts every outcome.
