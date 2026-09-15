import json
import subprocess
import sys
from pathlib import Path

import build_failure_index as bfi

ROOT = Path(__file__).resolve().parents[1]


def test_committed_index_is_current() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/build_failure_index.py"), "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_index_validates_and_is_consistent() -> None:
    index = bfi.build_index()
    assert bfi.schema_problems(index) == []
    entries = {e["id"]: e for e in index["failure_modes"]}
    active = {i for i, e in entries.items() if e["status"] == "active"}
    assert index["active_count"] == len(active)
    for entry in entries.values():
        if entry["status"] == "merged":
            assert entry["merged_into"] in active
        elif entry["tier"] == "C":
            assert entry["fallback"]
        else:
            assert "fallback" not in entry


def test_known_mappings() -> None:
    entries = {e["id"]: e for e in bfi.build_index()["failure_modes"]}
    assert entries[36] == {**entries[36], "status": "merged", "merged_into": 10}
    assert "REQ-F-001" in entries[1]["requirements"]
    assert 3 in entries[10]["triage_rows"]
    assert "REQ-O-004" in entries[76]["requirements"]


def test_workaround_survives_shell_comments_in_code() -> None:
    entries = {e["id"]: e for e in bfi.build_index()["failure_modes"]}
    workaround = entries[10]["workaround"]
    assert workaround.startswith("**Signature:**")
    assert "**Limitation:**" in workaround


def test_stdout_mode_matches_file() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/build_failure_index.py"), "--stdout"], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == json.loads((ROOT / "challenges/index.json").read_text())
