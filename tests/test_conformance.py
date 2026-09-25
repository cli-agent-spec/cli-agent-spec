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
