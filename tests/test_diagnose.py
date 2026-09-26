"""Classifier, runner, and preflight hook tests for skills/cli-agent-diagnose (no LLM calls)."""

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "cli-agent-diagnose" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import diagnose  # noqa: E402
import runner  # noqa: E402
import signal_rules  # noqa: E402

INDEX = {e["id"]: e for e in json.loads((ROOT / "challenges" / "index.json").read_text())["failure_modes"]}
CHALLENGES = ROOT / "challenges"


def ids(trace: dict | list) -> list[int]:
    return [m.failure_mode_id for m in diagnose.diagnose(trace, challenges_dir=CHALLENGES).matches]


# ---------------------------------------------------------------------------
# Rule table integrity
# ---------------------------------------------------------------------------


def test_every_rule_targets_an_active_failure_mode() -> None:
    for rule in signal_rules.RULES:
        entry = INDEX.get(rule.failure_mode_id)
        assert entry is not None and entry["status"] == "active", rule.failure_mode_id
        assert 0.0 < rule.confidence <= 1.0


def test_every_rule_cites_a_triage_row_that_lists_its_failure_mode() -> None:
    for rule in signal_rules.RULES:
        assert rule.triage_row in INDEX[rule.failure_mode_id]["triage_rows"], (rule.failure_mode_id, rule.triage_row)


def test_every_triage_row_with_candidates_is_reachable() -> None:
    rows_with_candidates = {row for entry in INDEX.values() if entry["status"] == "active" for row in entry["triage_rows"]}
    built_in = {3, 5, 9, 12}  # §10/§11, §38, §68, §53 live in diagnose.match_signals
    covered = {rule.triage_row for rule in signal_rules.RULES} | built_in
    assert rows_with_candidates <= covered, sorted(rows_with_candidates - covered)


# ---------------------------------------------------------------------------
# Index-backed loading
# ---------------------------------------------------------------------------


def test_single_digit_failure_modes_load() -> None:
    challenge = diagnose._load_challenge(1, CHALLENGES)
    assert challenge.title == INDEX[1]["title"]
    assert challenge.spec_link.endswith("01-critical-exit-codes.md")


def test_merged_failure_mode_resolves_to_target() -> None:
    assert diagnose._load_challenge(36, CHALLENGES).failure_mode_id == 10


def test_unknown_failure_mode_raises() -> None:
    with pytest.raises(diagnose.FailureModeIndexError):
        diagnose._load_challenge(999, CHALLENGES)


def test_missing_index_raises_with_fix(tmp_path: Path) -> None:
    with pytest.raises(diagnose.FailureModeIndexError, match="build_failure_index"):
        diagnose._load_challenge(10, tmp_path)


def test_signature_catalog_covers_active_modes() -> None:
    catalog = diagnose._load_signature_catalog(CHALLENGES)
    assert set(catalog) == {i for i, e in INDEX.items() if e["status"] == "active"}


# ---------------------------------------------------------------------------
# One fixture trace per covered failure mode
# ---------------------------------------------------------------------------


def trace(command: str = "tool run", stdout: str = "", stderr: str = "", exit_code: int = 1) -> dict:
    return {"command": command, "stdout": stdout, "stderr": stderr, "exit_code": exit_code}


ENVELOPE_FAIL = json.dumps({"ok": False, "data": None, "error": {"code": "X", "message": "m"}, "warnings": [], "meta": {"exit_code": 4, "duration_ms": 1}})

