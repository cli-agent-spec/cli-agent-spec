import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "conformance" / "run.py"
RESULT_SCHEMA = json.loads((ROOT / "schemas" / "conformance-result.json").read_text())
FIXTURES = ROOT / "tests" / "fixtures" / "conformance"


def run_kit(profile: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run([sys.executable, str(KIT), str(profile), *extra], capture_output=True, text=True, timeout=120)
    return result.returncode, json.loads(result.stdout)


def statuses(envelope: dict) -> dict[str, str]:
    return {check["id"]: check["status"] for check in envelope["data"]["checks"]}


@pytest.fixture(scope="module")
def good() -> tuple[int, dict]:
    return run_kit(ROOT / "conformance/profiles/democli-good.json")


@pytest.fixture(scope="module")
def bad() -> tuple[int, dict]:
    return run_kit(ROOT / "conformance/profiles/democli-bad.json")


def test_good_mock_passes_every_check(good) -> None:
    code, envelope = good
    assert code == 0
    assert envelope["ok"] is True and envelope["meta"]["exit_code"] == 0
    assert set(statuses(envelope).values()) == {"pass"}
    assert envelope["data"]["levels"] == {"level_1": "pass", "level_2": "pass", "level_3": "pass"}


def test_bad_mock_fails_output_and_safety_checks(bad) -> None:
    code, envelope = bad
    assert code == 4
    assert envelope["ok"] is False and envelope["error"]["code"] == "CONFORMANCE_CHECKS_FAILED"
    result = statuses(envelope)
    for check in ("json_envelope", "stdout_no_ansi", "no_color_honored", "help_off_stdout",
                  "invalid_input_exit_2", "dry_run_preview", "destructive_refuses_unconfirmed"):
        assert result[check] == "fail", check
    assert result["manifest_valid"] == "skip"
    assert result["argument_order"] == "fail"
    assert envelope["data"]["levels"]["level_1"] == "fail"


def test_overwritten_and_last_wins_global_option_fails_argument_order() -> None:
    code, envelope = run_kit(FIXTURES / "lastwinscli.json")
    assert code == 4
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == "argument_order"]
    details = [f["detail"] for f in check["failures"]]
    assert any("overwritten by a default" in d for d in details)
    assert any("given twice" in d and "expected 2" in d for d in details)


def test_option_after_positional_read_as_positional_fails_argument_order() -> None:
    code, envelope = run_kit(FIXTURES / "posixcli.json")
    assert code == 4
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == "argument_order"]
    details = [f["detail"] for f in check["failures"]]
    assert any("had no effect" in d for d in details)
    assert any("different data than before it" in d for d in details)


def test_envelope_timestamp_must_be_a_date_time() -> None:
    code, envelope = run_kit(FIXTURES / "timestampcli.json", "--only", "json_envelope")
    assert code == 4
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == "json_envelope"]
    assert check["status"] == "fail"
    assert any("meta/timestamp" in f["detail"] and "date-time" in f["detail"] for f in check["failures"])


def test_argument_order_rejects_identical_values(tmp_path: Path) -> None:
    profile = json.loads((ROOT / "conformance/profiles/democli-good.json").read_text())
    profile["command"] = [str((ROOT / "benchmark/harness/cli/good/democli").resolve())]
    profile["argument_order"]["alternate_value"] = profile["argument_order"]["value"]
    path = tmp_path / "same.json"
    path.write_text(json.dumps(profile))
    code, envelope = run_kit(path)
    assert code == 2 and "alternate_value" in envelope["error"]["message"]


def test_hanging_cli_fails_hang_and_exit_checks() -> None:
    code, envelope = run_kit(FIXTURES / "hangcli.json")
    assert code == 4
    result = statuses(envelope)
    assert result["no_hang_stdin_closed"] == "fail"
    assert result["no_hang_stdin_open"] == "fail"
    assert result["exit_code_contract"] == "fail"
    details = [f["detail"] for c in envelope["data"]["checks"] if c["id"] == "exit_code_contract" for f in c["failures"]]
    assert any("outside" in d for d in details) and any("meta.exit_code" in d for d in details)


@pytest.mark.parametrize("fixture", ["good", "bad"])
def test_output_matches_result_schema(fixture, request) -> None:
    _code, envelope = request.getfixturevalue(fixture)
    assert list(Draft7Validator(RESULT_SCHEMA).iter_errors(envelope["data"])) == []


