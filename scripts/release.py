"""The release bot's rules: decide whether a spec release is due, write it, and check it.

Usage:
  uv run --no-project python scripts/release.py quiet
  uv run --no-project python scripts/release.py plan [--dry-run] [--check-blockers] [--github-output FILE]
  uv run --no-project python scripts/release.py apply --version 1.10.0 --date 2026-10-05
  uv run --no-project python scripts/release.py check --version 1.10.0
  uv run --no-project python scripts/release.py notes --version 1.10.0

quiet  prints the policy's quiet_minutes: how long master must stay unchanged after a push
plan   prints the decision as JSON: release (with the next version) or skip (with why)
apply  dates the Unreleased entries as the new version and rewrites the policy's
       version_lines; it commits nothing
check  exits 1 unless the checkout is a finished release commit for the version
notes  prints the version's CHANGELOG section, the body of its GitHub release

The spec version lives only in CHANGELOG.md: its newest "## X.Y.Z — YYYY-MM-DD" heading.
A release bumps MINOR when a path matching the policy's minor_paths changed since the
previous tag, else PATCH. The bot never bumps MAJOR: that is a person's decision.

Exit codes: 0 done (a plan may decide to skip); 1 a check failed; 2 bad input, such as a
malformed policy, version, or CHANGELOG.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNRELEASED = "## Unreleased"
BLOCKER_LABEL = "release-blocker"
_RELEASE_HEADING = re.compile(r"^## (?P<version>\d+\.\d+\.\d+)(?: — (?P<date>\d{4}-\d\d-\d\d))?\s*$")
_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_MODES = ("off", "dry-run", "release")
_POLICY_KEYS = {"mode", "min_days_between", "quiet_minutes", "minor_paths", "version_lines"}
_LINE_KEYS = {"file", "pattern", "replace"}
_MAX_QUIET = 300  # a GitHub job runs at most 6 hours; leave room for the rest of the run


class ReleaseError(Exception):
    """A malformed policy, version, or CHANGELOG, or a repo the bot can't read"""