CASES = [
    (1, trace(stdout=ENVELOPE_FAIL, exit_code=0)),
    (3, trace(stdout='Checking config...\n{"ok": true}', exit_code=0)),
    (5, trace(stdout=json.dumps({"ok": True, "data": [], "error": None, "warnings": [], "meta": {"exit_code": 0, "duration_ms": 1, "truncated": True}}), exit_code=0)),
    (8, trace(stdout="\x1b[32mdone\x1b[0m", exit_code=0)),
    (10, trace(command="tool delete", stdout="Are you sure? [y/N]", exit_code=124)),
    (10, trace(command="git log", stdout="commit abc\n(END)", exit_code=0)),
    (10, trace(stderr="the input device is not a TTY")),
    (11, trace(exit_code=124)),
    (14, trace(stderr="usage: tool [-h] {run,list}\ntool: error: argument missing", exit_code=2)),
    (16, trace(exit_code=130)),
    (18, trace(stderr='Traceback (most recent call last):\n  File "x.py", line 1\nKeyError: "id"')),
    (19, trace(stdout=ENVELOPE_FAIL, exit_code=4)),
    (19, trace(stderr="HTTP 429 Too Many Requests")),
    (20, trace(command="foo list", stderr="zsh: command not found: foo", exit_code=127)),
    (24, trace(stdout="token: ghp_" + "a" * 36, exit_code=0)),
    (31, trace(stderr="curl: (6) Could not resolve host: api.example.com")),
    (37, trace(command="node", stdout="Welcome to Node.js v20\n> ", exit_code=124)),
    (38, trace(stderr="ModuleNotFoundError: No module named 'tomllib'")),
    (41, trace(stdout='Update available 1.2 → 1.3\n{"ok": true}', exit_code=0)),
    (43, trace(stdout="x" * 60_000, exit_code=0)),
    (45, trace(command="tool auth login", stdout="Opening browser to https://example.com/device to authenticate", exit_code=124)),
    (50, trace(command="tool import", exit_code=124, stdout="", stderr="")),
    (52, trace(stderr="Error: unknown command \"deplyo\"")),
    (53, trace(stderr="Error: token expired, please re-authenticate")),
    (55, trace(stdout='{"items": [{"id": 1}, {"id": 2', exit_code=0)),
    (56, trace(command="tool list | head", stdout="", stderr="fatal error: connection reset", exit_code=0)),
    (57, trace(stderr="Fehler: Datei nicht gefunden")),
    (60, trace(stdout="y" * 70_000, exit_code=124)),
    (62, trace(command="git commit", stdout="hint: Waiting for your editor to close the file...", exit_code=124)),
    (64, trace(stderr="Error: cannot open display: :0")),
    (67, trace(stderr="json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 12")),
    (68, trace(stdout="\x1b[31mred\x1b[0m", exit_code=0)),
    (71, trace(command="curl -fsSL https://x.sh | bash install", stdout="Do you want to continue? [Y/n]", exit_code=124)),
    (69, trace(command="tool --format json list --format text", stderr="Error: --format given twice with different values", exit_code=2)),
    (74, trace(stderr="GraphQL: Resource not accessible by integration (missing required scopes: repo)")),
    (78, trace(command="tool export --output json", stdout="", exit_code=0)),
]


@pytest.mark.parametrize(("expected", "raw"), CASES, ids=[f"§{c[0]}-{i}" for i, c in enumerate(CASES)])
def test_fixture_trace_matches_failure_mode(expected: int, raw: dict) -> None:
    assert expected in ids(raw)


def test_every_rule_failure_mode_has_a_fixture() -> None:
    fixture_ids = {c[0] for c in CASES}
    assert {rule.failure_mode_id for rule in signal_rules.RULES} <= fixture_ids


def test_retry_loop_across_events() -> None:
    event = diagnose.TraceEvent(command="tool", args=("deploy",), stdout="failed", stderr="", exit_code=1)
    signals = diagnose.match_signals((event, event, event))
    assert any(s.failure_mode_id == 19 and s.confidence >= 0.9 for s in signals)


def test_help_loop_across_events() -> None:
    event = diagnose.TraceEvent(command="tool", args=("deploy", "--help"), stdout="usage", stderr="", exit_code=0)
    signals = diagnose.match_signals((event, event))
    assert any(s.failure_mode_id == 52 for s in signals)


