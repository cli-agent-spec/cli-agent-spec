#!/usr/bin/env python3
"""
Extract and deduplicate invocation invariants (env vars and flags) from Agent Workaround
sections across multiple §N failure modes. Used to populate the Invocation Invariants
block in report-agent-dev.md.

Usage:
    python build_invariants.py <workarounds.json>

Input JSON (produced by the skill after reading challenge files):
    [
      {
        "section": 10,
        "workaround_text": "Set TERM=dumb before invoking...\nPass --no-pager on every call..."
      },
      ...
    ]

Output — two blocks, each entry on its own line, ready to paste into the invariants block:

    ENV:
      TERM=dumb                # §10 — disables interactive terminal detection
      NO_COLOR=1               # §22,§30 — suppresses ANSI escape codes

    FLAGS:
      --no-pager               # §10 — prevents pager from blocking stdout
      --output=json            # §44 — guarantees machine-readable output

Exit codes:
    0   output produced
    1   no env vars or flags found
    2   usage / parse error
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Patterns that signal an env var recommendation in a workaround section.
# Captures NAME=VALUE or just NAME (with context showing it is an env var).
ENV_PATTERNS = [
    re.compile(r"\b([A-Z][A-Z0-9_]+=\S+)"),          # KEY=VALUE
    re.compile(r"(?:set|export)\s+([A-Z][A-Z0-9_]+=\S+)"),  # set KEY=VALUE
    re.compile(r"env(?:ironment)?\s+var(?:iable)?\s+`([A-Z][A-Z0-9_]+=[^`]+)`"),
]

# Patterns that signal a flag recommendation.
FLAG_PATTERNS = [
    re.compile(r"(`|\")(--[\w-]+(?:=\S+)?)\1"),       # `--flag` or "--flag"
    re.compile(r"(?:pass|add|use|include)\s+(--[\w-]+(?:=\S+)?)"),  # prose "pass --flag"
    re.compile(r"(?:always|every call)[^.]*?(--[\w-]+(?:=\S+)?)"),
]

# Lines that explain *why* — used to produce the comment after the entry.
WHY_PATTERN = re.compile(r"(?:—|:|-)\s*(.{10,80}?)(?:\.|$)")


def extract_env_vars(text: str) -> list[tuple[str, str]]:
    """Return list of (KEY=VALUE, why_clause) pairs."""
    found = []
    for pat in ENV_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(1) if pat.groups == 1 else m.group(pat.lastindex)
            # Find a nearby why clause on the same line
            line = text[max(0, m.start() - 60) : m.end() + 120]
            why_m = WHY_PATTERN.search(line)
            why = why_m.group(1).strip() if why_m else ""
            found.append((val.strip("`\""), why))
    return found


def extract_flags(text: str) -> list[tuple[str, str]]:
    """Return list of (--flag, why_clause) pairs."""
    found = []
    for pat in FLAG_PATTERNS:
        for m in pat.finditer(text):
            flag = m.group(2) if pat.groups >= 2 else m.group(1)
            line = text[max(0, m.start() - 60) : m.end() + 120]
            why_m = WHY_PATTERN.search(line)
            why = why_m.group(1).strip() if why_m else ""
            found.append((flag.strip(), why))
    return found


def deduplicate(
    entries: list[tuple[str, str, int]]
) -> list[tuple[str, str, list[int]]]:
    """
    entries: [(value, why, section), ...]
    Returns deduplicated [(value, why, [section, ...]), ...] preserving first-seen why.
    """
    seen: dict[str, tuple[str, list[int]]] = {}
    for value, why, section in entries:
        if value not in seen:
            seen[value] = (why, [section])
        else:
            if section not in seen[value][1]:
                seen[value][1].append(section)
    return [(v, w, sections) for v, (w, sections) in seen.items()]


def format_section_list(sections: list[int]) -> str:
    return ",".join(f"§{s}" for s in sorted(sections))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: build_invariants.py <workarounds.json>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        sys.exit(2)

    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        sys.exit(2)

    raw_env: list[tuple[str, str, int]] = []
    raw_flags: list[tuple[str, str, int]] = []

    for item in items:
        section = item["section"]
        text = item.get("workaround_text", "")
        for val, why in extract_env_vars(text):
            raw_env.append((val, why, section))
        for flag, why in extract_flags(text):
            raw_flags.append((flag, why, section))

    env_deduped = deduplicate(raw_env)
    flags_deduped = deduplicate(raw_flags)

    if not env_deduped and not flags_deduped:
        print("(no invariants found)")
        sys.exit(1)

    if env_deduped:
        print("ENV:")
        for val, why, sections in env_deduped:
            sec_str = format_section_list(sections)
            comment = f"  # {sec_str} — {why}" if why else f"  # {sec_str}"
            print(f"  {val:<24}{comment}")

    if flags_deduped:
        print("\nFLAGS:")
        for flag, why, sections in flags_deduped:
            sec_str = format_section_list(sections)
            comment = f"  # {sec_str} — {why}" if why else f"  # {sec_str}"
            print(f"  {flag:<24}{comment}")


if __name__ == "__main__":
    main()
