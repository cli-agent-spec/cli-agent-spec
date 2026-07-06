# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Filter, compact, and stream Claude Code tool-execution JSONL for CLI agent diagnosis.

Reads PostToolUse Bash events, strips internal noise, groups by session and run
(time-gap clustering), and emits compact trace records to stdout.

Usage:
    uv run scripts/filter.py <tool-execution.jsonl> [options]
    cat tool-execution.jsonl | uv run scripts/filter.py - [options]

Output: JSONL — one record per CLI invocation, tagged with session and run.

Pipe to diagnose.py:
    uv run scripts/filter.py tool-execution.jsonl --cli gws > filtered.jsonl
    uv run scripts/diagnose.py --history filtered.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

MIN_PYTHON = (3, 10)


def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"filter.py requires Python {required}+; current Python is {current}. Run it with `uv run` or a Python {required}+ interpreter.",
            file=sys.stderr,
        )
        sys.exit(2)


# ── Noise classification ──────────────────────────────────────────────────────

# Shell utilities and internal tooling that are never CLI agent invocations
_NOISE_BINS: frozenset[str] = frozenset({
    # Shell builtins / POSIX utilities
    "ls", "find", "grep", "cat", "head", "tail", "wc", "echo", "printf",
    "awk", "sed", "cut", "sort", "uniq", "xargs", "tee", "tr",
    # File ops
    "mkdir", "rm", "cp", "mv", "ln", "chmod", "chown", "touch", "stat", "file",
    # Info commands
    "which", "type", "command", "env", "whoami", "uname", "date", "pwd", "id",
    # VCS
    "git", "svn", "hg",
    # Package managers
    "brew", "npm", "pip", "pip3", "cargo", "apt", "apt-get", "yum", "dnf",
    # Scripting runtimes used internally
    "python", "python3", "perl", "ruby", "node",
    # GUI / macOS
    "open",
    # Shells
    "bash", "zsh", "sh", "fish",
})

# Prefixes that identify our own skill/script invocations
_NOISE_PREFIXES: tuple[str, ...] = (
    "uv run skills/",
    "uv run scripts/",
    "uv run --with",
    "npm install",
    "ajv ",
)


def _first_bin(command: str) -> str:
    """Return the binary name from the first token of a command."""
    token = command.strip().split()[0] if command.strip() else ""
    # Handle env/timeout wrappers: `perl -e 'alarm(N); exec @ARGV' -- REAL_CMD`
    if token in ("perl",) and "exec @ARGV" in command:
        # Extract the real command after '--'
        parts = command.split("--", 1)
        if len(parts) > 1:
            real = parts[1].strip().split()[0]
            return Path(real).name
    return Path(token).name


def _is_noise(command: str, cli_filter: str | None) -> bool:
    if cli_filter:
        # Keep only commands that invoke the specified CLI anywhere
        first = _first_bin(command)
        return first != cli_filter
    # General noise filter
    cmd = command.strip()
    for prefix in _NOISE_PREFIXES:
        if cmd.startswith(prefix):
            return True
    return _first_bin(cmd) in _NOISE_BINS


# ── JSONL streaming ───────────────────────────────────────────────────────────

def _iter_events(src: Iterator[str]) -> Iterator[dict]:
    for raw in src:
        raw = raw.strip()
        if not raw:
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue


def _parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return None


# ── Run clustering ────────────────────────────────────────────────────────────

def _run_key(
    event: dict,
    prev_session: str | None,
    prev_ts: datetime | None,
    prev_run: int,
    gap_seconds: int,
) -> int:
    session = event.get("session_id", "")
    ts = _parse_ts(event.get("ts", ""))

    if session != prev_session:
        return 1  # new session always resets run counter

    if prev_ts is None or ts is None:
        return prev_run

    gap = (ts - prev_ts).total_seconds()
    return prev_run + 1 if gap > gap_seconds else prev_run


# ── Classification ────────────────────────────────────────────────────────────

_FAIL_PATTERNS = re.compile(
    r"error|failed|failure|exception|traceback|not found|permission denied|"
    r"command not found|no such file|unauthorized|403|404|500|invalid_rapt|"
    r"auth(?:entication)? (?:failed|required|expired)|token expired",
    re.IGNORECASE,
)

# JSON stdout with {"ok": false} or {"error": ...} or HTTP 4xx/5xx codes
_JSON_FAIL = re.compile(r'"ok"\s*:\s*false|"error"\s*:\s*\{|"status"\s*:\s*(?:4|5)\d{2}', re.IGNORECASE)

_SHELL_OPERATORS = re.compile(r"[|;&]")


def _classify_outcome(stdout: str, stderr: str, interrupted: bool) -> str:
    if interrupted:
        return "interrupted"
    # stderr signals
    if stderr.strip() and _FAIL_PATTERNS.search(stderr):
        return "fail"
    if not stdout.strip() and stderr.strip():
        return "fail"
    # stdout signals — gws errors arrive as JSON in stdout
    if stdout.strip():
        if _JSON_FAIL.search(stdout):
            return "fail"
        if _FAIL_PATTERNS.search(stdout[:500]):  # check only prefix to avoid false positives in large output
            return "fail"
    return "success"