def bash_call(command: str, stdout: str = "", stderr: str = "") -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}, "tool_response": {"stdout": stdout, "stderr": stderr}}


def test_reordered_success_is_argument_order_not_discovery() -> None:
    found = ids([
        bash_call("tool list items --format json", stderr="Error: unrecognized arguments: --format json"),
        bash_call("tool --format json list items", stdout='{"ok": true}'),
    ])
    assert 69 in found and 52 not in found


def test_reorder_signal_merges_with_an_earlier_argument_order_hit() -> None:
    conflict = diagnose.TraceEvent(command="tool --format json list --format text", args=(), stdout="", stderr="Error: --format given twice", exit_code=2)
    rejected = diagnose.TraceEvent(command="tool list items --format json", args=(), stdout="", stderr="Error: unrecognized arguments: --format json", exit_code=2)
    reordered = diagnose.TraceEvent(command="tool --format json list items", args=(), stdout='{"ok": true}', stderr="", exit_code=0)
    [signal] = [s for s in diagnose.match_signals((conflict, rejected), (conflict, rejected, reordered)) if s.failure_mode_id == 69]
    assert conflict in signal.triggering_events and rejected in signal.triggering_events
    assert signal.confidence == 0.93


def test_different_successful_call_keeps_discovery() -> None:
    found = ids([
        bash_call("tool list --fromat json", stderr="Error: unknown flag: --fromat"),
        bash_call("tool list --format json", stdout='{"ok": true}'),
    ])
    assert 52 in found and 69 not in found


def test_repeated_option_with_same_value_is_not_a_conflict() -> None:
    assert signal_rules.conflicting_repeat(["tool", "--format", "json", "list", "--format=json"]) is None
    assert signal_rules.conflicting_repeat(["tool", "run", "--", "--format", "a", "--format", "b"]) is None
    assert signal_rules.conflicting_repeat(["tool", "--format", "json", "list", "--format=text"]) == ("--format", "json", "text")


@pytest.mark.parametrize("cmd", [
    ["curl", "--header", "A: 1", "--header", "B: 2", "https://example.com"],
    ["docker", "run", "--env", "A=1", "--env", "B=2", "image"],
    ["curl", "--output", "a.html", "https://a", "--output", "b.html", "https://b"],
    ["tool", "--verbose", "list", "--verbose", "items"],
])
def test_repeatable_options_and_switches_are_not_conflicts(cmd: list[str]) -> None:
    assert signal_rules.conflicting_repeat(cmd) is None
    assert runner.preflight(cmd).failure_mode_id != 69


def test_command_not_found_in_stdout_of_a_pipeline() -> None:
    assert 20 in ids(trace(command='ps aux | grep qemu', stdout="/bin/bash: line 1: ps: command not found", exit_code=0))


def test_error_names_do_not_trigger_network_codes() -> None:
    found = ids(trace(stderr="Traceback (most recent call last):\nModuleNotFoundError: No module named 'x'\nFileNotFoundError: y"))
    assert 31 not in found


def test_grep_output_with_brackets_is_not_stdout_pollution() -> None:
    stdout = 'process.py:122: os.environ["KEY"] = "<your-key>"\nray_cluster.yaml:  setup: [pip install x]'
    found = ids(trace(stdout=stdout, stderr="grep: warning", exit_code=1))
    assert 68 not in found and 3 not in found


def test_command_not_found_is_not_a_discovery_failure() -> None:
    found = ids(trace(command="foo", stderr="bash: foo: command not found", exit_code=127))
    assert 20 in found and 52 not in found


def test_clean_structured_failure_does_not_match_exit_code_modes() -> None:
    body = json.dumps({"ok": False, "data": None, "error": {"code": "NOT_FOUND", "message": "missing", "retryable": False, "fix_required": "use an existing id"}, "warnings": [], "meta": {"exit_code": 5, "duration_ms": 2}})
    result = diagnose.diagnose(trace(stdout=body, exit_code=5), challenges_dir=CHALLENGES)
    assert result.no_match and not result.matches