def test_invalid_profile_exits_2(tmp_path: Path) -> None:
    profile = tmp_path / "broken.json"
    profile.write_text(json.dumps({"schema_version": "1.0", "tool": "x", "command": ["true"], "timeout_seconds": 1, "probes": [
        {"name": "rm", "argv": ["rm"], "kind": "destructive"}
    ]}))
    code, envelope = run_kit(profile)
    assert code == 2
    assert envelope["error"]["code"] == "INVALID_PROFILE" and envelope["error"]["phase"] == "validation"
    assert envelope["meta"]["exit_code"] == 2


def test_only_filters_reported_checks(good) -> None:
    code, envelope = run_kit(ROOT / "conformance/profiles/democli-good.json", "--only", "manifest_valid")
    assert code == 0
    assert list(statuses(envelope)) == ["manifest_valid"]


def test_check_levels_match_requirement_levels() -> None:
    import validate_links

    sys.path.insert(0, str(ROOT / "conformance"))
    import run as kit

    levels = validate_links.requirement_levels()
    for spec in kit.CHECKS:
        assert spec.level == min(levels[r] for r in spec.requirements), spec.id


POSIX_ONLY = pytest.mark.skipif(sys.platform == "win32", reason="SIGINT delivery and process groups need POSIX signals")


@pytest.fixture(scope="module")
def broken_streams() -> tuple[int, dict]:
    return run_kit(FIXTURES / "streamcli.json", "--only", "stream_contract", "stream_sigint")


def stream_failures(envelope: dict, check_id: str) -> dict[str, list[str]]:
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == check_id]
    failures: dict[str, list[str]] = {}
    for failure in check["failures"]:
        failures.setdefault(failure["probe"], []).append(failure["detail"])
    return failures


@POSIX_ONLY
def test_conforming_streams_pass_stream_checks() -> None:
    code, envelope = run_kit(FIXTURES / "streamcli-good.json", "--only", "stream_contract", "stream_sigint")
    assert code == 0, envelope
    assert statuses(envelope) == {"stream_contract": "pass", "stream_sigint": "pass"}
    runs = {c["id"]: c["runs_checked"] for c in envelope["data"]["checks"]}
    assert runs == {"stream_contract": 4, "stream_sigint": 1}
    assert list(Draft7Validator(RESULT_SCHEMA).iter_errors(envelope["data"])) == []


@pytest.mark.parametrize(("probe", "expected"), [
    ("no terminal line", "without a terminal line"),
    ("line after the terminal line", "follows the terminal line 3"),
    ("prose line", "line 2 is not JSON"),
    ("summary then exit 1", "summary line but exited 1, expected 0"),
    ("exit mismatch", "declares meta.exit_code 12 but the process exited 1"),
    ("stall", "0.5s deadline after 1 lines and no terminal line; killed"),
    ("linger after the summary", "0.5s deadline after its terminal line; killed"),
])
def test_broken_stream_fails_stream_contract(broken_streams, probe: str, expected: str) -> None:
    code, envelope = broken_streams
    assert code == 4
    details = stream_failures(envelope, "stream_contract")[probe]
    assert any(expected in d for d in details), details


def test_killed_stream_reports_timeout_evidence(broken_streams) -> None:
    _code, envelope = broken_streams
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == "stream_contract"]
    [stall] = [f for f in check["failures"] if f["probe"] == "stall"]
    assert stall["timed_out"] is True and stall["exit_code"] is None
    assert stall["duration_ms"] < 3000


@POSIX_ONLY
def test_deadline_holds_when_a_child_outlives_the_cli(broken_streams) -> None:
    _code, envelope = broken_streams
    [check] = [c for c in envelope["data"]["checks"] if c["id"] == "stream_contract"]
    [orphan] = [f for f in check["failures"] if f["probe"] == "child keeps stdout open"]
    assert orphan["timed_out"] is True
    assert orphan["duration_ms"] < 3000, orphan


