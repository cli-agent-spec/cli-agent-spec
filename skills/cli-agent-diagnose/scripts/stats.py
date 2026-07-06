# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Summarize Claude Code tool usage from a tool-execution JSONL log.

Reads the raw hook log (Pre + Post + Failure events) and emits a per-tool
table with success/fail counts and stdout sizes.

Usage:
    uv run scripts/stats.py <tool-execution.jsonl>
    uv run scripts/stats.py tmp/tool-execution.jsonl
    uv run scripts/stats.py tmp/tool-execution.jsonl --session <prefix>
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

MIN_PYTHON = (3, 10)


def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"stats.py requires Python {required}+; current Python is {current}. Run it with `uv run` or a Python {required}+ interpreter.",
            file=sys.stderr,
        )
        sys.exit(2)


@dataclass
class ToolStats:
    success: int = 0
    fail: int = 0
    pre: int = 0
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    interrupted: int = 0


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f}KB"
    return f"{n / 1024 ** 2:.1f}MB"


def _bar(ratio: float, width: int = 12) -> str:
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    require_supported_python()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="JSONL log file path")
    parser.add_argument("--session", metavar="PREFIX", help="Filter to session IDs starting with this prefix")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON instead of table")
    args = parser.parse_args()

    by_tool: dict[str, ToolStats] = defaultdict(ToolStats)
    sessions: set[str] = set()
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    total_lines = 0
    skipped = 0

    with open(args.input) as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue

            total_lines += 1
            sid = ev.get("session_id", "")

            if args.session and not sid.startswith(args.session):
                skipped += 1
                continue

            sessions.add(sid)
            hook = ev.get("hook_event_name", "")
            tool = ev.get("tool_name", "Unknown")
            ts = _parse_ts(ev.get("ts", ""))
            resp = ev.get("tool_response") or {}

            if ts:
                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts

            stats = by_tool[tool]

            if hook == "PreToolUse":
                stats.pre += 1
            elif hook == "PostToolUse":
                stats.success += 1
                if isinstance(resp, dict):
                    stats.stdout_bytes += len((resp.get("stdout") or "").encode())
                    stats.stderr_bytes += len((resp.get("stderr") or "").encode())
                    if resp.get("interrupted"):
                        stats.interrupted += 1
            elif hook == "PostToolUseFailure":
                stats.fail += 1
                if isinstance(resp, dict):
                    stats.stdout_bytes += len((resp.get("stdout") or "").encode())
                    stats.stderr_bytes += len((resp.get("stderr") or "").encode())

    if args.as_json:
        out = {
            "sessions": sorted(sessions),
            "first_ts": first_ts.isoformat() if first_ts else None,
            "last_ts": last_ts.isoformat() if last_ts else None,
            "tools": {
                tool: {
                    "success": s.success,
                    "fail": s.fail,
                    "interrupted": s.interrupted,
                    "stdout_bytes": s.stdout_bytes,
                    "stderr_bytes": s.stderr_bytes,
                }
                for tool, s in sorted(by_tool.items(), key=lambda x: -(x[1].success + x[1].fail))
            },
        }
        print(json.dumps(out, indent=2))
        return

    # ── Header ───────────────────────────────────────────────────────────────
    duration = ""
    if first_ts and last_ts:
        secs = int((last_ts - first_ts).total_seconds())
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        duration = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

    print(f"\n{'Tool Execution Summary':}")
    print(f"  Log:      {args.input}  ({total_lines} lines)")
    print(f"  Sessions: {len(sessions)}  {' '.join(sid[:8] for sid in sorted(sessions))}")
    if duration:
        print(f"  Span:     {first_ts.strftime('%H:%M:%S') if first_ts else '?'} → "  # type: ignore[union-attr]
              f"{last_ts.strftime('%H:%M:%S') if last_ts else '?'}  ({duration})")  # type: ignore[union-attr]
    if skipped:
        print(f"  Filtered: {skipped} events excluded (--session)")
    print()

    # ── Table ─────────────────────────────────────────────────────────────────
    col_tool   = 18
    col_ok     = 7
    col_fail   = 6
    col_int    = 6
    col_stdout = 9
    col_stderr = 9
    col_bar    = 14

    header = (
        f"{'Tool':<{col_tool}}  {'Success':>{col_ok}}  {'Fail':>{col_fail}}  "
        f"{'Intr':>{col_int}}  {'Stdout':>{col_stdout}}  {'Stderr':>{col_stderr}}  "
        f"{'Success rate':<{col_bar}}"
    )
    sep = "─" * len(header)
    print(header)
    print(sep)

    totals = ToolStats()
    rows = sorted(by_tool.items(), key=lambda x: -(x[1].success + x[1].fail))

    for tool, s in rows:
        total_calls = s.success + s.fail
        rate = s.success / total_calls if total_calls else 0.0
        bar = _bar(rate)
        pct = f"{rate * 100:.0f}%"

        print(
            f"{tool:<{col_tool}}  "
            f"{s.success:>{col_ok}}  "
            f"{s.fail:>{col_fail}}  "
            f"{s.interrupted:>{col_int}}  "
            f"{_fmt_bytes(s.stdout_bytes):>{col_stdout}}  "
            f"{_fmt_bytes(s.stderr_bytes):>{col_stderr}}  "
            f"{bar} {pct}"
        )
        totals.success += s.success
        totals.fail += s.fail
        totals.interrupted += s.interrupted
        totals.stdout_bytes += s.stdout_bytes
        totals.stderr_bytes += s.stderr_bytes

    print(sep)
    total_calls = totals.success + totals.fail
    rate = totals.success / total_calls if total_calls else 0.0
    print(
        f"{'TOTAL':<{col_tool}}  "
        f"{totals.success:>{col_ok}}  "
        f"{totals.fail:>{col_fail}}  "
        f"{totals.interrupted:>{col_int}}  "
        f"{_fmt_bytes(totals.stdout_bytes):>{col_stdout}}  "
        f"{_fmt_bytes(totals.stderr_bytes):>{col_stderr}}  "
        f"{_bar(rate)} {rate * 100:.0f}%"
    )
    print()


if __name__ == "__main__":
    main()
