"""Shared loaders for the CLI Agent Spec corpus.

Every validation script reads the repository through this module so that the
definition of "a failure mode file", "a requirement file", or "a schema pair"
exists in exactly one place.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHALLENGES_DIR = "challenges"
REQUIREMENTS_DIR = "requirements"
SCHEMAS_DIR = "schemas"
GUIDES_DIR = "guides"

MERGED_MARKER = "MERGED"


class CorpusError(Exception):
    """The repository layout does not match what the spec tooling expects."""


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class FailureModeId:
    number: int

    def __post_init__(self) -> None:
        if self.number < 1:
            raise CorpusError(f"failure mode number must be positive, got {self.number}")

    def __str__(self) -> str:
        return f"§{self.number}"


class Tier(StrEnum):
    FRAMEWORK = "f"
    COMMAND = "c"
    OPT_IN = "o"

    @property
    def letter(self) -> str:
        return self.value.upper()


@dataclass(frozen=True, order=True)
class RequirementId:
    tier: Tier
    number: int

    _PATTERN = re.compile(r"^REQ-([FCO])-(\d{3})$")

    @classmethod
    def parse(cls, text: str) -> RequirementId:
        match = cls._PATTERN.match(text)
        if match is None:
            raise CorpusError(f"malformed requirement id: {text!r}")
        return cls(Tier(match.group(1).lower()), int(match.group(2)))

    def __str__(self) -> str:
        return f"REQ-{self.tier.letter}-{self.number:03d}"


# ---------------------------------------------------------------------------
# Corpus files
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FailureModeFile:
    id: FailureModeId
    path: Path
    part_dir: str
    merged: bool

    @property
    def text(self) -> str:
        return self.path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class RequirementFile:
    id: RequirementId
    path: Path

    @property
    def text(self) -> str:
        return self.path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class SchemaPair:
    name: str
    json_path: Path
    md_path: Path

    def load(self) -> dict[str, object]:
        loaded = json.loads(self.json_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise CorpusError(f"{self.json_path} does not contain a JSON object")
        return loaded


_FAILURE_MODE_FILE = re.compile(r"^(\d{2})-(critical|high|medium)-[a-z0-9-]+\.md$")
_REQUIREMENT_FILE = re.compile(r"^([fco])-(\d{3})-[a-z0-9-]+\.md$")


def failure_mode_files(root: Path = ROOT) -> tuple[FailureModeFile, ...]:
    """Every numbered failure mode file, including merged stubs, sorted by §N."""
    found: list[FailureModeFile] = []
    for part in sorted((root / CHALLENGES_DIR).iterdir()):
        if not part.is_dir():
            continue
        for path in sorted(part.glob("*.md")):
            if path.name == "index.md":
                continue
            match = _FAILURE_MODE_FILE.match(path.name)
            if match is None:
                raise CorpusError(f"unexpected file name in {part.name}: {path.name}")
            text = path.read_text(encoding="utf-8")
            found.append(
                FailureModeFile(
                    id=FailureModeId(int(match.group(1))),
                    path=path,
                    part_dir=part.name,
                    merged=MERGED_MARKER in text,
                )
            )
    numbers = [f.id for f in found]
    if len(numbers) != len(set(numbers)):
        raise CorpusError("duplicate failure mode numbers in challenges/")
    return tuple(sorted(found, key=lambda f: f.id))


def active_failure_modes(root: Path = ROOT) -> tuple[FailureModeFile, ...]:
    return tuple(f for f in failure_mode_files(root) if not f.merged)


def requirement_files(root: Path = ROOT) -> tuple[RequirementFile, ...]:
    found: list[RequirementFile] = []
    for path in sorted((root / REQUIREMENTS_DIR).glob("*.md")):
        match = _REQUIREMENT_FILE.match(path.name)
        if match is None:
            continue
        found.append(RequirementFile(RequirementId(Tier(match.group(1)), int(match.group(2))), path))
    return tuple(sorted(found, key=lambda r: r.id))


def schema_pairs(root: Path = ROOT) -> tuple[SchemaPair, ...]:
    schemas = root / SCHEMAS_DIR
    pairs: list[SchemaPair] = []
    for json_path in sorted(schemas.glob("*.json")):
        md_path = json_path.with_suffix(".md")
        if not md_path.is_file():
            raise CorpusError(f"{json_path.name} has no companion {md_path.name}")
        pairs.append(SchemaPair(json_path.stem, json_path, md_path))
    return tuple(pairs)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FencedBlock:
    path: Path
    lang: str
    body: str
    line: int              # 1-based line of the opening fence
    section: str           # nearest preceding "## " heading, or "" when none
    label: str             # nearest preceding non-blank prose line inside the section


_FENCE_OPEN = re.compile(r"^(```+)([\w+-]*)\s*$")
_HEADING = re.compile(r"^(#{2,6}) ")


def fenced_blocks(path: Path) -> Iterator[FencedBlock]:
    """Yield fenced code blocks with the heading and label that introduce them."""
    lines = path.read_text(encoding="utf-8").splitlines()
    section = ""
    label = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        opening = _FENCE_OPEN.match(line)
        if opening is None:
            if line.startswith("## "):
                section = line[3:].strip()
                label = ""
            elif line.strip() and not _HEADING.match(line):
                label = line.strip()
            index += 1
            continue
        fence = opening.group(1)
        body: list[str] = []
        close = index + 1
        while close < len(lines) and not _closes(lines[close], fence):
            body.append(lines[close])
            close += 1
        if close == len(lines):
            raise CorpusError(f"{path}:{index + 1}: unterminated code fence")
        yield FencedBlock(path, opening.group(2), "\n".join(body), index + 1, section, label)
        index = close + 1


def _closes(line: str, fence: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= len(fence) and set(stripped) == {"`"}


def strip_fenced_code(text: str) -> str:
    """Remove fenced code blocks so prose-only scans ignore example content."""
    kept: list[str] = []
    fence = ""
    for line in text.splitlines():
        if fence:
            if _closes(line, fence):
                fence = ""
            continue
        opening = _FENCE_OPEN.match(line)
        if opening is not None:
            fence = opening.group(1)
            continue
        kept.append(line)
    return "\n".join(kept)


def section_body(text: str, heading: str) -> str:
    """Body of the first heading that matches exactly, up to the next heading of the same level."""
    level = len(heading) - len(heading.lstrip("#"))
    pattern = re.compile(rf"^{re.escape(heading)}[ \t]*$", re.M)
    match = pattern.search(text)
    if match is None:
        return ""
    stop = re.compile(rf"^#{{1,{level}}} ", re.M)
    end = stop.search(text, match.end())
    return text[match.end(): end.start() if end else len(text)]
