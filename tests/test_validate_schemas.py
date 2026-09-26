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


def test_exit_code_entry_missing_required_fields_is_classified(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        **Invalid — missing required fields**
        ```json
        {"name": "NOT_FOUND", "description": "Target not found"}
        ```
        """)
    stats = vs.new_stats()
    assert vs.check_example_file(path, validators, stats) == []
    assert stats["expected_invalid"] == 1


def test_object_with_foreign_fields_is_not_an_exit_code_entry(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"name": "--live", "type": "boolean", "description": "Execute for real"}
        ```
        """)
    stats = vs.new_stats()
    assert vs.check_example_file(path, validators, stats) == []
    assert stats["unclassified"] == 1


def test_standalone_error_detail_is_validated(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"code": "auth_error", "message": "Authentication failed"}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert [p.kind for p in problems] == ["EXAMPLE"]
    assert vs.ERROR_DETAIL in problems[0].message


def test_object_with_foreign_fields_is_not_an_error_detail(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"level": "warn", "code": "DEPRECATED", "message": "Use new-sub"}
        ```
        """)
    stats = vs.new_stats()
    assert vs.check_example_file(path, validators, stats) == []
    assert stats["unclassified"] == 1


def test_failure_mode_entry_is_validated(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"id": 36, "title": "Pager Blocking", "path": "challenges/x.md", "part": "01-x", "status": "merged"}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert [p.kind for p in problems] == ["EXAMPLE"]
    assert vs.FAILURE_MODE_ENTRY in problems[0].message


def test_meta_fragment_may_omit_required_meta_fields(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"meta": {"request_id": "req_01"}}
        ```
        """)
    stats = vs.new_stats()
    assert vs.check_example_file(path, validators, stats) == []
    assert stats["validated"] == 1


def test_meta_fragment_nested_objects_are_fully_validated(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"meta": {"pagination": {"total": 3}}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert problems and {p.kind for p in problems} == {"EXAMPLE"}
    assert all("/meta/pagination" in p.message for p in problems)


def test_meta_timestamp_must_be_a_date_time(tmp_path: Path, validators) -> None:
    path = write_md(tmp_path, """\
        ```json
        {"meta": {"timestamp": "yesterday"}}
        ```
        """)
    problems = vs.check_example_file(path, validators, vs.new_stats())
    assert [p.kind for p in problems] == ["EXAMPLE"]
    assert "date-time" in problems[0].message


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
        {"ok": true, "data": {"schema_version": "3.0", "framework_version": "1", "etag": "x",
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