@dataclass(frozen=True, slots=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, text: str) -> Version:
        m = _VERSION.fullmatch(text)
        if m is None:
            raise ReleaseError(f"a spec version is MAJOR.MINOR.PATCH, got {text!r}")
        return cls(int(m[1]), int(m[2]), int(m[3]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def tag(self) -> str:
        return f"v{self}"

    def bump(self, part: str) -> Version:
        if part == "minor":
            return Version(self.major, self.minor + 1, 0)
        return Version(self.major, self.minor, self.patch + 1)


@dataclass(frozen=True, slots=True)
class VersionLine:
    file: str
    pattern: re.Pattern[str]
    replace: str


@dataclass(frozen=True, slots=True)
class Policy:
    mode: str
    min_days_between: int
    quiet_minutes: int
    minor_paths: tuple[str, ...]  # fnmatch patterns; "*" also matches "/"
    version_lines: tuple[VersionLine, ...]

    @classmethod
    def load(cls, path: Path) -> Policy:
        if not path.is_file():
            raise ReleaseError(f"no release policy at {path}")
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        if unknown := set(raw) - _POLICY_KEYS:
            raise ReleaseError(f"{path.name}: unknown keys {sorted(unknown)}")
        mode = raw.get("mode")
        if mode not in _MODES:
            raise ReleaseError(f"{path.name}: mode must be one of {_MODES}, got {mode!r}")
        days = raw.get("min_days_between")
        if not isinstance(days, int) or isinstance(days, bool) or days < 0:
            raise ReleaseError(f"{path.name}: min_days_between must be an integer >= 0")
        quiet = raw.get("quiet_minutes")
        if not isinstance(quiet, int) or isinstance(quiet, bool) or not 0 <= quiet <= _MAX_QUIET:
            raise ReleaseError(f"{path.name}: quiet_minutes must be an integer in 0..{_MAX_QUIET}")
        paths = raw.get("minor_paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
            raise ReleaseError(f"{path.name}: minor_paths must be a non-empty list of patterns")
        lines = []
        for i, entry in enumerate(raw.get("version_lines", [])):
            if not isinstance(entry, dict) or set(entry) != _LINE_KEYS:
                raise ReleaseError(f"{path.name}: version_lines[{i}] takes exactly {sorted(_LINE_KEYS)}")
            if not all(isinstance(entry[k], str) for k in _LINE_KEYS):
                raise ReleaseError(f"{path.name}: version_lines[{i}] values must be strings")
            try:
                pattern = re.compile(entry["pattern"])
            except re.error as exc:
                raise ReleaseError(f"{path.name}: version_lines[{i}].pattern: {exc}") from None
            lines.append(VersionLine(entry["file"], pattern, entry["replace"]))
        return cls(mode, days, quiet, tuple(paths), tuple(lines))


@dataclass(frozen=True, slots=True)
class Changelog:
    text: str

    def unreleased(self) -> list[str]:
        """The lines of the Unreleased section, blank lines included"""
        lines = self.text.splitlines()
        starts = [i for i, line in enumerate(lines) if line.rstrip() == UNRELEASED]
        if len(starts) != 1:
            raise ReleaseError(f"CHANGELOG.md needs exactly one '{UNRELEASED}' heading, found {len(starts)}")
        start = starts[0] + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
        return lines[start:end]

    def has_unreleased(self) -> bool:
        return any(line.strip() for line in self.unreleased())

    def releases(self) -> list[tuple[Version, dt.date | None]]:
        """Every release heading, newest first"""
        found = []
        for line in self.text.splitlines():
            if m := _RELEASE_HEADING.match(line):
                date = None if m["date"] is None else dt.date.fromisoformat(m["date"])
                found.append((Version.parse(m["version"]), date))
        if not found:
            raise ReleaseError("CHANGELOG.md has no '## X.Y.Z — YYYY-MM-DD' release heading")
        return found

    def current(self) -> Version:
        return self.releases()[0][0]

    def latest_date(self) -> dt.date | None:
        return next((date for _, date in self.releases() if date is not None), None)

    def section(self, version: Version) -> str:
        lines = self.text.splitlines()
        heads = [i for i, line in enumerate(lines) if (m := _RELEASE_HEADING.match(line)) and m["version"] == str(version)]
        if len(heads) != 1:
            raise ReleaseError(f"CHANGELOG.md needs exactly one '## {version}' heading, found {len(heads)}")
        start = heads[0] + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
        return "\n".join(lines[start:end]).strip("\n") + "\n"


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise ReleaseError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def has_tag(repo: Path, tag: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], capture_output=True, text=True
    )
    return proc.returncode == 0


def changed_paths(repo: Path, since: Version) -> list[str]:
    if not has_tag(repo, since.tag):
        raise ReleaseError(f"no tag {since.tag} for the newest CHANGELOG release; fetch tags (fetch-depth: 0)")
    return git(repo, "diff", "--name-only", f"{since.tag}..HEAD").splitlines()


def open_blockers(repo: Path) -> list[str]:
    proc = subprocess.run(
        ["gh", "issue", "list", "--label", BLOCKER_LABEL, "--state", "open", "--json", "number,title"],
        capture_output=True,
        text=True,
        cwd=repo,
    )
    if proc.returncode != 0:
        raise ReleaseError(f"gh issue list failed: {proc.stderr.strip()}")
    return [f"#{i['number']} {i['title']}" for i in json.loads(proc.stdout)]


def plan(repo: Path, policy: Policy, today: dt.date, dry_run: bool, blockers: bool) -> dict[str, str]:
    mode = "dry-run" if dry_run and policy.mode != "off" else policy.mode
    decision = {"mode": mode, "date": today.isoformat()}
    changelog = Changelog((repo / "CHANGELOG.md").read_text(encoding="utf-8"))
    current = changelog.current()
    decision["current"] = str(current)

    def skip(reason: str) -> dict[str, str]:
        return decision | {"action": "skip", "reason": reason}

    if mode == "off":
        return skip("the policy's mode is off")
    if not changelog.has_unreleased():
        return skip("nothing under Unreleased")
    last = changelog.latest_date()
    if last is not None and (today - last).days < policy.min_days_between:
        return skip(f"the latest release is {(today - last).days} day(s) old; the policy waits {policy.min_days_between}")
    if blockers and (found := open_blockers(repo)):
        return skip(f"open '{BLOCKER_LABEL}' issues: {', '.join(found)}")
    contract = [p for p in changed_paths(repo, current) if any(fnmatch.fnmatch(p, g) for g in policy.minor_paths)]
    if contract:
        version = current.bump("minor")
        why = f"a minor bump: {len(contract)} contract file(s) changed since {current.tag}, first {contract[0]}"
    else:
        version = current.bump("patch")
        why = f"a patch bump: no minor_paths file changed since {current.tag}"
    return decision | {
        "action": "release",
        "version": str(version),
        "base": git(repo, "rev-parse", "HEAD").strip(),
        "reason": f"{version} is {why}",
    }


def replace_once(text: str, pattern: re.Pattern[str], new: str, where: str) -> str:
    hits = len(pattern.findall(text))
    if hits != 1:
        raise ReleaseError(f"{where}: {pattern.pattern!r} matches {hits} times, want exactly 1")
    return pattern.sub(lambda _: new, text)


def apply(repo: Path, policy: Policy, version: Version, date: dt.date) -> list[str]:
    path = repo / "CHANGELOG.md"
    changelog = Changelog(path.read_text(encoding="utf-8"))
    current = changelog.current()
    if version <= current:
        raise ReleaseError(f"{version} is not after the newest release, {current}")
    if not changelog.has_unreleased():
        raise ReleaseError("nothing under Unreleased to release")
    heading = f"{UNRELEASED}\n\n## {version} — {date.isoformat()}"
    path.write_text(
        replace_once(changelog.text, re.compile(rf"(?m)^{re.escape(UNRELEASED)}$"), heading, "CHANGELOG.md"),
        encoding="utf-8",
    )
    changed = ["CHANGELOG.md"]
    values = {"version": str(version), "minor": f"{version.major}.{version.minor}", "date": date.isoformat()}
    for line in policy.version_lines:
        target = repo / line.file
        if not target.is_file():
            raise ReleaseError(f"version_lines names {line.file}, which doesn't exist")
        text = replace_once(target.read_text(encoding="utf-8"), line.pattern, line.replace.format(**values), line.file)
        target.write_text(text, encoding="utf-8")
        changed.append(line.file)
    return changed


def check(repo: Path, version: Version) -> list[str]:
    """Why the checkout is not a finished release commit for version; empty when it is"""
    changelog = Changelog((repo / "CHANGELOG.md").read_text(encoding="utf-8"))
    problems = []
    if changelog.has_unreleased():
        problems.append("Unreleased still holds entries")
    newest, date = changelog.releases()[0]
    if newest != version:
        problems.append(f"the newest CHANGELOG release is {newest}, not {version}")
    elif date is None:
        problems.append(f"'## {version}' has no date")
    elif not changelog.section(version).strip():
        problems.append(f"'## {version}' is empty")
    if has_tag(repo, version.tag):
        problems.append(f"tag {version.tag} already exists")
    return problems


def github_output(decision: dict[str, str]) -> str:
    """``key=value`` lines for $GITHUB_OUTPUT. A reason can quote an issue title, and a
    newline in it would otherwise let the title set outputs such as action."""
    return "".join(f"{k}={' '.join(v.splitlines())}\n" for k, v in decision.items())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("quiet", "plan", "apply", "check", "notes"):
        p = sub.add_parser(name)
        p.add_argument("--repo", type=Path, default=ROOT, help="checkout of master")
        p.add_argument("--policy", type=Path, help="default: .github/release-policy.toml in --repo")
    p_plan = sub.choices["plan"]
    p_plan.add_argument("--today", type=dt.date.fromisoformat, help="YYYY-MM-DD; default: today in UTC")
    p_plan.add_argument("--dry-run", action="store_true", help="plan as dry-run whatever the policy's mode")
    p_plan.add_argument("--check-blockers", action="store_true", help=f"skip while '{BLOCKER_LABEL}' issues are open")
    p_plan.add_argument("--github-output", type=Path, help="also append the decision as key=value lines")
    for name in ("apply", "check", "notes"):
        sub.choices[name].add_argument("--version", required=True, help="the planned version, e.g. 1.10.0")
    sub.choices["apply"].add_argument("--date", required=True, type=dt.date.fromisoformat, help="YYYY-MM-DD")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    try:
        policy = Policy.load(args.policy or repo / ".github" / "release-policy.toml")
        if args.command == "quiet":
            print(policy.quiet_minutes)
        elif args.command == "plan":
            today = args.today or dt.datetime.now(dt.UTC).date()
            decision = plan(repo, policy, today, args.dry_run, args.check_blockers)
            print(json.dumps(decision, indent=2))
            if args.github_output:
                with args.github_output.open("a", encoding="utf-8") as out:
                    out.write(github_output(decision))
        elif args.command == "apply":
            for changed in apply(repo, policy, Version.parse(args.version), args.date):
                print(f"updated {changed}")
        elif args.command == "check":
            problems = check(repo, Version.parse(args.version))
            for problem in problems:
                print(f"FAIL {problem}")
            if problems:
                return 1
            print(f"PASS release commit for {args.version}")
        else:
            changelog = Changelog((repo / "CHANGELOG.md").read_text(encoding="utf-8"))
            sys.stdout.write(changelog.section(Version.parse(args.version)))
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
