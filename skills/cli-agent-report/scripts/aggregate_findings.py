#!/usr/bin/env python3
"""
Parse evaluations/<cli>/findings.md and emit structured JSON for report generation.

Usage:
    python aggregate_findings.py <findings.md> [--scope <filter>]

Scope filter syntax (same as cli-agent-evaluate-batch):
    critical | high | medium | all
    "part 1" … "part 7"
    §1 §2 §10   (explicit list)

Output JSON structure:
    {
      "rows": [
        {"section": 1, "title": "...", "severity": "Critical", "score": 2, "notes": "...", "indeterminate": false},
        ...
      ],
      "summary": {
        "Critical": {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0},
        "High":     {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0},
        "Medium":   {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0},
        "all":      {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0}
      },
      "average_score": 1.5,
      "sorted": {
        "severity_desc_score_asc": [1, 10, 2, ...],
        "score_asc_severity_desc": [10, 1, 2, ...],
        "critical_then_high_then_medium_section_asc": [1, 10, 2, ...]
      },
      "lists": {
        "passing": [{"section": 1, "title": "..."}],
        "failing": [{"section": 10, "title": "...", "severity": "Critical", "score": 0}],
        "partial": [{"section": 2,  "title": "...", "severity": "High",     "score": 1}],
        "indeterminate": [{"section": 5, "title": "..."}]
      }
    }
"""

import json
import re
import sys
from pathlib import Path

SEVERITY_ORDER = ["Critical", "High", "Medium"]
SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER)}

# Matches a pipe-delimited findings row: | §N | Title | Severity | Score | Notes |
# Score field may be 0, 1, 2, 3, or ? (indeterminate)
ROW_PATTERN = re.compile(
    r"^\|\s*§(\d+)\s*\|\s*([^|]+?)\s*\|\s*(Critical|High|Medium)\s*\|\s*([0-3?])/3\s*\|\s*(.*?)\s*\|"
)

SCOPE_SEVERITY = {"critical", "high", "medium"}
PART_RANGES = {
    1: range(1, 11),
    2: range(11, 22),
    3: range(22, 32),
    4: range(32, 45),
    5: range(45, 55),
    6: range(55, 65),
    7: range(65, 72),
}


def parse_scope(scope: str | None) -> set[int] | None:
    """Return a set of §N integers in scope, or None meaning "all"."""
    if not scope or scope.strip().lower() == "all":
        return None

    s = scope.strip().lower()

    if s in SCOPE_SEVERITY:
        return None  # caller must filter by severity instead

    part_match = re.match(r"part\s+(\d)", s)
    if part_match:
        part = int(part_match.group(1))
        if part not in PART_RANGES:
            raise ValueError(f"Unknown part number: {part}")
        return set(PART_RANGES[part])

    sections = re.findall(r"§(\d+)", scope)
    if sections:
        return {int(n) for n in sections}

    raise ValueError(f"Unrecognised scope: {scope!r}")


def severity_filter(scope: str | None) -> str | None:
    if scope and scope.strip().lower() in SCOPE_SEVERITY:
        return scope.strip().capitalize()
    return None


def parse_findings(path: Path, scope: str | None) -> list[dict]:
    section_filter = parse_scope(scope)
    sev_filter = severity_filter(scope)

    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW_PATTERN.match(line)
        if not m:
            continue
        section = int(m.group(1))
        title = m.group(2).strip()
        sev = m.group(3).strip()
        raw_score = m.group(4).strip()
        notes = m.group(5).strip()

        if section_filter is not None and section not in section_filter:
            continue
        if sev_filter is not None and sev != sev_filter:
            continue

        indeterminate = raw_score == "?"
        score = None if indeterminate else int(raw_score)

        rows.append(
            {
                "section": section,
                "title": title,
                "severity": sev,
                "score": score,
                "notes": notes,
                "indeterminate": indeterminate,
            }
        )
    return rows


def bucket(score: int | None, indeterminate: bool) -> str:
    if indeterminate:
        return "indeterminate"
    if score == 3:
        return "pass"
    if score == 0:
        return "fail"
    return "partial"


def build_summary(rows: list[dict]) -> dict:
    summary: dict[str, dict] = {
        sev: {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0}
        for sev in SEVERITY_ORDER
    }
    summary["all"] = {"pass": 0, "partial": 0, "fail": 0, "indeterminate": 0, "total": 0}

    for row in rows:
        b = bucket(row["score"], row["indeterminate"])
        summary[row["severity"]][b] += 1
        summary[row["severity"]]["total"] += 1
        summary["all"][b] += 1
        summary["all"]["total"] += 1

    return summary


def average_score(rows: list[dict]) -> float:
    scored = [r for r in rows if not r["indeterminate"]]
    if not scored:
        return 0.0
    return round(sum(r["score"] for r in scored) / len(scored), 1)


def sort_severity_desc_score_asc(rows: list[dict]) -> list[int]:
    def key(r: dict) -> tuple:
        sev_rank = SEVERITY_RANK.get(r["severity"], 99)
        score = r["score"] if not r["indeterminate"] else 99
        return (sev_rank, score, r["section"])

    return [r["section"] for r in sorted(rows, key=key)]


def sort_score_asc_severity_desc(rows: list[dict]) -> list[int]:
    """Issues mode: score asc, severity desc within same score; indeterminate last."""
    def key(r: dict) -> tuple:
        if r["indeterminate"]:
            return (999, 0, r["section"])
        sev_rank = SEVERITY_RANK.get(r["severity"], 99)
        return (r["score"], sev_rank, r["section"])

    return [r["section"] for r in sorted(rows, key=key)]


def sort_runtime(rows: list[dict]) -> list[int]:
    """Runtime score summary: Critical → High → Medium, within group §N ascending."""
    def key(r: dict) -> tuple:
        return (SEVERITY_RANK.get(r["severity"], 99), r["section"])

    return [r["section"] for r in sorted(rows, key=key)]


def build_lists(rows: list[dict]) -> dict:
    def slim(r: dict) -> dict:
        return {"section": r["section"], "title": r["title"], "severity": r["severity"], "score": r["score"]}

    passing = [slim(r) for r in rows if not r["indeterminate"] and r["score"] == 3]
    failing = [slim(r) for r in rows if not r["indeterminate"] and r["score"] == 0]
    partial = [slim(r) for r in rows if not r["indeterminate"] and r["score"] in (1, 2)]
    indeterminate = [{"section": r["section"], "title": r["title"]} for r in rows if r["indeterminate"]]

    return {
        "passing": passing,
        "failing": failing,
        "partial": partial,
        "indeterminate": indeterminate,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: aggregate_findings.py <findings.md> [--scope <filter>]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(1)

    scope: str | None = None
    if "--scope" in sys.argv:
        idx = sys.argv.index("--scope")
        scope = sys.argv[idx + 1]

    rows = parse_findings(path, scope)

    result = {
        "rows": rows,
        "summary": build_summary(rows),
        "average_score": average_score(rows),
        "sorted": {
            "severity_desc_score_asc": sort_severity_desc_score_asc(rows),
            "score_asc_severity_desc": sort_score_asc_severity_desc(rows),
            "runtime_severity_section": sort_runtime(rows),
        },
        "lists": build_lists(rows),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
