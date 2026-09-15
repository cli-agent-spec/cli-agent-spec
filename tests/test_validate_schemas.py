import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import validate_schemas as vs

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def validators():
    schemas = vs.load_schemas()
    return vs.build_validators(schemas, vs.build_registry(schemas))


def write_md(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "doc.md"
    path.write_text(textwrap.dedent(body))
    return path


def test_corpus_is_clean() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_schemas.py"), "--json"], capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert report["errors"] == 0, json.dumps(report, indent=2)
    assert result.returncode == 0
    assert report["stats"]["validated"] > 150


def test_schema_files_pass_structural_checks() -> None:
    schemas = vs.load_schemas()
    assert vs.check_schemas(schemas, vs.build_registry(schemas)) == []


def test_envelope_ok_must_match_exit_code(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"ok": true, "data": null, "error": null, "warnings": [], "meta": {"exit_code": 5, "duration_ms": 1}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert any("ok" in p.message for p in problems)


def test_envelope_requires_exit_code(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"ok": true, "data": {}, "error": null, "warnings": [], "meta": {"duration_ms": 1}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert any("exit_code" in p.message for p in problems)


def test_string_warning_is_rejected(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"ok": true, "data": {}, "error": null, "warnings": ["deprecated"], "meta": {"exit_code": 0, "duration_ms": 1}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert any("warnings/0" in p.message for p in problems)


def test_invalid_label_that_validates_is_reported(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        **Invalid — looks wrong but is not**
        ```json
        {"description": "Done", "retryable": false, "side_effects": "complete"}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert [p.kind for p in problems] == ["INVALID EXAMPLE PASSES"]


def test_invalid_label_that_fails_is_accepted(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        **Invalid — invariant violation**
        ```json
        {"description": "Timed out", "retryable": true, "side_effects": "partial"}
        ```
        """)
    assert vs.check_example_file(path, validators, vs.new_stats()) == []


def test_unparseable_json_block_is_reported(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        { "data": [...] }
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert [p.kind for p in problems] == ["UNPARSEABLE"]


def test_jsonl_block_validates_each_line(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```jsonl
        {"_cmd": "account.create"}
        {"_cmd": "Account.Create"}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert len(problems) == 1 and "_cmd" in problems[0].message


def test_dispatch_opts_accept_integers(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"_cmd": "deployments.list", "_opts": {"limit": 5, "draft": true}}
        ```
        """)
    assert vs.check_example_file(path, validators, vs.new_stats()) == []


def test_manifest_inside_envelope_is_validated(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"ok": true, "data": {"schema_version": "1.0", "framework_version": "1", "etag": "x",
          "commands": {"run": {"description": "Run", "flags": {}, "exit_codes": {}}}},
         "error": null, "warnings": [], "meta": {"exit_code": 0, "duration_ms": 1}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert any("danger_level" in p.message for p in problems)
    assert any("required_scopes" in p.message for p in problems)


def test_common_mistakes_section_is_skipped(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ## Common mistakes

        ```json
        {"_cmd": "account/create"}
        ```
        """)
    stats = vs.new_stats()
    assert vs.check_example_file(path, validators, stats) == []
    assert stats["blocks"] == 0
