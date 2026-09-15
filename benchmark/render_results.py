"""Render the results table in benchmark/README.md from a harness results file.

Only files produced by harness version 2 (trials, log-based grading) are accepted, so the
table never mixes numbers graded under different rules.

Usage:
  uv run benchmark/render_results.py benchmark/results/<file>.json
  uv run benchmark/render_results.py --empty      reset the table to its not-yet-run state

Exit codes: 0 README updated, 2 usage error or incompatible results file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

README = Path(__file__).resolve().parent / "README.md"
START = "<!-- results:start -->"
END = "<!-- results:end -->"
HARNESS_VERSION = "2"

EMPTY = """No results recorded with harness version 2 yet. Run the harness, then render:

```bash
uv run benchmark/harness/run.py --all --trials 5 --output benchmark/results/$(date +%Y%m%d).json
uv run benchmark/render_results.py benchmark/results/<file>.json
```"""


def render(data: dict[str, object]) -> str:
    summary = data["summary"]
    if not isinstance(summary, list):
        raise ValueError("summary must be a list")
    lines = [
        f"Model `{data['model']}` · {data['trials']} trials per cell · {data['date']} · harness v{data['harness_version']}",
        "",
        "| Scenario | Mode | Success | Unsafe retries | Median tokens | Tokens per success | Median API calls |",
        "|----------|------|---------|----------------|---------------|--------------------|------------------|",
    ]
    for row in summary:
        per_success = row["tokens_per_success"] if row["tokens_per_success"] is not None else "no success"
        lines.append(
            f"| {row['scenario']} | cli-{row['mode']} | {row['successes']}/{row['trials']} | {row['unsafe_retries']} "
            f"| {row['median_total_tokens']} | {per_success} | {row['median_api_calls']} |"
        )
    lines += ["", "Tokens per success divides all tokens spent in a cell by its successful trials, so failed attempts count as cost."]
    return "\n".join(lines)


def replace_block(readme: str, body: str) -> str:
    start, end = readme.find(START), readme.find(END)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"{README.name} lacks the {START} / {END} markers")
    return readme[: start + len(START)] + "\n" + body + "\n" + readme[end:]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("results", nargs="?", type=Path, help="results JSON written by run.py --output")
    source.add_argument("--empty", action="store_true", help="reset the table to its not-yet-run state")
    args = parser.parse_args(argv)

    if args.empty:
        body = EMPTY
    else:
        data = json.loads(args.results.read_text(encoding="utf-8"))
        version = data.get("harness_version") if isinstance(data, dict) else "1 (bare run list)"
        if version != HARNESS_VERSION:
            print(f"error: {args.results} is harness version {version!r}; only version {HARNESS_VERSION} results are rendered", file=sys.stderr)
            return 2
        body = render(data)
    README.write_text(replace_block(README.read_text(encoding="utf-8"), body), encoding="utf-8")
    print(f"updated {README}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
