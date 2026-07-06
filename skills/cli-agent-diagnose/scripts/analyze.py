# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Analyze filtered trace segments for CLI agent failure modes.

Reads the compact JSONL produced by filter.py, groups events by run, and
passes each run through diagnose.py. Emits a per-run issue summary to stdout.

Typical pipeline:
    uv run scripts/filter.py tool-execution.jsonl --cli gws --stats \\
      | uv run scripts/analyze.py

Or from a saved file:
    uv run scripts/filter.py tool-execution.jsonl --cli gws > filtered.jsonl
    uv run scripts/analyze.py filtered.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_PYTHON = (3, 10)

_SCRIPTS_DIR = Path(__file__).parent
_DIAGNOSE = _SCRIPTS_DIR / "diagnose.py"


def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"analyze.py requires Python {required}+; current Python is {current}. Run it with `uv run` or a Python {required}+ interpreter.",
            file=sys.stderr,
        )
        sys.exit(2)


def _run_diagnose(events: list[dict]) -> dict | None:
    """Run diagnose.py --history on a list of trace events. Returns parsed result or None."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for ev in events:
            # diagnose.py --history expects Claude Code PostToolUse-like records or compact traces
            f.write(json.dumps({
                "command": ev["command"],
                "stdout": ev["stdout"],
                "stderr": ev["stderr"],
                "exit_code": ev["exit_code"],
            }) + "\n")
        path = f.name

    result = subprocess.run(
        ["uv", "run", str(_DIAGNOSE), "--history", path],
        capture_output=True,
        text=True,
    )
    Path(path).unlink(missing_ok=True)

    stdout = result.stdout.strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def _segment_summary(run: int, session: str, events: list[dict]) -> dict:
    outcomes = {}
    for ev in events:
        outcomes[ev.get("outcome", "unknown")] = outcomes.get(ev.get("outcome", "unknown"), 0) + 1

    shapes = {}
    for ev in events:
        shapes[ev.get("shape", "simple")] = shapes.get(ev.get("shape", "simple"), 0) + 1

    total_stdout = sum(ev.get("stdout_bytes", 0) for ev in events)
    stderr_count = sum(1 for ev in events if ev.get("has_stderr"))
    start_ts = events[0].get("ts", "") if events else ""
    end_ts = events[-1].get("ts", "") if events else ""

    return {
        "session": session,
        "run": run,
        "call_count": len(events),
        "start_ts": start_ts,
        "end_ts": end_ts,
        "outcomes": outcomes,
        "shapes": shapes,
        "stderr_count": stderr_count,
        "total_stdout_bytes": total_stdout,
    }


def _iter_runs(src) -> dict[tuple[str, int], list[dict]]:
    """Group events by (session, run). Returns ordered dict preserving first-seen order."""
    groups: dict[tuple[str, int], list[dict]] = {}
    for raw in src:
        raw = raw.strip()
        if not raw:
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        key = (ev.get("session", ""), ev.get("run", 0))
        if key not in groups:
            groups[key] = []
        groups[key].append(ev)
    return groups


def main() -> None:
    require_supported_python()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", default="-", help="Filtered JSONL file or '-' for stdin (default)")
    parser.add_argument("--min-calls", type=int, default=1, metavar="N", help="Skip runs with fewer than N calls")
    parser.add_argument("--no-diagnose", action="store_true", help="Skip diagnose.py; emit segment stats only")
    args = parser.parse_args()

    src = sys.stdin if args.input == "-" else open(args.input)

    try:
        runs = _iter_runs(src)
    finally:
        if src is not sys.stdin:
            src.close()

    total_runs = len(runs)
    total_matches = 0

    print(f"# {total_runs} run segment(s)\n", file=sys.stderr)

    for (session, run), events in runs.items():
        if len(events) < args.min_calls:
            continue

        summary = _segment_summary(run, session, events)

        print(f"## Run {run}  [{session}]  {summary['start_ts']} → {summary['end_ts']}")
        print(f"   calls={summary['call_count']}  stderr={summary['stderr_count']}  "
              f"stdout={summary['total_stdout_bytes']}B")
        print(f"   outcomes={summary['outcomes']}  shapes={summary['shapes']}")

        if not args.no_diagnose:
            result = _run_diagnose(events)
            if result and not result.get("no_match") and not result.get("trace_insufficient"):
                matches = result.get("matches", [])
                total_matches += len(matches)
                for m in matches:
                    sev = m.get("severity", "?")
                    conf = m.get("confidence", 0)
                    print(f"   ⚠  §{m['failure_mode_id']} {m['title']}  [{sev}]  confidence={conf:.2f}")
                    print(f"      {m.get('evidence', '')}")
            elif result and result.get("no_match"):
                print("   ✓  no failure modes matched")
            elif result and result.get("trace_insufficient"):
                hints = result.get("suggested_context", [])
                print(f"   ?  trace insufficient — {'; '.join(hints)}")
            else:
                print("   –  diagnose returned no output")

        print()

    if not args.no_diagnose:
        print(f"# Total: {total_matches} failure mode match(es) across {total_runs} run(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