def _classify_shape(command: str) -> str:
    """Return 'piped' if the command uses pipes, 'combined' if it chains with && / || / ;, else 'simple'."""
    # Strip quoted strings to avoid false positives on operators inside quotes
    stripped = re.sub(r"'[^']*'|\"[^\"]*\"", "", command)
    if "|" in stripped:
        return "piped"
    if re.search(r"&&|\|\|", stripped):
        return "combined"
    if ";" in stripped:
        return "combined"
    return "simple"


# ── Compaction ────────────────────────────────────────────────────────────────

def _compact(event: dict) -> dict | None:
    tool_input = event.get("tool_input", {})
    tool_response = event.get("tool_response", {})

    command = tool_input.get("command", "")
    if not command:
        return None

    stdout = tool_response.get("stdout", "")
    stderr = tool_response.get("stderr", "")
    interrupted = bool(tool_response.get("interrupted", False))
    is_failure_event = event.get("hook_event_name") == "PostToolUseFailure"
    exit_code = 1 if is_failure_event else (130 if interrupted else 0)

    return {
        "session": event.get("session_id", "")[:8],  # short prefix for readability
        "ts": event.get("ts", ""),
        "tool": event.get("tool_name", "Bash"),
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        # classification
        "outcome": "fail" if is_failure_event else _classify_outcome(stdout, stderr, interrupted),
        "has_stderr": bool(stderr.strip()),
        "stdout_lines": stdout.count("\n") + 1 if stdout.strip() else 0,
        "stdout_bytes": len(stdout.encode()),
        "shape": _classify_shape(command),
    }


# ── Human-readable display ────────────────────────────────────────────────────

_OUTCOME_ICON = {"success": "✓", "fail": "✗", "retry": "↺", "interrupted": "⏱"}


def _print_human(record: dict, tail: int) -> None:
    icon = _OUTCOME_ICON.get(record["outcome"], "?")
    cmd_first_line = record["command"].split("\n")[0]
    print(f"\n{icon} run={record['run']} [{record['session']}] {record['ts']}  {record['shape']}")
    # print full command (all lines, indented)
    for line in record["command"].splitlines():
        print(f"  {line}")
    # stdout tail
    stdout = record.get("stdout", "")
    if stdout.strip():
        lines = stdout.splitlines()
        shown = lines[-tail:]
        skipped = len(lines) - len(shown)
        if skipped > 0:
            print(f"  stdout ({skipped} lines skipped):")
        else:
            print(f"  stdout:")
        for line in shown:
            print(f"    {line}")
    else:
        print(f"  stdout: (empty)")
    # stderr if present
    stderr = record.get("stderr", "")
    if stderr.strip():
        for line in stderr.splitlines()[-3:]:
            print(f"  stderr: {line}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    require_supported_python()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="JSONL file path or '-' for stdin")
    parser.add_argument("--cli", metavar="NAME", help="Keep only invocations of this CLI binary (e.g. gws)")
    parser.add_argument("--gap", type=int, default=60, metavar="SECONDS", help="Time gap that starts a new run (default: 60)")
    parser.add_argument("--outcome", metavar="OUTCOME", help="Keep only events with this outcome: fail, success, retry, interrupted")
    parser.add_argument("--show", action="store_true", help="Human-readable output: command + tailed stdout instead of JSONL")
    parser.add_argument("--tail", type=int, default=5, metavar="N", help="Lines of stdout to show with --show (default: 5)")
    parser.add_argument("--stats", action="store_true", help="Print summary stats to stderr when done")
    args = parser.parse_args()

    src = sys.stdin if args.input == "-" else open(args.input)

    kept = dropped = 0
    prev_session: str | None = None
    prev_ts: datetime | None = None
    prev_command: str | None = None
    run = 0

    try:
        for event in _iter_events(src):
            hook = event.get("hook_event_name", "")
            if hook not in ("PostToolUse", "PostToolUseFailure"):
                dropped += 1
                continue
            if event.get("tool_name") != "Bash":
                dropped += 1
                continue

            command = (event.get("tool_input") or {}).get("command", "")
            if _is_noise(command, args.cli):
                dropped += 1
                continue

            record = _compact(event)
            if record is None:
                dropped += 1
                continue

            session = event.get("session_id", "")
            ts = _parse_ts(event.get("ts", ""))
            run = _run_key(event, prev_session, prev_ts, run, args.gap)

            # Retry: same first token + same leading args as previous call in same run
            is_retry = (
                prev_session == session
                and prev_command is not None
                and command.split()[:3] == prev_command.split()[:3]
                and command != prev_command
            )
            record["outcome"] = "retry" if is_retry else record["outcome"]

            prev_session = session
            prev_ts = ts
            prev_command = command

            record["run"] = run

            if args.outcome and record["outcome"] != args.outcome:
                dropped += 1
                continue

            if args.show:
                _print_human(record, args.tail)
            else:
                print(json.dumps(record, ensure_ascii=False))
            kept += 1

    finally:
        if src is not sys.stdin:
            src.close()

    if args.stats:
        print(f"kept={kept} dropped={dropped} total={kept + dropped}", file=sys.stderr)


if __name__ == "__main__":
    main()
