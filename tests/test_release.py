import datetime as dt
import subprocess
from pathlib import Path

import pytest

import release
from release import Changelog, Policy, ReleaseError, Version

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 10, 5)

POLICY = """\
mode = "release"
min_days_between = 0
quiet_minutes = 30
minor_paths = ["requirements/*", "schemas/*"]

[[version_lines]]
file = "README.md"
pattern = 'CLI Agent Spec v\\d+\\.\\d+(?= —)'
replace = "CLI Agent Spec v{minor}"
"""

CHANGELOG = """\
# Changelog

## Versioning

- Spec version

## Unreleased

### Something changed

- An entry

## 1.9.0 — 2026-09-30

### Earlier

- Old entry

## 1.6.0

- Undated
"""


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_repo(tmp_path: Path, changelog: str = CHANGELOG, policy: str = POLICY) -> Path:
    repo = tmp_path / "repo"
    (repo / ".github").mkdir(parents=True)
    (repo / "requirements").mkdir()
    (repo / ".github" / "release-policy.toml").write_text(policy, encoding="utf-8")
    (repo / "README.md").write_text("*CLI Agent Spec v1.9 — 75 failure modes*\n", encoding="utf-8")
    (repo / "requirements" / "f-001.md").write_text("req\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    run(repo, "init", "-q", "-b", "master")
    run(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "base", "--allow-empty")
    run(repo, "add", "-A")
    run(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "1.9.0")
    run(repo, "tag", "v1.9.0")
    (repo / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return repo


def commit(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    run(repo, "add", "-A")
    run(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", f"change {path}")


def load(repo: Path) -> Policy:
    return Policy.load(repo / ".github" / "release-policy.toml")


def test_repo_policy_loads_and_its_version_lines_match_once() -> None:
    policy = load(ROOT)
    assert policy.mode in ("off", "dry-run", "release")
    for line in policy.version_lines:
        text = (ROOT / line.file).read_text(encoding="utf-8")
        assert len(line.pattern.findall(text)) == 1, line.file


def test_repo_changelog_parses() -> None:
    changelog = Changelog((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert changelog.current() >= Version(1, 9, 0)


def test_contract_change_is_minor(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    commit(repo, "requirements/f-001.md", "req, changed\n")
    decision = release.plan(repo, load(repo), TODAY, dry_run=False, blockers=False)
    assert decision["action"] == "release"
    assert decision["version"] == "1.10.0"
    assert "requirements/f-001.md" in decision["reason"]


def test_prose_only_change_is_patch(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    commit(repo, "guides/intro.md", "prose\n")
    decision = release.plan(repo, load(repo), TODAY, dry_run=False, blockers=False)
    assert decision["version"] == "1.9.1"


def test_empty_unreleased_skips(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, changelog=CHANGELOG.replace("### Something changed\n\n- An entry\n\n", ""))
    decision = release.plan(repo, load(repo), TODAY, dry_run=False, blockers=False)
    assert decision == decision | {"action": "skip", "reason": "nothing under Unreleased"}


def test_min_days_between_skips(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, policy=POLICY.replace("min_days_between = 0", "min_days_between = 7"))
    decision = release.plan(repo, load(repo), TODAY, dry_run=False, blockers=False)
    assert decision["action"] == "skip"
    assert "5 day(s) old" in decision["reason"]


def test_off_mode_skips_and_dry_run_flag_downgrades(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert release.plan(repo, load(repo), TODAY, dry_run=True, blockers=False)["mode"] == "dry-run"
    off = make_repo(tmp_path / "off", policy=POLICY.replace('mode = "release"', 'mode = "off"'))
    decision = release.plan(off, load(off), TODAY, dry_run=True, blockers=False)
    assert (decision["mode"], decision["action"]) == ("off", "skip")


def test_missing_tag_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    run(repo, "tag", "-d", "v1.9.0")
    with pytest.raises(ReleaseError, match="no tag v1.9.0"):
        release.plan(repo, load(repo), TODAY, dry_run=False, blockers=False)


def test_apply_dates_unreleased_and_passes_check(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    changed = release.apply(repo, load(repo), Version(1, 10, 0), TODAY)
    assert changed == ["CHANGELOG.md", "README.md"]
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## Unreleased\n\n## 1.10.0 — 2026-10-05\n\n### Something changed\n\n- An entry\n\n## 1.9.0" in text
    assert (repo / "README.md").read_text(encoding="utf-8") == "*CLI Agent Spec v1.10 — 75 failure modes*\n"
    assert release.check(repo, Version(1, 10, 0)) == []
    notes = Changelog(text).section(Version(1, 10, 0))
    assert notes == "### Something changed\n\n- An entry\n"


def test_check_reports_an_unfinished_release(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert release.check(repo, Version(1, 9, 0)) == [
        "Unreleased still holds entries",
        "tag v1.9.0 already exists",
    ]


def test_apply_refuses_an_older_version(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    with pytest.raises(ReleaseError, match="not after the newest release"):
        release.apply(repo, load(repo), Version(1, 9, 0), TODAY)


def test_version_line_must_match_once(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("no footer\n", encoding="utf-8")
    with pytest.raises(ReleaseError, match="matches 0 times"):
        release.apply(repo, load(repo), Version(1, 10, 0), TODAY)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (('mode = "release"', 'mode = "on"'), "mode must be one of"),
        (("quiet_minutes = 30", "quiet_minutes = 301"), "quiet_minutes"),
        (('minor_paths = ["requirements/*", "schemas/*"]', "minor_paths = []"), "minor_paths"),
        (("quiet_minutes = 30", "quiet_minutes = 30\nbump = 1"), "unknown keys"),
    ],
)
def test_malformed_policy_fails(tmp_path: Path, change: tuple[str, str], message: str) -> None:
    path = tmp_path / "policy.toml"
    path.write_text(POLICY.replace(*change), encoding="utf-8")
    with pytest.raises(ReleaseError, match=message):
        Policy.load(path)


def test_github_output_flattens_newlines() -> None:
    assert release.github_output({"reason": "a\naction=release"}) == "reason=a action=release\n"