@POSIX_ONLY
@pytest.mark.parametrize(("probe", "expected"), [
    ("ends before the signal (SIGINT after 5 lines)", "before after_lines 5; SIGINT never sent"),
    ("SIGINT exits 1 (SIGINT after 2 lines)", "exited 1 after SIGINT, expected 130"),
    ("SIGINT wrong code (SIGINT after 2 lines)", "error.code 'INTERRUPTED', expected 'CANCELLED'"),
    ("SIGINT ignored (SIGINT after 2 lines)", "stream ended on its summary line after SIGINT"),
    ("hang after SIGINT (SIGINT after 2 lines)", "no exit within the 0.8s deadline after SIGINT; killed"),
])
def test_wrong_sigint_handling_fails_stream_sigint(broken_streams, probe: str, expected: str) -> None:
    _code, envelope = broken_streams
    details = stream_failures(envelope, "stream_sigint")[probe]
    assert any(expected in d for d in details), details


@POSIX_ONLY
def test_killed_streams_leave_no_processes(broken_streams) -> None:
    _code, envelope = broken_streams
    assert envelope["data"]["summary"]["failed"] == 2
    processes = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True, check=True).stdout
    assert not [line for line in processes.splitlines() if "sleep 37" in line or str(FIXTURES / "streamcli") in line]


def test_broken_stream_result_matches_schema(broken_streams) -> None:
    _code, envelope = broken_streams
    assert list(Draft7Validator(RESULT_SCHEMA).iter_errors(envelope["data"])) == []


def test_profile_without_stream_probes_skips_stream_checks(bad) -> None:
    _code, envelope = bad
    result = statuses(envelope)
    assert result["stream_contract"] == "skip" and result["stream_sigint"] == "skip"


@pytest.mark.parametrize(("probe", "message"), [
    ({"name": "s", "argv": ["good"], "kind": "stream", "signal": "INT"}, "after_lines"),
    ({"name": "s", "argv": ["good"], "kind": "stream", "after_lines": 2}, "signal"),
    ({"name": "s", "argv": ["good"], "kind": "read", "deadline_seconds": 1}, "probes/0"),
    ({"name": "s", "argv": ["good"], "kind": "read", "signal": "INT", "after_lines": 2}, "probes/0"),
    ({"name": "s", "argv": ["good"], "kind": "stream", "dry_run_flag": "--dry-run"}, "probes/0"),
    ({"name": "s", "argv": ["good"], "kind": "stream", "signal": "TERM", "after_lines": 2}, "signal"),
    ({"name": "s", "argv": ["good"], "kind": "stream", "signal": "INT", "after_lines": 0}, "after_lines"),
])
def test_invalid_stream_probe_exits_2(tmp_path: Path, probe: dict, message: str) -> None:
    profile = tmp_path / "stream.json"
    profile.write_text(json.dumps({"schema_version": "1.0", "tool": "x", "command": ["true"], "timeout_seconds": 1, "probes": [probe]}))
    code, envelope = run_kit(profile)
    assert code == 2 and envelope["error"]["code"] == "INVALID_PROFILE"
    assert message in envelope["error"]["message"]


@pytest.mark.parametrize(("probe", "message"), [
    ({"name": "s", "argv": [], "kind": "stream", "signal": "INT"}, "signal and after_lines together"),
    ({"name": "s", "argv": [], "kind": "stream", "after_lines": 2}, "signal and after_lines together"),
    ({"name": "s", "argv": [], "kind": "read", "deadline_seconds": 1}, "apply only to stream probes"),
    ({"name": "s", "argv": [], "kind": "invalid", "after_lines": 2, "signal": "INT"}, "apply only to stream probes"),
    ({"name": "s", "argv": [], "kind": "stream", "dry_run_flag": "--dry-run"}, "must not declare dry_run_flag"),
    ({"name": "s", "argv": [], "kind": "destructive"}, "must declare dry_run_flag"),
])
def test_load_probe_enforces_stream_rules_without_the_schema(probe: dict, message: str) -> None:
    sys.path.insert(0, str(ROOT / "conformance"))
    import run as kit

    with pytest.raises(kit.ProfileError, match=message):
        kit.load_probe(probe)


def test_load_probe_reads_stream_fields() -> None:
    sys.path.insert(0, str(ROOT / "conformance"))
    import run as kit

    probe = kit.load_probe({"name": "s", "argv": ["watch"], "kind": "stream", "deadline_seconds": 2, "signal": "INT", "after_lines": 3})
    assert (probe.kind, probe.deadline_seconds, probe.sigint_after_lines) == (kit.ProbeKind.STREAM, 2.0, 3)
