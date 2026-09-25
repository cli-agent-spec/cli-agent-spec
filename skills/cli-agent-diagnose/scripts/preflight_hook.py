#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
FailSense PreToolUse hook for Claude Code.

Intercepts Bash tool calls before they run. If the intended command
matches a known §N failure pattern, outputs a warning and the
recommended call instead.

Install:
    Add to .claude/settings.json (project) or ~/.claude/settings.json (global):

    {
      "hooks": {
        "PreToolUse": [{
          "matcher": "Bash",
          "hooks": [{
            "type": "command",
            "command": "python /path/to/preflight_hook.py"
          }]
        }]
      }
    }

Claude Code passes tool input as JSON on stdin:
    {"tool": "Bash", "input": {"command": "git log"}}

The hook writes to stdout:
    - Nothing (exit 0)    → proceed as-is
    - JSON block (exit 0) → Claude Code shows the message before running
    - exit 2              → block the call (Claude Code will not run it)

This hook uses exit 0 + message only — it advises, never blocks.
Agents that want hard blocking can change the exit code logic.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from typing import NamedTuple

MIN_PYTHON = (3, 10)

_SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(_SKILL_DIR))

from runner import preflight, PreflightAdvice  # noqa: E402


def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"preflight_hook.py requires Python {required}+; current Python is {current}. Run it with `uv run` or a Python {required}+ interpreter.",
            file=sys.stderr,
        )
        sys.exit(2)


class ShellScan(NamedTuple):
    text: str        # comments and backslash-newline continuations removed, whitespace-trimmed
    multiline: bool  # an unquoted newline separates the input into several commands


def scan_shell(command: str) -> ShellScan:
    """Read a Bash command the way bash splits lines, which shlex cannot.

    - A comment runs from a # that starts a word outside quotes to the end of its line;
      a mid-word # (URL fragment), a quoted "#fff", and an escaped \\# are literal
    - Backslash-newline outside single quotes is a continuation and disappears
    - Any other unquoted newline separates commands
    """
    kept: list[str] = []
    newlines: list[int] = []
    quote = ""
    in_comment = False
    index = 0
    while index < len(command):
        char = command[index]
        following = command[index + 1] if index + 1 < len(command) else ""
        if in_comment:
            if char != "\n":
                index += 1
                continue
            in_comment = False
        if char == "\\" and quote != "'":
            if following != "\n":
                kept.append(char + following)
            index += 2
            continue
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "#" and (not kept or kept[-1] in (" ", "\t", "\n", ";", "|", "&", "(", ")")):
            in_comment = True
            index += 1
            continue
        elif char == "\n":
            newlines.append(len(kept))
        kept.append(char)
        index += 1
    lead = 0
    while lead < len(kept) and kept[lead].isspace():
        lead += 1
    tail = len(kept)
    while tail > lead and kept[tail - 1].isspace():
        tail -= 1
    return ShellScan("".join(kept[lead:tail]), any(lead <= position < tail for position in newlines))


def main() -> None:
    require_supported_python()

    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)  # not JSON — pass through

    # Extract the bash command string
    command_str: str = ""
    inp = payload.get("input") or payload.get("tool_input") or {}
    if isinstance(inp, dict):
        command_str = str(inp.get("command", ""))
    elif isinstance(inp, str):
        command_str = inp

    scan = scan_shell(command_str)
    if not scan.text or scan.multiline:
        sys.exit(0)  # empty, or several commands on separate lines
    command_str = scan.text

    # Parse shell command into argv (best-effort; compound commands pass through)
    try:
        argv = shlex.split(command_str)
    except ValueError:
        sys.exit(0)  # shell syntax we can't parse — pass through

    # Skip compound shell expressions (pipes, &&, ||, ;, redirections, subshells). A second
    # lexer splits operators out of words, so "list;" and "a&&b" are caught; quoted text is not
    operators = shlex.shlex(command_str, posix=True, punctuation_chars=True)
    operators.whitespace_split = True
    operators.commenters = ""  # a mid-word "#" (URL fragment) is not a comment in bash
    if any(tok and set(tok) <= set("|&;<>()") for tok in operators):
        sys.exit(0)

    advice = preflight(argv)

    if advice.safe:
        sys.exit(0)

    # Build advisory message for Claude Code to show before running
    lines = [
        f"FailSense pre-flight: §{advice.failure_mode_id} risk detected ({advice.risk_level})",
        f"  {advice.reason}",
    ]
    if advice.recommended_call:
        lines.append(f"  Recommended: {shlex.join(advice.recommended_call)}")
    else:
        lines.append("  No drop-in substitute — agent should reconsider the approach.")

    # Claude Code hook output: print message, exit 0 to advise without blocking
    print("\n".join(lines))
    sys.exit(0)


if __name__ == "__main__":
    main()
