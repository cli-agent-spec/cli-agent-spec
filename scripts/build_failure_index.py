"""Generate challenges/index.json: the failure mode taxonomy as one machine-readable file.

Every field is parsed from the markdown corpus, so the JSON never becomes a second
source of truth. CI runs --check, which fails when the committed file is stale or
does not validate against schemas/failure-mode-index.json.

Usage:
  uv run scripts/build_failure_index.py           write challenges/index.json
  uv run scripts/build_failure_index.py --check   exit 1 if the committed file is stale or invalid
  uv run scripts/build_failure_index.py --stdout  print the index without writing

Exit codes: 0 success, 1 stale or invalid index, 2 usage error, 3 corpus cannot be parsed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator
from spec_corpus import ROOT, CorpusError, FailureModeFile, failure_mode_files, section_body

INDEX_PATH = ROOT / "challenges" / "index.json"
SCHEMA_PATH = ROOT / "schemas" / "failure-mode-index.json"
SCHEMA_VERSION = "1.0"

_TITLE = re.compile(r"^## (\d+)\.\s+(.+?)\s*$", re.M)
_METADATA = re.compile(r"^\*\*Severity:\*\*.*$", re.M)
_FIELD = re.compile(r"\*\*([A-Za-z ]+):\*\*\s*([^|]+?)\s*(?:\||$)")
_MERGED_INTO = re.compile(r"consolidated into \*\*§(\d+)\*\*")
_MERGED_TITLE = re.compile(r"^# \d+\.\s+(.+?)\s*$", re.M)
_REQ_ROW = re.compile(r"^\| \[(REQ-[FCO]-\d{3})\]\([^)]+\) \| (P[0-3]) \|[^|]*\|(.*)\|\s*$", re.M)
_FM_REF = re.compile(r"§(\d+)")
_TRIAGE_ROW = re.compile(r"^\| (\d+) \|(.*)$", re.M)
_TIER = re.compile(r"^\*\*Tier:\*\*\s*([ABC])\b", re.M)

METADATA_KEYS = {
    "Severity": "severity",
    "Frequency": "frequency",
    "Detectability": "detectability",
    "Token Spend": "token_spend",
    "Time": "time",
    "Context": "context",
}


@dataclass(frozen=True)
class CorpusLinks:
    requirements: dict[int, list[str]]
    triage_rows: dict[int, list[int]]


def _line_value(text: str, marker: str, path: Path) -> str:
    match = re.search(rf"^\*\*{re.escape(marker)}:\*\*\s*(.+?)\s*$", text, re.M)
    if match is None:
        raise CorpusError(f"{path}: no **{marker}:** line in Agent Workaround")
    return match.group(1)


def _metadata(text: str, path: Path) -> dict[str, str]:
    line = _METADATA.search(text)
    if line is None:
        raise CorpusError(f"{path}: no **Severity:** metadata line")
    found = {key: value for key, value in _FIELD.findall(line.group(0))}
    missing = sorted(set(METADATA_KEYS) - set(found))
    if missing:
        raise CorpusError(f"{path}: metadata line lacks {', '.join(missing)}")
    values = {METADATA_KEYS[key]: found[key].strip() for key in METADATA_KEYS}
    values["severity"] = values["severity"].lower()
    return values


def corpus_links() -> CorpusLinks:
    requirements: dict[int, list[str]] = {}
    index_text = (ROOT / "requirements" / "index.md").read_text(encoding="utf-8")
    for req_id, _priority, modes in _REQ_ROW.findall(index_text):
        for number in _FM_REF.findall(modes):
            requirements.setdefault(int(number), []).append(req_id)
    triage_rows: dict[int, list[int]] = {}
    triage_text = section_body((ROOT / "challenges" / "triage.md").read_text(encoding="utf-8"), "## Decision table")
    for row, rest in _TRIAGE_ROW.findall(triage_text):
        cells = rest.split("|")
        if len(cells) < 3:
            continue
        for number in _FM_REF.findall(cells[1]):
            triage_rows.setdefault(int(number), []).append(int(row))
    return CorpusLinks(
        requirements={k: sorted(set(v)) for k, v in requirements.items()},
        triage_rows={k: sorted(set(v)) for k, v in triage_rows.items()},
    )


def active_entry(fm: FailureModeFile, links: CorpusLinks) -> dict[str, object]:
    text = fm.text
    title = _TITLE.search(text)
    if title is None or int(title.group(1)) != fm.id.number:
        raise CorpusError(f"{fm.path}: heading '## {fm.id.number}. <title>' not found")
    workaround = section_body(text, "### Agent Workaround").strip()
    problem = section_body(text, "### The Problem").strip()
    if not workaround or not problem:
        raise CorpusError(f"{fm.path}: empty The Problem or Agent Workaround section")
    tier_match = _TIER.search(workaround)
    if tier_match is None:
        raise CorpusError(f"{fm.path}: no **Tier:** letter in Agent Workaround")
    tier = tier_match.group(1)
    entry: dict[str, object] = {
        "id": fm.id.number,
        "title": title.group(2),
        "path": str(fm.path.relative_to(ROOT)),
        "part": fm.part_dir,
        "status": "active",
        **_metadata(text, fm.path),
        "signature": _line_value(workaround, "Signature", fm.path),
        "tier": tier,
        "limitation": _line_value(workaround, "Limitation", fm.path),
        "requirements": links.requirements.get(fm.id.number, []),
        "triage_rows": links.triage_rows.get(fm.id.number, []),
        "problem": problem,
        "workaround": workaround,
    }
    if tier == "C":
        entry["fallback"] = _line_value(workaround, "Fallback", fm.path)
    return entry


def merged_entry(fm: FailureModeFile) -> dict[str, object]:
    text = fm.text
    target = _MERGED_INTO.search(text)
    title = _MERGED_TITLE.search(text)
    if target is None or title is None:
        raise CorpusError(f"{fm.path}: merged stub must name its title and 'consolidated into **§N**'")
    return {
        "id": fm.id.number,
        "title": title.group(1),
        "path": str(fm.path.relative_to(ROOT)),
        "part": fm.part_dir,
        "status": "merged",
        "merged_into": int(target.group(1)),
    }


def build_index() -> dict[str, object]:
    links = corpus_links()
    entries = [merged_entry(fm) if fm.merged else active_entry(fm, links) for fm in failure_mode_files()]
    active_ids = {e["id"] for e in entries if e["status"] == "active"}
    for entry in entries:
        if entry["status"] == "merged" and entry["merged_into"] not in active_ids:
            raise CorpusError(f"§{entry['id']} is merged into §{entry['merged_into']}, which is not an active failure mode")
    return {
        "schema_version": SCHEMA_VERSION,
        "active_count": len(active_ids),
        "failure_modes": entries,
    }


def render(index: dict[str, object]) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def schema_problems(index: dict[str, object]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in Draft7Validator(schema).iter_errors(index)]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail if challenges/index.json is stale or invalid")
    mode.add_argument("--stdout", action="store_true", help="print the index instead of writing it")
    args = parser.parse_args(argv)

    try:
        index = build_index()
    except CorpusError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    problems = schema_problems(index)
    if problems:
        print("error: generated index does not match schemas/failure-mode-index.json", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    rendered = render(index)

    if args.stdout:
        sys.stdout.write(rendered)
        return 0
    if args.check:
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        if current != rendered:
            print("challenges/index.json is stale: run uv run scripts/build_failure_index.py", file=sys.stderr)
            return 1
        print(f"challenges/index.json is current ({index['active_count']} active failure modes)")
        return 0
    INDEX_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {INDEX_PATH.relative_to(ROOT)} ({index['active_count']} active failure modes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
