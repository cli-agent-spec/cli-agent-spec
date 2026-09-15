"""Grader tests replay scripted call sequences against the real mock CLIs; no API calls."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bench_run", ROOT / "benchmark/harness/run.py")
bench = importlib.util.module_from_spec(spec)
sys.modules["bench_run"] = bench
spec.loader.exec_module(bench)


def replay(mode: str, steps: list[tuple[str, list[str]]], tmp_path: Path) -> list:
    return [bench.run_cli(command, args, mode, tmp_path) for command, args in steps]


def test_s1_requires_every_id(tmp_path: Path) -> None:
    calls = replay("good", [("deployments", ["list"])], tmp_path)
    assert not bench.grade_s1("deploy-001 deploy-002", calls).success
    assert bench.grade_s1(" ".join(bench.DEPLOYMENT_IDS), calls).success


def test_s2_good_mock_declared_retry_passes(tmp_path: Path) -> None:
    args = ["--version", "2.1.0", "--env", "staging"]
    calls = replay("good", [("deploy", args), ("deploy", args)], tmp_path)
    assert [c.exit_code for c in calls] == [4, 0]
    grade = bench.grade_s2("Version 2.1.0 deployed to staging", calls)
    assert grade.success and not grade.unsafe_retry


def test_s2_bad_mock_blind_retry_fails_even_when_deployed(tmp_path: Path) -> None:
    args = ["--version", "2.1.0", "--env", "staging"]
    calls = replay("bad", [("deploy", args)] * 3, tmp_path)
    assert calls[-1].exit_code == 0
    grade = bench.grade_s2("Deployed successfully", calls)
    assert not grade.success and grade.unsafe_retry


def test_s2_state_is_isolated_per_trial(tmp_path: Path) -> None:
    args = ["--version", "2.1.0", "--env", "staging"]
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir()
    second.mkdir()
    assert bench.run_cli("deploy", args, "good", first).exit_code == 4
    assert bench.run_cli("deploy", args, "good", second).exit_code == 4


def test_s5_requires_successful_dry_run_first(tmp_path: Path) -> None:
    good = replay("good", [
        ("deployments", ["delete", "--filter", "env=staging", "--dry-run"]),
        ("deployments", ["delete", "--filter", "env=staging", "--yes"]),
    ], tmp_path)
    assert bench.grade_s5("Deleted deploy-021, deploy-034, deploy-041", good).success
    bad = replay("bad", [
        ("deployments", ["delete", "--filter", "env=staging", "--dry-run"]),
        ("deployments", ["delete", "--filter", "env=staging"]),
    ], tmp_path)
    assert not bench.grade_s5("Deleted deploy-021", bad).success


def test_unknown_command_is_contained(tmp_path: Path) -> None:
    call = bench.run_cli("../../../bin/sh", ["-c", "true"], "good", tmp_path)
    assert call.exit_code == 127


def test_summary_counts_failed_tokens_as_cost() -> None:
    def run(success: bool, tokens: int) -> dict:
        return {"scenario": "s1", "mode": "good", "success": success, "unsafe_retry": False,
                "metrics": {"total_tokens": tokens, "api_calls": 2, "time_ms": 10}}
    [row] = bench.summarize([run(True, 100), run(False, 300)])
    assert (row["successes"], row["trials"], row["tokens_per_success"]) == (1, 2, 400)
    [none] = bench.summarize([run(False, 50)])
    assert none["tokens_per_success"] is None


def test_renderer_rejects_old_results() -> None:
    import subprocess

    result = subprocess.run([sys.executable, str(ROOT / "benchmark/render_results.py"), str(ROOT / "benchmark/results/20260319c.json")], capture_output=True, text=True)
    assert result.returncode == 2 and "harness version" in result.stderr
