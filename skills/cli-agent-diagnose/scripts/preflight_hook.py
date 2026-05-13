#!/usr/bin/env python3
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

_SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(_SKILL_DIR))

from runner import preflight, PreflightAdvice  # noqa: E402


def main() -> None:
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

    if not command_str.strip():
        sys.exit(0)

    # Parse shell command into argv (best-effort; compound commands pass through)
    try:
        argv = shlex.split(command_str)
    except ValueError:
        sys.exit(0)  # shell syntax we can't parse — pass through

    # Skip compound shell expressions (pipes, &&, ||, ;)
    for tok in argv:
        if tok in ("|", "&&", "||", ";", ">", ">>", "<"):
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