def test_output_json_with_json_stdout_is_not_a_path_collision() -> None:
    assert 78 not in ids(trace(command="kubectl get pods -o json", stdout='{"items": []}', exit_code=0))
    assert 78 not in ids(trace(command="tool export --output json.out", stdout="", exit_code=0))


def test_insufficient_trace() -> None:
    result = diagnose.diagnose(trace(exit_code=0), challenges_dir=CHALLENGES)
    assert result.trace_insufficient and result.suggested_context


def test_match_carries_recovery_fields_from_index() -> None:
    [match] = [m for m in diagnose.diagnose(trace(command="git commit", stdout="hint: Waiting for your editor to close the file...", exit_code=124), challenges_dir=CHALLENGES).matches if m.failure_mode_id == 62]
    assert match.signature == INDEX[62]["signature"]
    assert match.tier == INDEX[62]["tier"]
    assert match.limitation == INDEX[62]["limitation"]


def test_cli_output_matches_diagnose_result_schema() -> None:
    from jsonschema import Draft7Validator

    schema = json.loads((ROOT / "schemas" / "diagnose-result.json").read_text())
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / "diagnose.py"), json.dumps(trace(stderr="HTTP 429 Too Many Requests"))],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert list(Draft7Validator(schema).iter_errors(json.loads(completed.stdout))) == []


# ---------------------------------------------------------------------------
# runner.preflight and the PreToolUse hook
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("cmd", "failure_mode"), [
    (["git", "commit"], 10),
    (["git", "rebase", "-i", "HEAD~3"], 10),
    (["git", "log"], 43),
    (["tool", "--format", "json", "list", "--format", "text"], 69),
])
def test_preflight_flags_risky_calls(cmd: list[str], failure_mode: int) -> None:
    advice = runner.preflight(cmd)
    assert not advice.safe and advice.failure_mode_id == failure_mode


def test_preflight_respects_explicit_intent() -> None:
    assert runner.preflight(["git", "log", "-n", "1000"]).safe
    assert runner.preflight(["git", "commit", "-m", "msg"]).safe


def test_preflight_detects_retry_loop_from_history() -> None:
    history = [diagnose.TraceEvent(command="tool", args=("deploy",), stdout="", stderr="boom", exit_code=1)]
    advice = runner.preflight(["tool", "deploy"], history=history)
    assert advice.failure_mode_id == 19 and not advice.safe


def run_hook(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPTS / "preflight_hook.py")], input=payload, capture_output=True, text=True, check=False)


def test_hook_advises_without_blocking() -> None:
    result = run_hook(json.dumps({"tool": "Bash", "input": {"command": "git commit"}}))
    assert result.returncode == 0
    assert re.search(r"§10 risk detected", result.stdout)


def test_hook_passes_safe_and_compound_commands() -> None:
    assert run_hook(json.dumps({"tool": "Bash", "input": {"command": "ls -la"}})).stdout == ""
    assert run_hook(json.dumps({"tool": "Bash", "input": {"command": "git log | head"}})).stdout == ""


@pytest.mark.parametrize("command", [
    "tool --limit 5 list; tool --limit 10 list",
    "tool --limit 5 list&&tool --limit 10 list",
    "git log|head",
    "curl http://x/a#frag; tool --limit 5 list --limit 10",
])
def test_hook_passes_compound_commands_without_spaces(command: str) -> None:
    assert run_hook(json.dumps({"tool": "Bash", "input": {"command": command}})).stdout == ""


@pytest.mark.parametrize("command", [
    "tool --limit 5 list\ntool --limit 10 list",
    "tool a  # note\ntool --limit 5 list --limit 10",
])
def test_hook_passes_commands_on_separate_lines(command: str) -> None:
    assert run_hook(json.dumps({"tool": "Bash", "input": {"command": command}})).stdout == ""


