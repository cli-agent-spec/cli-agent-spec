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

## Fixtures

The benchmark mocks double as fixtures. [`democli-good.json`](profiles/democli-good.json) passes every check; [`democli-bad.json`](profiles/democli-bad.json) fails the output and safety checks. `tests/fixtures/conformance/hangcli` covers hangs and illegal exit codes; `lastwinscli` lets a subcommand default replace a global option given before the command path and keeps the last of two conflicting values. `posixcli` stops option parsing at the first positional, so an option after it is silently ignored. `tests/test_conformance.py` asserts every outcome.
