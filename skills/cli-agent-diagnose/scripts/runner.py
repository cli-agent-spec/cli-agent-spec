from __future__ import annotations

"""
failsense.runner — transparent subprocess wrapper

Drop-in replacement for subprocess.run that intercepts known failure modes
and applies §N workarounds inline, before returning to the caller.

Usage:
    from skills.cli_agent_diagnose.runner import run

    result = run(["git", "log"])
    # → subprocess.CompletedProcess with fixed output
    # → result.fix contains the §N annotation if a transformation occurred

Two stages:
    1. Pre-flight  — transform the command before running (zero-cost, pattern table)
    2. Post-flight — if output signals a §N, apply workaround and re-run once

The caller's code is unchanged. The only difference is the import.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

try:
    from .diagnose import (
        TraceEvent,
        match_signals,
        CHALLENGES_DIR,
        _load_challenge,
        _ANSI_RE,
    )
except ImportError:
    from diagnose import (  # type: ignore[no-redef]
        TraceEvent,
        match_signals,
        CHALLENGES_DIR,
        _load_challenge,
        _ANSI_RE,
    )


# ---------------------------------------------------------------------------
# Pre-flight transformation table
#
# Each entry: (command_prefix, condition_fn, transform_fn)
#   command_prefix: tuple of strings that must be a prefix of the command
#   condition_fn:   (cmd, kwargs) → bool  — True when transformation applies
#   transform_fn:   (cmd, kwargs) → (new_cmd, new_kwargs, note)
# ---------------------------------------------------------------------------

def _git_log_needs_limit(cmd: list[str], _kwargs: dict) -> bool:
    """git log without -n / --max-count and without pagination flags."""
    args = cmd[1:]  # strip "git" or "git --no-pager"
    if args and args[0] == "--no-pager":
        args = args[1:]
    if not args or args[0] != "log":
        return False
    return not any(a in ("-n", "--max-count", "--no-pager") for a in args)


def _git_log_transform(cmd: list[str], kwargs: dict) -> tuple[list[str], dict, str]:
    new_cmd = ["git", "--no-pager", "log", "--format=%h %s", "-n", "20"]
    # Preserve any extra flags the caller added (e.g. --author, --since)
    extra = [a for a in cmd[2:] if not a.startswith("log")]
    if extra:
        new_cmd.extend(extra)
    return new_cmd, kwargs, "§43 pre-flight: added --no-pager --format=%h\\ %s -n 20"


def _git_diff_unguarded(cmd: list[str], _kwargs: dict) -> bool:
    args = cmd[1:]
    if args and args[0] == "--no-pager":
        return False
    return bool(args) and args[0] in ("diff", "show", "blame")


def _git_diff_transform(cmd: list[str], kwargs: dict) -> tuple[list[str], dict, str]:
    new_cmd = ["git", "--no-pager"] + cmd[1:]
    return new_cmd, kwargs, "§43 pre-flight: added --no-pager"


def _aws_no_output_flag(cmd: list[str], _kwargs: dict) -> bool:
    if not cmd or cmd[0] != "aws":
        return False
    return "--output" not in cmd and "--no-paginate" not in cmd


def _aws_transform(cmd: list[str], kwargs: dict) -> tuple[list[str], dict, str]:
    new_cmd = cmd + ["--output", "json", "--no-paginate"]
    return new_cmd, kwargs, "§43/§19 pre-flight: added --output json --no-paginate"


def _gh_no_json(cmd: list[str], _kwargs: dict) -> bool:
    if not cmd or cmd[0] != "gh":
        return False
    list_cmds = {"repo", "pr", "issue", "run", "release"}
    return len(cmd) >= 2 and cmd[1] in list_cmds and "--json" not in cmd


def _gh_transform(cmd: list[str], kwargs: dict) -> tuple[list[str], dict, str]:
    # Only add --limit if it's a list subcommand
    new_cmd = cmd[:]
    if len(cmd) >= 3 and cmd[2] in ("list", "ls") and "--limit" not in cmd:
        new_cmd += ["--limit", "20"]
    env = dict(kwargs.get("env") or os.environ)
    env["GH_NO_PAGER"] = "1"
    env["NO_COLOR"] = "1"
    new_kwargs = {**kwargs, "env": env}
    return new_cmd, new_kwargs, "§43/§68 pre-flight: GH_NO_PAGER=1 NO_COLOR=1 --limit 20"


def _kubectl_no_output(cmd: list[str], _kwargs: dict) -> bool:
    if not cmd or cmd[0] != "kubectl":
        return False
    return "-o" not in cmd and "--output" not in cmd and "get" in cmd


def _kubectl_transform(cmd: list[str], kwargs: dict) -> tuple[list[str], dict, str]:
    new_cmd = cmd + ["-o", "json"]
    return new_cmd, kwargs, "§43 pre-flight: added -o json for structured output"


_PRE_FLIGHT: list[tuple[
    str,                                                           # match on cmd[0]
    str | None,                                                    # match on cmd[1] (None = any)
    Any,                                                           # condition_fn
    Any,                                                           # transform_fn
]] = [
    ("git",     "log",   _git_log_needs_limit,  _git_log_transform),
    ("git",     "diff",  _git_diff_unguarded,   _git_diff_transform),
    ("git",     "show",  _git_diff_unguarded,   _git_diff_transform),
    ("aws",     None,    _aws_no_output_flag,   _aws_transform),
    ("gh",      None,    _gh_no_json,           _gh_transform),
    ("kubectl", "get",   _kubectl_no_output,    _kubectl_transform),
]


# ---------------------------------------------------------------------------
# Post-flight workaround table
#
# Maps §N → a function that takes the original (cmd, kwargs, result)
# and returns (new_cmd, new_kwargs) for a single re-run attempt.
# Returns None if no re-run is possible.
# ---------------------------------------------------------------------------

def _post_ansi_fix(
    cmd: list[str], kwargs: dict, _result: subprocess.CompletedProcess
) -> tuple[list[str], dict] | None:
    """§68 — strip ANSI via env NO_COLOR=1."""
    env = dict(kwargs.get("env") or os.environ)
    if env.get("NO_COLOR"):
        return None  # already applied
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    return cmd, {**kwargs, "env": env}


def _post_large_output_fix(
    cmd: list[str], kwargs: dict, _result: subprocess.CompletedProcess
) -> tuple[list[str], dict] | None:
    """§43 — try to add a limit flag for known tools."""
    if cmd and cmd[0] == "git":
        return _git_log_transform(cmd, kwargs)[:2]
    return None


def _post_pager_fix(
    cmd: list[str], kwargs: dict, _result: subprocess.CompletedProcess
) -> tuple[list[str], dict] | None:
    """§10 — suppress pager and interactive prompts."""
    env = dict(kwargs.get("env") or os.environ)
    env.update({
        "PAGER": "cat", "GIT_PAGER": "cat", "MANPAGER": "cat",
        "EDITOR": "true", "GIT_EDITOR": "true", "VISUAL": "true",
        "LESS": "-FRX",
    })
    new_kwargs = {
        **kwargs,
        "env": env,
        "stdin": subprocess.DEVNULL,
    }
    return cmd, new_kwargs


_POST_FLIGHT: dict[int, Any] = {
    10:  _post_pager_fix,
    11:  _post_pager_fix,
    43:  _post_large_output_fix,
    68:  _post_ansi_fix,
}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class FixedResult:
    """subprocess.CompletedProcess augmented with FailSense fix metadata."""
    returncode: int
    stdout: str
    stderr: str
    args: list[str]
    fixed: str          # empty string when no fix was applied
    failure_mode_id: int | None   # §N that triggered the fix, or None
    pre_flighted: bool  # True if the fix was applied before running

    @classmethod
    def from_completed(
        cls,
        r: subprocess.CompletedProcess,
        fixed: str = "",
        failure_mode_id: int | None = None,
        pre_flighted: bool = False,
    ) -> FixedResult:
        return cls(
            returncode=r.returncode,
            stdout=r.stdout if isinstance(r.stdout, str) else (r.stdout or b"").decode(errors="replace"),
            stderr=r.stderr if isinstance(r.stderr, str) else (r.stderr or b"").decode(errors="replace"),
            args=list(r.args),
            fixed=fixed,
            failure_mode_id=failure_mode_id,
            pre_flighted=pre_flighted,
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

_OUTPUT_LARGE_THRESHOLD = 50_000   # chars — §43 signal


def run(
    cmd: Sequence[str],
    *,
    timeout: int = 30,
    challenges_dir: Path = CHALLENGES_DIR,
    **kwargs: Any,
) -> FixedResult:
    """
    Transparent subprocess.run replacement with inline §N fixing.

    Passes all kwargs through to subprocess.run (capture_output, env, cwd, etc.).
    Always sets capture_output=True and text=True; callers must not set them.
    Returns FixedResult, a drop-in for subprocess.CompletedProcess plus .fixed and
    .failure_mode_id indicating what (if anything) was transformed.
    """
    cmd_list = list(cmd)

    # Default to text + capture so we can inspect output
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)

    # Stage 1: pre-flight
    pre_cmd, pre_kwargs, pre_note = _apply_pre_flight(cmd_list, kwargs)
    was_pre_flighted = pre_note != ""

    result = subprocess.run(pre_cmd, timeout=timeout, **pre_kwargs)

    # Stage 2: post-flight — inspect output for §N signals
    event = TraceEvent(
        command=pre_cmd[0] if pre_cmd else "",
        args=tuple(pre_cmd[1:]),
        stdout=result.stdout or "",
        stderr=result.stderr or "",
        exit_code=result.returncode,
        timed_out=result.returncode == 124,
    )
    signals = match_signals((event,))

    if not signals:
        return FixedResult.from_completed(result, pre_flighted=was_pre_flighted, fixed=pre_note)

    top = signals[0]

    # If the pre-flight already handled this §N, don't re-run
    if was_pre_flighted and _pre_flight_covers(top.failure_mode_id, pre_note):
        return FixedResult.from_completed(
            result, fixed=pre_note, failure_mode_id=top.failure_mode_id, pre_flighted=True
        )

    post_fn = _POST_FLIGHT.get(top.failure_mode_id)
    if post_fn is None:
        return FixedResult.from_completed(
            result, fixed=pre_note, failure_mode_id=top.failure_mode_id, pre_flighted=was_pre_flighted
        )

    fix_args = post_fn(pre_cmd, pre_kwargs, result)
    if fix_args is None:
        return FixedResult.from_completed(
            result, fixed=pre_note, failure_mode_id=top.failure_mode_id, pre_flighted=was_pre_flighted
        )

    fixed_cmd, fixed_kwargs = fix_args
    fixed_result = subprocess.run(fixed_cmd, timeout=timeout, **fixed_kwargs)

    try:
        challenge = _load_challenge(top.failure_mode_id, challenges_dir)
        note = f"§{top.failure_mode_id} post-flight ({challenge.title}): {top.evidence}"
    except FileNotFoundError:
        note = f"§{top.failure_mode_id} post-flight: {top.evidence}"

    combined_note = f"{pre_note}; {note}" if pre_note else note
    return FixedResult.from_completed(
        fixed_result,
        fixed=combined_note,
        failure_mode_id=top.failure_mode_id,
        pre_flighted=was_pre_flighted,
    )


def _apply_pre_flight(
    cmd: list[str], kwargs: dict
) -> tuple[list[str], dict, str]:
    """Return (new_cmd, new_kwargs, note). note is empty if no transform applied."""
    if not cmd:
        return cmd, kwargs, ""
    for tool, sub, condition, transform in _PRE_FLIGHT:
        if cmd[0] != tool:
            continue
        if sub is not None and (len(cmd) < 2 or cmd[1] != sub):
            continue
        if condition(cmd, kwargs):
            new_cmd, new_kwargs, note = transform(cmd, kwargs)
            return new_cmd, new_kwargs, note
    return cmd, kwargs, ""


def _pre_flight_covers(failure_mode_id: int, pre_note: str) -> bool:
    return f"§{failure_mode_id}" in pre_note


# ---------------------------------------------------------------------------
# Pre-flight advisory — inspect a call before running it
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreflightAdvice:
    """
    Advisory returned before a tool call runs.
    safe=True  → call is fine as-is, proceed.
    safe=False → call will likely trigger a §N failure; use recommended_call instead.
    """
    safe: bool
    risk_level: str                     # "none" | "low" | "medium" | "high" | "critical"
    failure_mode_id: int | None         # predicted §N, or None when safe
    reason: str                         # one sentence
    recommended_call: list[str] | None  # substitute command, or None when safe


def preflight(
    cmd: Sequence[str],
    *,
    history: Sequence[TraceEvent] | None = None,
    challenges_dir: Path = CHALLENGES_DIR,
) -> PreflightAdvice:
    """
    Classify a tool call BEFORE running it. Zero tokens, zero subprocess calls.

    Works from command shape alone for predictable §N failure modes:
      §43 — output unboundedness (git log without -n, aws without --no-paginate)
      §10 — interactivity (git commit without -m, missing --yes flags)
      §19 — retry loop (same call already failed in history)
      §52 — command tree (--help called repeatedly in history)

    Cannot predict output-dependent failures: §38, §53, §68.

    Args:
        cmd:     the command the agent intends to run
        history: prior TraceEvents in this session (enables §19/§52 detection)

    Returns PreflightAdvice. If safe=False, recommended_call is the corrected command.
    """
    cmd_list = list(cmd)

    # --- §19: retry loop — same call already failed in history ---
    if history:
        key = (cmd_list[0] if cmd_list else "", tuple(cmd_list[1:]))
        prior_failures = [
            e for e in history
            if e.command == key[0] and e.args == key[1] and e.exit_code != 0
        ]
        if prior_failures:
            return PreflightAdvice(
                safe=False,
                risk_level="high",
                failure_mode_id=19,
                reason=(
                    f"§19: this exact call failed {len(prior_failures)}× already "
                    f"with no retryable hint — calling again will loop"
                ),
                recommended_call=None,  # no structural fix; agent needs a different approach
            )

        # --- §52: command tree — --help called too many times ---
        help_calls = [
            e for e in history
            if cmd_list and e.command == cmd_list[0] and "--help" in e.args
        ]
        if len(help_calls) >= 2 and "--help" in cmd_list:
            return PreflightAdvice(
                safe=False,
                risk_level="medium",
                failure_mode_id=52,
                reason=(
                    f"§52: --help called {len(help_calls)}× already; "
                    f"schema not discoverable this way — try --schema or tool manifest"
                ),
                recommended_call=[cmd_list[0], "--schema", "--output", "json"]
                if cmd_list else None,
            )

    # --- §10: interactivity — editor/prompt will open ---
    if cmd_list and cmd_list[0] == "git" and len(cmd_list) >= 2:
        sub = cmd_list[1]
        if sub == "commit" and "-m" not in cmd_list and "--message" not in cmd_list:
            return PreflightAdvice(
                safe=False,
                risk_level="critical",
                failure_mode_id=10,
                reason="§10: git commit without -m will open $EDITOR and hang indefinitely",
                recommended_call=None,  # agent must supply the message
            )
        if sub == "rebase" and "-i" in cmd_list:
            return PreflightAdvice(
                safe=False,
                risk_level="critical",
                failure_mode_id=10,
                reason="§10: git rebase -i opens interactive editor — use --exec or scripted rebase",
                recommended_call=None,
            )

    # --- §43: output unboundedness — from pre-flight pattern table ---
    new_cmd, _new_kwargs, note = _apply_pre_flight(cmd_list, {})
    if note:
        # Extract §N from note prefix
        fid_match = re.match(r"§(\d+)", note)
        fid = int(fid_match.group(1)) if fid_match else 43
        severity_map = {10: "critical", 11: "high", 43: "critical", 68: "high"}
        return PreflightAdvice(
            safe=False,
            risk_level=severity_map.get(fid, "high"),
            failure_mode_id=fid,
            reason=note,
            recommended_call=new_cmd,
        )

    return PreflightAdvice(
        safe=True,
        risk_level="none",
        failure_mode_id=None,
        reason="no known failure pattern matches this call",
        recommended_call=None,
    )