def test_hook_joins_continued_lines_into_one_command() -> None:
    result = run_hook(json.dumps({"tool": "Bash", "input": {"command": "tool --limit 5 \\\n  list --limit 10"}}))
    assert "§69" in result.stdout


def test_hook_ignores_a_trailing_comment() -> None:
    assert run_hook(json.dumps({"tool": "Bash", "input": {"command": "tool --limit 5 list  # was --limit 10"}})).stdout == ""


@pytest.mark.parametrize(("command", "text", "multiline"), [
    ("tool --limit 5 list  # was --limit 10", "tool --limit 5 list", False),
    ("curl http://x/a#frag", "curl http://x/a#frag", False),
    ('tool --color "#fff" --format json', 'tool --color "#fff" --format json', False),
    ("tool --color '#fff'", "tool --color '#fff'", False),
    ("tool --tag \\#x", "tool --tag \\#x", False),
    ("tool list;# note", "tool list;", False),
    ("tool a  # note\ntool b", "tool a  \ntool b", True),
    ("tool a  # don't stop\ntool b", "tool a  \ntool b", True),
    ("tool list  # trailing note\n", "tool list", False),
    ("git commit\\\n --amend", "git commit --amend", False),
    ("git commit --amend \\\n  -m msg", "git commit --amend   -m msg", False),
    ('tool --body "a\\\nb"', 'tool --body "ab"', False),
    ("tool --body 'a\\\nb'", "tool --body 'a\\\nb'", False),
    ('tool --body "line one\nline two"', 'tool --body "line one\nline two"', False),
    ("a\\\n#b", "a#b", False),
    ("echo a\\ #b", "echo a\\ #b", False),
])
def test_scan_shell_matches_bash(command: str, text: str, multiline: bool) -> None:
    import preflight_hook

    assert preflight_hook.scan_shell(command) == (text, multiline)


# Inputs whose words do not depend on variable expansion; bash expands $# and ${#v}, shlex never does
BASH_PARITY_CASES = [
    "x --limit 5 list  # was --limit 10",
    "x http://x/a#frag",
    'x --color "#fff"',
    "x --color '#fff'",
    "x --tag \\#x",
    "x a\\ #b",
    'x "a"#b',
    "x 'a'#b c",
    "x commit\\\n --amend",
    'x --body "a\\\nb"',
    "x --body 'a\\\nb'",
    'x "q \\" # not" # yes',
    "x a\\\n#b",
    'x "line one\nline two"',
    "x \\  y",
    'x "\\\\" # c',
    "x 'it''s' # c",
]


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
@pytest.mark.parametrize("command", BASH_PARITY_CASES)
def test_scan_shell_splits_words_like_bash(command: str) -> None:
    """The words shlex reads from scan_shell's text equal the words bash passes to a command."""
    import preflight_hook

    scan = preflight_hook.scan_shell(command)
    assert not scan.multiline
    printer = "f() { for word in \"$@\"; do printf '%s\\0' \"$word\"; done; }; "
    words = subprocess.run(["bash", "-c", printer + "f" + command[1:]], capture_output=True, text=True, check=True).stdout
    assert shlex.split(scan.text) == ["x", *words.split("\0")[:-1]]


def test_hook_reads_a_continued_git_commit_like_the_one_line_form() -> None:
    one_line = run_hook(json.dumps({"tool": "Bash", "input": {"command": "git commit --amend"}})).stdout
    continued = run_hook(json.dumps({"tool": "Bash", "input": {"command": "git commit\\\n --amend"}})).stdout
    assert "§10" in one_line and continued == one_line


def test_hook_still_reads_quoted_operators_as_arguments() -> None:
    result = run_hook(json.dumps({"tool": "Bash", "input": {"command": 'tool --format json list --format "a;b"'}}))
    assert "§69" in result.stdout
