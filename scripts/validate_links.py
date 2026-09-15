"""Validate cross-links and structural consistency of the CLI Agent Spec corpus.

Checks, each reported separately:

  links        relative markdown links resolve to a file
  symmetry     schema "Used by" rows and requirement "## Schema" links agree
  indexes      every corpus file is listed in its index and every index row resolves
  sections     failure mode, requirement, and schema doc files carry required sections in order
  counts       prose counters match the corpus on disk
  snippets     every embedded extract_envelope copy matches the canonical block in triage.md
  levels       requirements/levels.md, priorities, and the index Level column agree

Usage:
  uv run scripts/validate_links.py [--json] [--only CHECK ...]

Exit codes: 0 no errors, 1 at least one error, 2 usage error.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from spec_corpus import (
    ROOT,
    FailureModeFile,
    RequirementFile,
    Tier,
    active_failure_modes,
    failure_mode_files,
    requirement_files,
    schema_pairs,
    section_body,
    strip_fenced_code,
)


@dataclass(frozen=True)
class Problem:
    check: str
    kind: str
    path: str
    message: str

    def render(self) -> str:
        return f"{self.kind}: {self.path} — {self.message}"


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------

_LINK = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
_EXCLUDED_PREFIXES = ("site/", "tmp/", "posts/", ".gstack/", ".idea/", ".claude/plugins/")
# Skill bundles mirror root files (kept identical by sync-skill-references.sh --check);
# their links to directories outside the bundle are checked once, at the root copy.
_BUNDLE_MIRROR = re.compile(r"^skills/[^/]+/references/")


def tracked_markdown() -> tuple[Path, ...]:
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return tuple(
        ROOT / name
        for name in sorted(set(listed))
        if not name.startswith(_EXCLUDED_PREFIXES) and not _BUNDLE_MIRROR.match(name) and (ROOT / name).is_file()
    )


def check_links() -> list[Problem]:
    problems: list[Problem] = []
    for path in tracked_markdown():
        prose = strip_fenced_code(path.read_text(encoding="utf-8"))
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for target in _LINK.findall(prose):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                problems.append(Problem("links", "BROKEN", _rel(path), f"link target not found: {target}"))
    return problems


# ---------------------------------------------------------------------------
# symmetry
# ---------------------------------------------------------------------------

_REQ_ID = re.compile(r"REQ-([FCO])-(\d{3})")
_SCHEMA_LINK = re.compile(r"\]\((?:\.\./)?schemas/([\w-]+)\.(?:md|json)")


def _requirement_index() -> dict[str, RequirementFile]:
    return {str(r.id): r for r in requirement_files()}


def check_symmetry() -> list[Problem]:
    problems: list[Problem] = []
    requirements = _requirement_index()
    for pair in schema_pairs():
        used_by = [line for line in pair.md_path.read_text(encoding="utf-8").splitlines() if "Used by" in line]
        for line in used_by:
            for tier, number in _REQ_ID.findall(line):
                req_id = f"REQ-{tier}-{number}"
                req = requirements.get(req_id)
                if req is None:
                    problems.append(Problem("symmetry", "MISSING FILE", _rel(pair.md_path), f"'Used by' names {req_id}, which has no file"))
                    continue
                if not re.search(rf"{re.escape(pair.name)}\.(json|md)", req.text):
                    problems.append(Problem("symmetry", "MISSING BACK-LINK", _rel(req.path), f"no link to {pair.name}.json or {pair.name}.md (listed in {pair.md_path.name} 'Used by')"))
    known = {pair.name for pair in schema_pairs()}
    for req in requirements.values():
        for name in sorted(set(_SCHEMA_LINK.findall(section_body(req.text, "## Schema")))):
            if name not in known and name not in {"index", "codegen-guide"}:
                problems.append(Problem("symmetry", "MISSING SCHEMA FILE", _rel(req.path), f"## Schema links to schemas/{name}, which does not exist"))
    return problems


# ---------------------------------------------------------------------------
# indexes
# ---------------------------------------------------------------------------

_MD_TARGET = re.compile(r"\]\(([\w./-]+\.(?:md|json))\)")


def _index_problems(index: Path, expected: list[Path], suffix: str) -> list[Problem]:
    problems: list[Problem] = []
    text = index.read_text(encoding="utf-8")
    linked = {(index.parent / target).resolve() for target in _MD_TARGET.findall(text) if target.endswith(suffix)}
    for target in sorted(linked):
        if not target.exists():
            problems.append(Problem("indexes", "MISSING", _rel(index), f"links to {target.name}, which does not exist"))
    for path in expected:
        if path.resolve() not in linked:
            problems.append(Problem("indexes", "UNLISTED", _rel(index), f"{_rel(path)} is not listed"))
    return problems


def check_indexes() -> list[Problem]:
    problems: list[Problem] = []
    problems += _index_problems(ROOT / "requirements/index.md", [r.path for r in requirement_files()], ".md")
    problems += _index_problems(ROOT / "schemas/index.md", [p.json_path for p in schema_pairs()], ".json")
    problems += _index_problems(ROOT / "challenges/index.md", [f.path for f in active_failure_modes()], ".md")
    parts: dict[Path, list[Path]] = collections.defaultdict(list)
    for fm in active_failure_modes():
        parts[fm.path.parent].append(fm.path)
    for part, files in sorted(parts.items()):
        problems += _index_problems(part / "index.md", files, ".md")
    guides = [p for p in sorted((ROOT / "guides").glob("*.md")) if p.name != "index.md"]
    problems += _index_problems(ROOT / "guides/index.md", guides, ".md")
    return problems


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

FAILURE_MODE_SECTIONS = ("### The Problem", "### Impact", "### Solutions", "### Evaluation", "### Agent Workaround")
REQUIREMENT_SECTIONS = ("## Description", "## Acceptance Criteria", "## Schema", "## Wire Format", "## Example", "## Related")
SCHEMA_DOC_SECTIONS = ("## Purpose", "## Examples", "## Common mistakes", "## Agent interpretation", "## Coding agent notes", "## Implementation notes")

TIER_GLOSSES = (
    "**Tier:** A (one safe command, no branching)",
    "**Tier:** B (one observable check, then one command)",
    "**Tier:** C (stateful logic; weak models apply the fallback below)",
)


def _headings(text: str) -> list[str]:
    return [line.rstrip() for line in strip_fenced_code(text).splitlines() if line.startswith("#")]


def _order_problem(path: Path, headings: list[str], required: tuple[str, ...]) -> Problem | None:
    positions: list[int] = []
    missing: list[str] = []
    for section in required:
        if section in headings:
            positions.append(headings.index(section))
        else:
            missing.append(section)
    if missing:
        return Problem("sections", "INCOMPLETE", _rel(path), "missing: " + ", ".join(repr(m) for m in missing))
    if positions != sorted(positions):
        return Problem("sections", "OUT OF ORDER", _rel(path), "required order: " + " → ".join(required))
    return None


def _failure_mode_problems(fm: FailureModeFile) -> list[Problem]:
    text = fm.text
    problems: list[Problem] = []
    order = _order_problem(fm.path, _headings(text), FAILURE_MODE_SECTIONS)
    if order:
        problems.append(order)
    workaround = text.split("### Agent Workaround", 1)[-1]
    lines = workaround.splitlines()
    tier_lines = [line for line in lines if line.startswith("**Tier:**")]
    for marker in ("**Signature:**", "**Tier:**", "**Limitation:**"):
        if not any(line.startswith(marker) for line in lines):
            problems.append(Problem("sections", "INCOMPLETE", _rel(fm.path), f"Agent Workaround has no {marker} line"))
    signature = next((line for line in lines if line.startswith("**Signature:**")), None)
    first_content = next((line for line in lines if line.strip()), None)
    if signature is not None and first_content != signature:
        problems.append(Problem("sections", "OUT OF ORDER", _rel(fm.path), "Agent Workaround must open with the **Signature:** line"))
    if signature is not None and signature.rstrip().endswith("."):
        problems.append(Problem("sections", "STYLE", _rel(fm.path), "**Signature:** line ends with a period"))
    for line in tier_lines:
        if line.rstrip() not in TIER_GLOSSES:
            problems.append(Problem("sections", "NON-CANONICAL TIER", _rel(fm.path), f"{line.strip()!r} does not match a pinned gloss"))
    is_tier_c = any(line.startswith("**Tier:** C") for line in tier_lines)
    has_fallback = any(line.startswith("**Fallback:**") for line in lines)
    if is_tier_c and not has_fallback:
        problems.append(Problem("sections", "INCOMPLETE", _rel(fm.path), "Tier C requires a **Fallback:** line"))
    if has_fallback and not is_tier_c:
        problems.append(Problem("sections", "STRAY FALLBACK", _rel(fm.path), "only Tier C carries a **Fallback:** line"))
    return problems


def check_sections() -> list[Problem]:
    problems: list[Problem] = []
    for fm in active_failure_modes():
        problems += _failure_mode_problems(fm)
    for req in requirement_files():
        order = _order_problem(req.path, _headings(req.text), REQUIREMENT_SECTIONS)
        if order:
            problems.append(order)
    for pair in schema_pairs():
        text = pair.md_path.read_text(encoding="utf-8")
        headings = _headings(text)
        order = _order_problem(pair.md_path, headings, SCHEMA_DOC_SECTIONS)
        if order:
            problems.append(order)
            continue
        between = headings[headings.index("## Purpose") + 1: headings.index("## Examples")]
        if not any(h.startswith("## ") for h in between):
            problems.append(Problem("sections", "INCOMPLETE", _rel(pair.md_path), "no field or value table section between '## Purpose' and '## Examples'"))
        if "Used by" not in text.split("## Purpose", 1)[0]:
            problems.append(Problem("sections", "INCOMPLETE", _rel(pair.md_path), "title block has no 'Used by' line"))
    return problems


# ---------------------------------------------------------------------------
# counts
# ---------------------------------------------------------------------------

_PRIORITY = re.compile(r"^\*\*Tier:\*\*.*\*\*Priority:\*\* (P[0-3])", re.M)


@dataclass(frozen=True)
class Claim:
    path: str
    pattern: str   # regex with exactly one capturing group holding the integer
    actual: int
    label: str


def canonical_schema_names() -> tuple[str, ...]:
    """Schema names listed in the 'Canonical types' table of schemas/index.md."""
    body = section_body((ROOT / "schemas/index.md").read_text(encoding="utf-8"), "## Canonical types")
    if not body:
        raise SystemExit("schemas/index.md has no '## Canonical types' section")
    return tuple(re.findall(r"\]\(([\w-]+)\.json\)", body))


def corpus_counts() -> dict[str, int]:
    requirements = requirement_files()
    per_tier = collections.Counter(r.id.tier for r in requirements)
    priorities: collections.Counter[str] = collections.Counter()
    tier_priorities: dict[Tier, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for req in requirements:
        match = _PRIORITY.search(req.text)
        if match is None:
            raise SystemExit(f"{_rel(req.path)} has no **Priority:** on its Tier line")
        priorities[match.group(1)] += 1
        tier_priorities[req.id.tier][match.group(1)] += 1
    counts = {
        "failure_modes": len(active_failure_modes()),
        "requirements": len(requirements),
        "schemas": len(schema_pairs()),
        "canonical_schemas": len(canonical_schema_names()),
    }
    for tier in Tier:
        counts[f"tier_{tier.value}"] = per_tier[tier]
        for priority in ("P0", "P1", "P2", "P3"):
            counts[f"tier_{tier.value}_{priority}"] = tier_priorities[tier][priority]
    for priority in ("P0", "P1", "P2", "P3"):
        counts[priority] = priorities[priority]
    levels = requirement_levels()
    for n in (1, 2, 3):
        counts[f"level_{n}"] = sum(1 for level in levels.values() if level <= n)
    return counts


def count_claims() -> list[Claim]:
    c = corpus_counts()
    fm, reqs = c["failure_modes"], c["requirements"]
    claims = [
        Claim("README.md", r"\*\*(\d+) documented failure modes\*\*", fm, "failure modes bullet"),
        Claim("README.md", r"\*\*(\d+) requirements\*\*", reqs, "requirements bullet"),
        Claim("README.md", r"\*\*(\d+) canonical JSON schemas\*\*", c["canonical_schemas"], "schemas bullet"),
        Claim("README.md", r"\*\*F\*\* — Framework-Automatic \| (\d+)", c["tier_f"], "F tier row"),
        Claim("README.md", r"\*\*C\*\* — Command Contract \| (\d+)", c["tier_c"], "C tier row"),
        Claim("README.md", r"\*\*O\*\* — Opt-In \| (\d+)", c["tier_o"], "O tier row"),
        Claim("README.md", r"· (\d+) canonical schemas ·", c["canonical_schemas"], "footer schemas"),
        Claim("README.md", r"— (\d+) failure modes ·", fm, "footer failure modes"),
        Claim("README.md", r"· (\d+) requirements ·", reqs, "footer requirements"),
        Claim("AGENTS.md", r"Current corpus: (\d+) failure modes", fm, "corpus line"),
        Claim("AGENTS.md", r"Current corpus: \d+ failure modes, (\d+) requirements", reqs, "corpus line"),
        Claim("AGENTS.md", r"← (\d+) failure modes grouped", fm, "tree"),
        Claim("AGENTS.md", r"← (\d+) requirements across", reqs, "tree"),
        Claim("CLAUDE.md", r"It defines (\d+) failure modes", fm, "what this repo is"),
        Claim("CLAUDE.md", r"It defines \d+ failure modes, (\d+) requirements", reqs, "what this repo is"),
        Claim("CLAUDE.md", r"(\d+) canonical JSON schemas", c["canonical_schemas"], "what this repo is"),
        Claim("CLAUDE.md", r"`challenges/` — (\d+) failure modes", fm, "directories"),
        Claim("CLAUDE.md", r"`requirements/` — (\d+) requirements", reqs, "directories"),
        Claim("CLAUDE.md", r"`schemas/` — (\d+) canonical", c["canonical_schemas"], "directories"),
        Claim("challenges/index.md", r"All (\d+) failure modes", fm, "header"),
        Claim("challenges/index.md", r"(\d+) active failure modes", fm, "footer"),
        Claim("challenges/checklist.md", r"(\d+) documented failure modes", fm, "header"),
        Claim("requirements/index.md", r"(\d+) documented failure modes", fm, "intro"),
        Claim("requirements/index.md", r"\*\*(\d+) total\*\*", reqs, "total"),
        Claim("requirements/index.md", r"\*\*\d+ total\*\* &nbsp;\|&nbsp; (\d+) Framework-Automatic", c["tier_f"], "total F"),
        Claim("requirements/index.md", r"(\d+) Command Contract ·", c["tier_c"], "total C"),
        Claim("requirements/index.md", r"· (\d+) Opt-In", c["tier_o"], "total O"),
    ]
    for priority in ("P0", "P1", "P2", "P3"):
        claims.append(Claim("requirements/index.md", rf"\*\*By priority:\*\*.*?{priority}: (\d+)", c[priority], f"by priority {priority}"))
    for n in (1, 2, 3):
        claims.append(Claim("requirements/index.md", rf"\*\*By level\*\*.*?Level {n}: (\d+)", c[f"level_{n}"], f"by level {n}"))
        claims.append(Claim("requirements/levels.md", rf"(?m)^\| {n} \| [^|]+\| [^|]+\| (\d+) \|$", c[f"level_{n}"], f"level {n} size"))
    headers = {Tier.FRAMEWORK: "## Framework-Automatic (F)", Tier.COMMAND: "## Command Contract (C)", Tier.OPT_IN: "## Opt-In (O)"}
    for tier, heading in headers.items():
        anchor = re.escape(heading) + r"\s*\n\s*\n"
        claims.append(Claim("requirements/index.md", anchor + r"\*\*(\d+) requirements\*\*", c[f"tier_{tier.value}"], f"{heading} header"))
        for priority in ("P0", "P1", "P2", "P3"):
            claims.append(Claim("requirements/index.md", anchor + rf"\*\*\d+ requirements\*\*.*?{priority}: (\d+)", c[f"tier_{tier.value}_{priority}"], f"{heading} {priority}"))
    return claims


def check_counts() -> list[Problem]:
    problems: list[Problem] = []
    for claim in count_claims():
        text = (ROOT / claim.path).read_text(encoding="utf-8")
        matches = re.findall(claim.pattern, text)
        if not matches:
            problems.append(Problem("counts", "NOT FOUND", claim.path, f"{claim.label}: pattern {claim.pattern!r} not found"))
            continue
        for found in matches:
            if int(found) != claim.actual:
                problems.append(Problem("counts", "STALE", claim.path, f"{claim.label} says {found}, corpus has {claim.actual}"))
    return problems


# ---------------------------------------------------------------------------
# snippets
# ---------------------------------------------------------------------------


def _extract_envelope_block(text: str) -> str:
    match = re.search(r"^def extract_envelope.*?^    return None[^\n]*$", text, re.M | re.S)
    return match.group(0) if match else ""


def check_snippets() -> list[Problem]:
    canonical_path = ROOT / "challenges/triage.md"
    canonical = _extract_envelope_block(canonical_path.read_text(encoding="utf-8"))
    if not canonical:
        return [Problem("snippets", "MISSING", _rel(canonical_path), "canonical extract_envelope block not found")]
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    problems: list[Problem] = []
    for directory in ("challenges", "requirements", "schemas", "guides"):
        for path in sorted((ROOT / directory).rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if "def extract_envelope" not in text or path == canonical_path:
                continue
            block = _extract_envelope_block(text)
            if hashlib.sha256(block.encode()).hexdigest() != digest:
                problems.append(Problem("snippets", "DRIFT", _rel(path), "extract_envelope differs from challenges/triage.md"))
    return problems


# ---------------------------------------------------------------------------
# levels
# ---------------------------------------------------------------------------

_LEVEL_ONE_BLOCK = re.compile(r"<!-- level-1 -->(.*?)<!-- /level-1 -->", re.S)
_INDEX_ROW = re.compile(r"^\| \[(REQ-[FCO]-\d{3})\]\([^)]+\) \| (P[0-3]) \|.*\| (\d) \|\s*$", re.M)


def level_one_ids() -> frozenset[str]:
    match = _LEVEL_ONE_BLOCK.search((ROOT / "requirements/levels.md").read_text(encoding="utf-8"))
    if match is None:
        raise SystemExit("requirements/levels.md has no <!-- level-1 --> block")
    return frozenset(re.findall(r"\[(REQ-[FCO]-\d{3})\]", match.group(1)))


def requirement_levels() -> dict[str, int]:
    """Lowest conformance level containing each requirement, computed from levels.md and priorities."""
    level_one = level_one_ids()
    levels: dict[str, int] = {}
    for req in requirement_files():
        match = _PRIORITY.search(req.text)
        if match is None:
            raise SystemExit(f"{_rel(req.path)} has no **Priority:** on its Tier line")
        rid = str(req.id)
        levels[rid] = 1 if rid in level_one else (2 if match.group(1) == "P0" else 3)
    return levels


def check_levels() -> list[Problem]:
    problems: list[Problem] = []
    levels = requirement_levels()
    for rid in sorted(level_one_ids()):
        if rid not in levels:
            problems.append(Problem("levels", "MISSING FILE", "requirements/levels.md", f"Level 1 lists {rid}, which has no file"))
    index_text = (ROOT / "requirements/index.md").read_text(encoding="utf-8")
    listed = {rid: int(level) for rid, _priority, level in _INDEX_ROW.findall(index_text)}
    for rid, level in sorted(levels.items()):
        if rid not in listed:
            problems.append(Problem("levels", "NO LEVEL", "requirements/index.md", f"{rid} row has no Level column"))
        elif listed[rid] != level:
            problems.append(Problem("levels", "STALE", "requirements/index.md", f"{rid} Level is {listed[rid]}, computed level is {level}"))
    return problems


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

CHECKS: dict[str, Callable[[], list[Problem]]] = {
    "links": check_links,
    "symmetry": check_symmetry,
    "indexes": check_indexes,
    "sections": check_sections,
    "counts": check_counts,
    "snippets": check_snippets,
    "levels": check_levels,
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="emit a JSON report on stdout")
    parser.add_argument("--only", nargs="+", choices=sorted(CHECKS), help="run only these checks")
    args = parser.parse_args(argv)

    selected = args.only or list(CHECKS)
    results = {name: CHECKS[name]() for name in selected}
    total = sum(len(problems) for problems in results.values())

    if args.json:
        report = {
            "ok": total == 0,
            "errors": total,
            "checks": {name: [problem.__dict__ for problem in problems] for name, problems in results.items()},
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for name, problems in results.items():
            print(f"=== {name}: {len(problems)} error(s)")
            for problem in problems:
                print(f"  {problem.render()}")
        print(f"--- total: {total} error(s)")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
