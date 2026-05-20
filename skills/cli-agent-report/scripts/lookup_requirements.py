#!/usr/bin/env python3
"""
Given one or more §N identifiers, find every requirement in requirements/index.md
whose "Failure mode(s)" column references that §N.

Usage:
    python lookup_requirements.py <requirements/index.md> §1 [§2 §10 ...]

Output (one block per §N):
    §1:
      - REQ-F-001 (Must) — Exit Code Contract [Tier: F = framework handles]
      - REQ-C-012 (Must) — ...

Exit codes:
    0   matches found for all requested §N
    1   no matches found for at least one §N (still prints results for others)
    2   usage error
"""

import re
import sys
from pathlib import Path

TIER_LABELS = {
    "F": "F = framework handles",
    "C": "C = you declare",
    "O": "O = you opt in",
}

# Matches: | REQ-F-001 | Must | Title | description... | §1, §10 |
ROW_PATTERN = re.compile(
    r"^\|\s*(REQ-([FCO])-(\d+))\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*([^|]*?)\s*\|"
)


def parse_requirements(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW_PATTERN.match(line)
        if not m:
            continue
        req_id = m.group(1)
        tier = m.group(2)
        priority = m.group(4).strip()
        title = m.group(5).strip()
        failure_modes_cell = m.group(6)

        sections = {int(n) for n in re.findall(r"§(\d+)", failure_modes_cell)}

        rows.append(
            {
                "id": req_id,
                "tier": tier,
                "priority": priority,
                "title": title,
                "sections": sections,
            }
        )
    return rows


def format_row(row: dict) -> str:
    tier_label = TIER_LABELS.get(row["tier"], row["tier"])
    return f"- {row['id']} ({row['priority']}) — {row['title']} [Tier: {tier_label}]"


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: lookup_requirements.py <requirements/index.md> §N [§N ...]",
            file=sys.stderr,
        )
        sys.exit(2)

    req_path = Path(sys.argv[1])
    if not req_path.exists():
        print(f"Not found: {req_path}", file=sys.stderr)
        sys.exit(2)

    requested = []
    for arg in sys.argv[2:]:
        nums = re.findall(r"(\d+)", arg)
        for n in nums:
            requested.append(int(n))

    if not requested:
        print("No §N identifiers provided.", file=sys.stderr)
        sys.exit(2)

    all_reqs = parse_requirements(req_path)
    any_missing = False

    for section in requested:
        matches = [r for r in all_reqs if section in r["sections"]]
        if not matches:
            print(f"§{section}: (no requirements reference this failure mode)")
            any_missing = True
        else:
            print(f"§{section}:")
            for row in matches:
                print(f"  {format_row(row)}")

    sys.exit(1 if any_missing else 0)


if __name__ == "__main__":
    main()
