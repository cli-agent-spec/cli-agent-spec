# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Parse, analyze, and navigate ATIF agent trajectory files (schema_version ATIF-v1.x).

Extracts tool calls with their observations, infers exit codes, classifies
outcomes, and optionally feeds bash invocations through the diagnose pipeline.

Usage:
    uv run scripts/traj.py <traj.json> [options]
    uv run scripts/traj.py <traj.json> --stats
    uv run scripts/traj.py <traj.json> --show --errors
    uv run scripts/traj.py <traj.json> --show --steps 1-5,12,30-37
    uv run scripts/traj.py <traj.json> --show --tool bash
    uv run scripts/traj.py <traj.json> --diagnose
    uv run scripts/traj.py <traj.json> --jsonl | uv run scripts/analyze.py

Typical diagnosis pipeline:
    uv run scripts/traj.py cc749d09-traj.txt --diagnose
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

MIN_PYTHON = (3, 10)

_SCRIPTS_DIR = Path(__file__).parent
_DIAGNOSE = _SCRIPTS_DIR / "diagnose.py"

# ── Exit code inference ───────────────────────────────────────────────────────

_EXIT_CODE_RE = re.compile(r"\[exit code:\s*(-?\d+)\]\s*$", re.MULTILINE)

_ERROR_WORDS = (
    "traceback (most recent call last)",
    "error:",
    "exception:",
    "no module named",
    "command not found",
    "permission denied",
    "no such file or directory",
    "syntaxerror",
    "nameerror",
    "typeerror",
    "valueerror",
    "importerror",
    "modulenotfounderror",
    "attributeerror",
    "runtimeerror",
    "assertionerror",
    "failed:",
    "fatal:",
    "panic:",
)


def _infer_exit_code(content: str, function: str) -> int:
    """Infer exit code from tool output content.

    Only bash calls embed explicit `[exit code: N]` markers or emit error
    patterns in stdout/stderr.  File-operation tools (write_file, edit_file,
    read_file) don't have exit codes — their content is file data or diffs,
    which will contain code strings that look like error messages but aren't.
    """
    if function != "bash":
        return 0
    m = _EXIT_CODE_RE.search(content)
    if m:
        return int(m.group(1))
    lower = content.lower()
    if any(w in lower for w in _ERROR_WORDS):
        return 1
    return 0


def _strip_exit_code_marker(content: str) -> str:
    return _EXIT_CODE_RE.sub("", content).rstrip()


# ── Outcome classification ────────────────────────────────────────────────────

# File-op success signals: these patterns confirm the tool succeeded
_FILE_OP_SUCCESS = re.compile(
    r"^(Wrote|Edited|Created|Renamed|Deleted|Copied)\b",
    re.MULTILINE,
)


def _classify_outcome(content: str, exit_code: int, function: str) -> str:
    if exit_code != 0:
        return "fail"
    if function != "bash":
        # For file ops: explicit error prefix means failure; otherwise success
        lower = content.lstrip()[:200].lower()
        if lower.startswith(("error", "failed", "permission denied", "no such file")):
            return "fail"
        return "success"
    lower = content.lower()
    if any(w in lower for w in _ERROR_WORDS):
        return "fail"
    if "warning:" in lower:
        return "warn"
    return "success"


_OUTCOME_ICON = {"success": "✓", "fail": "✗", "warn": "⚠", "unknown": "?"}


# ── ATIF-v1.2 content normalisation ──────────────────────────────────────────

# v1.2 embeds "[stdout]", "[error] tool reported failure", and "[metadata] {...}"
# markers inside observation content — and duplicates the stdout section.
_METADATA_TAG_RE = re.compile(r"\n\[metadata\]\s*\{.*\}\s*$", re.DOTALL)
_STDOUT_TAG_RE   = re.compile(r"\n\[stdout\]\n.*$", re.DOTALL)
_ERROR_TAG_RE    = re.compile(r"\n?\[error\]\s*tool reported failure\s*$")
_EXIT_CODE_PREFIX_RE = re.compile(r"^Exit code\s+(-?\d+)\n?")

# Map v1.2 PascalCase tool names to the normalised lowercase names used elsewhere
_FUNCTION_NAME_MAP: dict[str, str] = {
    "Bash":       "bash",
    "Read":       "read_file",
    "Write":      "write_file",
    "Edit":       "edit_file",
    "Glob":       "glob",
    "Grep":       "grep",
    "LS":         "ls",
    "TodoRead":   "todo_read",
    "TodoWrite":  "todo_write",
    "WebSearch":  "web_search",
    "WebFetch":   "web_fetch",
    "Task":       "task",
    "ExitPlanMode": "exit_plan_mode",
    "NotebookRead": "notebook_read",
    "NotebookEdit": "notebook_edit",
}


def _normalise_function(name: str) -> str:
    return _FUNCTION_NAME_MAP.get(name, name.lower())


def _clean_v12_content(content: str) -> str:
    """Strip v1.2-specific noise markers from observation content."""
    content = _METADATA_TAG_RE.sub("", content)
    content = _STDOUT_TAG_RE.sub("", content)
    content = _ERROR_TAG_RE.sub("", content)
    return content.rstrip()


def _extract_v12_tool_call(
    tc_raw: dict,
    extra: dict,
    content: str,
) -> tuple[str, int]:
    """Return (clean_content, exit_code) for a v1.2 tool step.

    v1.2 stores clean stdout/stderr in extra.tool_result_metadata.tool_use_result
    (for Bash) or extra.tool_result_metadata.raw_tool_result.content.
    The is_error flag is definitive for exit code.
    """
    is_error: bool = bool(extra.get("tool_result_is_error", False))
    metadata: dict = extra.get("tool_result_metadata") or extra.get("metadata") or {}

    tool_use_result: dict = metadata.get("tool_use_result") or {}
    raw_result: dict = metadata.get("raw_tool_result") or {}

    # Bash: prefer separate stdout field; missing for error cases
    fn = _normalise_function(tc_raw.get("function_name", ""))
    if fn == "bash":
        stdout = tool_use_result.get("stdout", "")
        stderr = tool_use_result.get("stderr", "")
        if stdout or stderr:
            clean = (stdout + ("\n" + stderr if stderr.strip() else "")).rstrip()
        else:
            # Error path: clean the raw content
            clean = _clean_v12_content(content)
            m = _EXIT_CODE_PREFIX_RE.match(clean)
            if m:
                is_error = True
                clean = clean[m.end():].rstrip()
    elif fn == "read_file":
        # Prefer the file.content field for clean text without line-number prefixes
        file_obj = tool_use_result.get("file") or {}
        clean = file_obj.get("content") or _clean_v12_content(content)
    else:
        raw_content = raw_result.get("content", "")
        clean = raw_content if raw_content else _clean_v12_content(content)

    exit_code = 1 if is_error else 0
    return clean, exit_code


# ── ATIF parsing ─────────────────────────────────────────────────────────────

def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fmt_ts(ts: str) -> str:
    dt = _parse_ts(ts)
    return dt.strftime("%H:%M:%S") if dt else ts


def _fmt_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    if ms < 60_000:
        return f"{ms / 1000:.1f}s"
    m, s = divmod(ms // 1000, 60)
    return f"{m}m{s:02d}s"


def _elapsed_between(ts1: str, ts2: str) -> str:
    dt1, dt2 = _parse_ts(ts1), _parse_ts(ts2)
    if dt1 is None or dt2 is None:
        return ""
    delta_ms = int((dt2 - dt1).total_seconds() * 1000)
    return _fmt_duration(delta_ms)


class ToolCall:
    __slots__ = ("call_id", "function", "arguments", "content", "exit_code", "outcome")

    def __init__(
        self,
        call_id: str,
        function: str,
        arguments: dict,
        content: str,
        exit_code: int,
        outcome: str,
    ) -> None:
        self.call_id = call_id
        self.function = function
        self.arguments = arguments
        self.content = content
        self.exit_code = exit_code
        self.outcome = outcome

    def cmd_summary(self, width: int = 120) -> str:
        """One-line summary of what the tool call did."""
        fn = self.function
        if fn == "bash":
            cmd = self.arguments.get("command", "")
            first = cmd.split("\n")[0]
            return first[:width]
        if fn == "write_file":
            return f"write {self.arguments.get('path', '?')} ({len(self.arguments.get('content', ''))} bytes)"
        if fn == "edit_file":
            return f"edit {self.arguments.get('path', '?')}"
        if fn == "read_file":
            return f"read {self.arguments.get('file_path', self.arguments.get('path', '?'))}"
        if fn in ("glob", "grep", "ls"):
            return f"{fn} {json.dumps(self.arguments)[:80]}"
        # Generic fallback
        args_short = json.dumps(self.arguments)[:80]
        return f"{fn}({args_short})"


class Step:
    __slots__ = (
        "step_id", "timestamp", "source", "message", "reasoning",
        "tool_calls", "metrics",
    )

    def __init__(
        self,
        step_id: int,
        timestamp: str,
        source: str,
        message: str,
        reasoning: str,
        tool_calls: list[ToolCall],
        metrics: dict,
    ) -> None:
        self.step_id = step_id
        self.timestamp = timestamp
        self.source = source
        self.message = message
        self.reasoning = reasoning
        self.tool_calls = tool_calls
        self.metrics = metrics

    @property
    def elapsed_ms(self) -> int:
        return (self.metrics.get("extra") or {}).get("elapsed_ms", 0)

    @property
    def has_error(self) -> bool:
        return any(tc.outcome == "fail" for tc in self.tool_calls)

    @property
    def tool_names(self) -> list[str]:
        return [tc.function for tc in self.tool_calls]


class Trajectory:
    __slots__ = ("schema_version", "session_id", "agent", "steps", "final_metrics")

    def __init__(
        self,
        schema_version: str,
        session_id: str,
        agent: dict,
        steps: list[Step],
        final_metrics: dict,
    ) -> None:
        self.schema_version = schema_version
        self.session_id = session_id
        self.agent = agent
        self.steps = steps
        self.final_metrics = final_metrics

    @property
    def agent_name(self) -> str:
        return self.agent.get("name", "?")

    @property
    def agent_version(self) -> str:
        return self.agent.get("version", "")

    @property
    def model(self) -> str:
        # model_name may appear in agent dict or per-step
        return self.agent.get("model_name", "?")

    @property
    def start_ts(self) -> str:
        return self.steps[0].timestamp if self.steps else ""

    @property
    def end_ts(self) -> str:
        return self.steps[-1].timestamp if self.steps else ""

    @property
    def duration(self) -> str:
        return _elapsed_between(self.start_ts, self.end_ts)

    @property
    def tool_calls(self) -> list[ToolCall]:
        result = []
        for s in self.steps:
            result.extend(s.tool_calls)
        return result

    @property
    def bash_calls(self) -> list[ToolCall]:
        return [tc for tc in self.tool_calls if tc.function == "bash"]

    @property
    def error_steps(self) -> list[Step]:
        return [s for s in self.steps if s.has_error]


def _load(path: Path) -> Trajectory:
    raw = json.loads(path.read_text(encoding="utf-8"))

    schema_version = raw.get("schema_version", "unknown")
    session_id = raw.get("session_id", "")
    agent = raw.get("agent", {})
    final_metrics = raw.get("final_metrics", {})
    is_v12 = schema_version.startswith("ATIF-v1.2")

    raw_steps = raw.get("steps", [])

    if is_v12:
        steps = _load_v12_steps(raw_steps)
    else:
        steps = _load_v16_steps(raw_steps)

    return Trajectory(
        schema_version=schema_version,
        session_id=session_id,
        agent=agent,
        steps=steps,
        final_metrics=final_metrics,
    )


def _load_v16_steps(raw_steps: list[dict]) -> list[Step]:
    steps: list[Step] = []
    for s in raw_steps:
        results_by_id: dict[str, str] = {}
        for r in (s.get("observation") or {}).get("results", []):
            results_by_id[r.get("source_call_id", "")] = r.get("content", "")

        tool_calls: list[ToolCall] = []
        for tc_raw in s.get("tool_calls", []):
            call_id = tc_raw.get("tool_call_id", "")
            function = _normalise_function(tc_raw.get("function_name", ""))
            arguments = tc_raw.get("arguments", {})
            content = results_by_id.get(call_id, "")
            exit_code = _infer_exit_code(content, function)
            outcome = _classify_outcome(content, exit_code, function)
            tool_calls.append(ToolCall(
                call_id=call_id,
                function=function,
                arguments=arguments,
                content=content,
                exit_code=exit_code,
                outcome=outcome,
            ))

        steps.append(Step(
            step_id=s.get("step_id", 0),
            timestamp=s.get("timestamp", ""),
            source=s.get("source", ""),
            message=s.get("message", ""),
            reasoning=s.get("reasoning_content", ""),
            tool_calls=tool_calls,
            metrics=s.get("metrics", {}),
        ))
    return steps


def _load_v12_steps(raw_steps: list[dict]) -> list[Step]:
    """Parse ATIF-v1.2 steps.

    v1.2 fragments each agent turn into multiple steps:
      - reasoning step  (message=""  or reasoning text, metrics present)
      - message step    (user-facing message, no tool_calls)
      - tool-exec step  (tool_calls + observation, no metrics)

    We consolidate them: tool-exec steps absorb the nearest preceding message.
    Pure reasoning-only steps (blank message, no tools) are hidden by default.
    """
    # Index raw steps
    id_to_raw: dict[int, dict] = {s.get("step_id", i): s for i, s in enumerate(raw_steps)}

    # Forward pass: find the user-facing message for each tool-exec step
    # (the last non-empty agent message before the tool call in source order)
    last_agent_msg: str = ""
    last_reasoning: str = ""
    last_metrics: dict = {}

    steps: list[Step] = []
    for s in raw_steps:
        source = s.get("source", "")
        raw_tools = s.get("tool_calls", [])
        msg = s.get("message", "")
        reasoning = s.get("reasoning_content", "")
        metrics = s.get("metrics", {})
        extra = s.get("extra", {})

        if source == "user":
            steps.append(Step(
                step_id=s.get("step_id", 0),
                timestamp=s.get("timestamp", ""),
                source="user",
                message=msg,
                reasoning="",
                tool_calls=[],
                metrics={},
            ))
            last_agent_msg = ""
            last_reasoning = ""
            last_metrics = {}
            continue

        # Agent step
        if not raw_tools:
            # Message-only or reasoning-only step — accumulate for the next tool step
            if reasoning:
                last_reasoning = reasoning
            if msg.strip():
                last_agent_msg = msg
            if metrics:
                last_metrics = metrics
            # Emit as a visible step only if it has a real user-facing message
            # and is the final turn (stop_reason=end_turn), not a precursor to tools
            stop_reason = extra.get("stop_reason", "")
            if stop_reason == "end_turn" and msg.strip():
                steps.append(Step(
                    step_id=s.get("step_id", 0),
                    timestamp=s.get("timestamp", ""),
                    source="agent",
                    message=msg,
                    reasoning=last_reasoning or reasoning,
                    tool_calls=[],
                    metrics=metrics or last_metrics,
                ))
                last_agent_msg = ""
                last_reasoning = ""
                last_metrics = {}
            continue

        # Tool-execution step
        results_by_id: dict[str, str] = {}
        for r in (s.get("observation") or {}).get("results", []):
            results_by_id[r.get("source_call_id", "")] = r.get("content", "")

        tool_calls: list[ToolCall] = []
        for tc_raw in raw_tools:
            call_id = tc_raw.get("tool_call_id", "")
            function = _normalise_function(tc_raw.get("function_name", ""))
            arguments = tc_raw.get("arguments") or tc_raw.get("extra", {}).get("raw_arguments", {})
            raw_content = results_by_id.get(call_id, "")
            # v1.2: extract clean content and authoritative exit code from extra
            content, exit_code = _extract_v12_tool_call(tc_raw, extra, raw_content)
            outcome = _classify_outcome(content, exit_code, function)
            tool_calls.append(ToolCall(
                call_id=call_id,
                function=function,
                arguments=arguments,
                content=content,
                exit_code=exit_code,
                outcome=outcome,
            ))

        steps.append(Step(
            step_id=s.get("step_id", 0),
            timestamp=s.get("timestamp", ""),
            source="agent",
            message=last_agent_msg,
            reasoning=last_reasoning,
            tool_calls=tool_calls,
            metrics=last_metrics,
        ))
        last_agent_msg = ""
        last_reasoning = ""
        last_metrics = {}

    return steps


# ── Step range parsing ────────────────────────────────────────────────────────

def _parse_step_range(spec: str) -> set[int]:
    """Parse '1-5,10,15-20' into a set of ints."""
    result: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            result.update(range(int(lo), int(hi) + 1))
        else:
            result.add(int(part))
    return result


# ── Human-readable display ────────────────────────────────────────────────────

def _print_header(traj: Trajectory) -> None:
    agent_str = f"{traj.agent_name}"
    if traj.agent_version:
        agent_str += f" {traj.agent_version}"
    print(f"━━━ {traj.schema_version}  {agent_str} ({traj.model})  session={traj.session_id[:8]} ━━━")
    fm = traj.final_metrics
    pt = fm.get("total_prompt_tokens", "?")
    ct = fm.get("total_completion_tokens", "?")
    cached = fm.get("total_cached_tokens", "?")
    print(f"  {fm.get('total_steps', len(traj.steps))} steps · {pt} prompt · {ct} completion · {cached} cached")
    print(f"  {_fmt_ts(traj.start_ts)} → {_fmt_ts(traj.end_ts)}  ({traj.duration})\n")


def _print_step(step: Step, tail: int, prev_ts: str = "") -> None:
    elapsed = f" +{_fmt_duration(step.elapsed_ms)}" if step.elapsed_ms else ""
    since = f"  ←{_elapsed_between(prev_ts, step.timestamp)}" if prev_ts else ""

    if step.source == "user":
        print(f"Step {step.step_id}  [user]  {_fmt_ts(step.timestamp)}{since}")
        msg = step.message.strip()
        if msg:
            first_line = msg.split("\n")[0]
            print(f"  {first_line[:120]}")
        return

    tool_summary = ""
    if step.tool_calls:
        tools = ", ".join(tc.function for tc in step.tool_calls)
        icons = " ".join(_OUTCOME_ICON.get(tc.outcome, "?") for tc in step.tool_calls)
        tool_summary = f"  [{tools}] {icons}"

    print(f"Step {step.step_id}  [agent]  {_fmt_ts(step.timestamp)}{since}{elapsed}{tool_summary}")

    # Message (agent text response)
    if step.message.strip():
        first = step.message.strip().split("\n")[0]
        print(f"  msg: {first[:110]}")

    # Each tool call
    for tc in step.tool_calls:
        icon = _OUTCOME_ICON.get(tc.outcome, "?")
        print(f"  ┌ {icon} {tc.cmd_summary()}")

        # Full bash command if multiline
        if tc.function == "bash":
            cmd = tc.arguments.get("command", "")
            lines = cmd.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:min(len(lines), 5)]:
                    print(f"  │   {line}")
                if len(lines) > 5:
                    print(f"  │   … ({len(lines) - 5} more lines)")

        # Output tail
        content = _strip_exit_code_marker(tc.content)
        if content.strip():
            output_lines = content.strip().splitlines()
            shown = output_lines[-tail:]
            skipped = len(output_lines) - len(shown)
            if skipped > 0:
                print(f"  │ ({skipped} lines skipped)")
            for line in shown:
                print(f"  │ {line}")

        if tc.exit_code != 0:
            print(f"  └ exit_code={tc.exit_code}")
        else:
            print("  └")


# ── Stats display ─────────────────────────────────────────────────────────────

def _print_stats(traj: Trajectory) -> None:
    all_tools = traj.tool_calls
    fn_counts: dict[str, int] = {}
    for tc in all_tools:
        fn_counts[tc.function] = fn_counts.get(tc.function, 0) + 1
    fn_str = "  ".join(f"{k}={v}" for k, v in sorted(fn_counts.items(), key=lambda x: -x[1]))

    agent_steps = [s for s in traj.steps if s.source == "agent"]
    user_steps = [s for s in traj.steps if s.source == "user"]
    error_steps = traj.error_steps
    bash_errors = [tc for tc in traj.bash_calls if tc.outcome == "fail"]

    fm = traj.final_metrics
    pt = fm.get("total_prompt_tokens", "?")
    ct = fm.get("total_completion_tokens", "?")
    cached = fm.get("total_cached_tokens", "?")

    elapsed_vals = [s.elapsed_ms for s in agent_steps if s.elapsed_ms > 0]
    avg_latency = f"{sum(elapsed_vals) / len(elapsed_vals) / 1000:.1f}s" if elapsed_vals else "?"
    max_latency_step = max(agent_steps, key=lambda s: s.elapsed_ms, default=None)
    max_latency_str = (
        f"  (step {max_latency_step.step_id}: {_fmt_duration(max_latency_step.elapsed_ms)})"
        if max_latency_step else ""
    )

    print("━━━ Session Stats ━━━")
    print(f"  session:    {traj.session_id}")
    print(f"  agent:      {traj.agent_name} {traj.agent_version}")
    print(f"  model:      {traj.model}")
    print(f"  duration:   {_fmt_ts(traj.start_ts)} → {_fmt_ts(traj.end_ts)}  ({traj.duration})")
    print(f"  steps:      {len(traj.steps)}  ({len(user_steps)} user · {len(agent_steps)} agent)")
    print(f"  tool calls: {len(all_tools)}  {fn_str}")
    print(f"  errors:     {len(error_steps)} step(s) with failures  ({len(bash_errors)} bash errors)")
    if error_steps:
        for s in error_steps:
            for tc in s.tool_calls:
                if tc.outcome == "fail":
                    print(f"              step {s.step_id}: {tc.cmd_summary(80)} [exit {tc.exit_code}]")
    cost = fm.get("total_cost_usd")
    cost_str = f"  · ${cost:.4f}" if cost is not None else ""
    print(f"  tokens:     {pt} prompt · {ct} completion · {cached} cached{cost_str}")
    print(f"  latency:    avg {avg_latency}/step{max_latency_str}")


# ── Tool call evaluation ──────────────────────────────────────────────────────

# Patterns that signal unbounded / noisy output
_GIT_LOG_UNBOUNDED = re.compile(r"\bgit\s+(--no-pager\s+)?log\b(?!.*(?:-n\s*\d|--max-count|--oneline.*-\d))", re.IGNORECASE)
_GIT_DIFF_UNBOUNDED = re.compile(r"\bgit\s+(?:diff|show)\b(?!.*--stat\b)", re.IGNORECASE)
_APT_NOISY = re.compile(r"\bapt(?:-get)?\s+(?:install|upgrade|update)\b", re.IGNORECASE)
_LS_BARE = re.compile(r"(?:^|&&|\|)\s*ls(?:\s+-[lah]+)?\s*(?:/[^\s]*)?(?:\s*$|&&|\|)", re.IGNORECASE)
_GREP_UNBOUNDED = re.compile(r"\bgrep\b(?!.*-m\s*\d)(?!.*--max-count)", re.IGNORECASE)
_FIND_DEEP = re.compile(r"\bfind\b(?!.*-maxdepth)", re.IGNORECASE)
_CAT_LARGE = re.compile(r"\bcat\b(?!\s*/dev/)", re.IGNORECASE)
_AND_CHAIN = re.compile(r"&&")

# Patterns in stdout that indicate wasted output
_PROGRESS_LINES = re.compile(r"^\s*(?:Get:|Hit:|Ign:|Reading|Building|Processing|Setting up|Selecting)\b", re.MULTILINE)
_BLANK_HEAVY = re.compile(r"\n{3,}")


def _eval_call(tc: "ToolCall") -> dict:
    """
    Evaluate one bash tool call for command efficiency and output token waste.

    Returns a dict with:
      lines, bytes       — raw output size
      signal             — "high" | "medium" | "low"
      issues             — list of detected inefficiency patterns
      rewrite            — suggested improved command, or None
    """
    if tc.function != "bash":
        return {}

    cmd = tc.arguments.get("command", "")
    content = _strip_exit_code_marker(tc.content)
    out_lines = content.strip().splitlines() if content.strip() else []
    out_bytes = len(content.encode())
    n_lines   = len(out_lines)

    issues:  list[str] = []
    rewrite: str | None = None

    # ── Command-level patterns ─────────────────────────────────────────────────

    # Unbounded git log
    if _GIT_LOG_UNBOUNDED.search(cmd):
        issues.append("git log without -n — add --oneline -20 to bound output")
        rewrite = re.sub(r"(git\s+(?:--no-pager\s+)?log)\b", r"\1 --oneline -20", cmd, count=1)

    # git diff without --stat (can be huge)
    if _GIT_DIFF_UNBOUNDED.search(cmd) and n_lines > 30:
        issues.append(f"git diff produced {n_lines} lines — add --stat for a summary first")
        if not rewrite:
            rewrite = re.sub(r"(git\s+(?:diff|show))\b", r"\1 --stat", cmd, count=1)

    # apt-get producing noise
    if _APT_NOISY.search(cmd):
        if n_lines > 20:
            issues.append(f"apt-get produced {n_lines} lines — add -qq to suppress progress")
            if not rewrite:
                rewrite = re.sub(r"\bapt(?:-get)?\s+install\b", "apt-get install -qq", cmd, count=1)

    # bare ls (rarely adds signal)
    if _LS_BARE.search(cmd) and tc.outcome == "success":
        issues.append("ls adds little signal — prefer grep/find for targeted lookup")

    # grep without line limit on large repos
    if _GREP_UNBOUNDED.search(cmd) and n_lines > 50:
        issues.append(f"grep produced {n_lines} lines — add -m 20 to cap matches")
        if not rewrite:
            rewrite = re.sub(r"\bgrep\b", "grep -m 20", cmd, count=1)

    # find without maxdepth on large output
    if _FIND_DEEP.search(cmd) and n_lines > 50:
        issues.append(f"find produced {n_lines} lines — add -maxdepth 3 to limit scope")
        if not rewrite:
            rewrite = re.sub(r"\bfind\b", "find -maxdepth 3", cmd, count=1)

    # cat of file (use Read tool instead)
    if _CAT_LARGE.search(cmd) and n_lines > 20:
        issues.append("cat in bash produces raw output — prefer the Read tool for file inspection")

    # Long && chain where exit codes are masked
    chain_parts = [p.strip() for p in _AND_CHAIN.split(cmd) if p.strip()]
    if len(chain_parts) > 4:
        issues.append(
            f"&& chain of {len(chain_parts)} commands — failures in early parts mask later results; split into separate calls"
        )

    # ── Output-level patterns ──────────────────────────────────────────────────

    # Merge conflict in output — wrong command used
    if "CONFLICT" in content and re.search(r"git merge", cmd):
        issues.append("merge exited with CONFLICT — use git merge -X theirs <ref> to auto-resolve")
        if not rewrite:
            rewrite = re.sub(r"(git merge\b)", r"\1 -X theirs", cmd, count=1)

    # Progress/packaging noise dominates output
    progress_lines = len(_PROGRESS_LINES.findall(content))
    if progress_lines > 10 and progress_lines > n_lines * 0.4:
        issues.append(
            f"{progress_lines}/{n_lines} lines are package-manager progress noise — redirect with -qq or 2>/dev/null"
        )

    # Large output in general
    if out_bytes > 20_000 and not issues:
        issues.append(f"stdout is {out_bytes:,} bytes — narrow the query to reduce context load")

    # Empty output from a success — may indicate a silent failure
    if tc.outcome == "success" and not content.strip() and tc.exit_code == 0:
        issues.append("command succeeded with empty output — verify it actually ran")

    # ── Signal rating ──────────────────────────────────────────────────────────
    if tc.outcome == "fail":
        signal = "fail"
    elif out_bytes > 20_000 or (issues and any("lines" in i for i in issues)):
        signal = "low"
    elif issues:
        signal = "medium"
    else:
        signal = "high"

    return {
        "lines":   n_lines,
        "bytes":   out_bytes,
        "signal":  signal,
        "issues":  issues,
        "rewrite": rewrite,
    }


_SIGNAL_ICON = {"high": "✓", "medium": "⚠", "low": "↓", "fail": "✗"}


def _print_eval(traj: "Trajectory") -> None:
    """Print per-call efficiency evaluation for all bash tool calls."""
    bash_steps = [s for s in traj.steps if any(tc.function == "bash" for tc in s.tool_calls)]
    if not bash_steps:
        print("no bash calls to evaluate")
        return

    total_bytes  = 0
    total_issues = 0

    for step in bash_steps:
        for tc in step.tool_calls:
            if tc.function != "bash":
                continue

            ev = _eval_call(tc)
            signal = ev.get("signal", "?")
            icon   = _SIGNAL_ICON.get(signal, "?")
            n      = ev.get("lines", 0)
            b      = ev.get("bytes", 0)
            total_bytes  += b
            total_issues += len(ev.get("issues", []))

            cmd_first = tc.arguments.get("command", "").split("\n")[0][:90]
            print(f"\nstep {step.step_id:>2}  {icon} signal={signal:<6}  {n:>4} lines  {b:>7,} bytes")
            print(f"       cmd: {cmd_first}")

            for issue in ev.get("issues", []):
                print(f"       ⚠  {issue}")

            if ev.get("rewrite"):
                rw_first = ev["rewrite"].split("\n")[0][:90]
                print(f"       →   {rw_first}")

    print(f"\n{'─'*60}")
    print(f"total stdout: {total_bytes:,} bytes across {len(bash_steps)} bash step(s)  ·  {total_issues} issue(s)")


# ── JSONL emission ────────────────────────────────────────────────────────────

def _emit_jsonl(traj: Trajectory) -> None:
    """Emit compact JSONL records compatible with analyze.py (one per tool call)."""
    for step in traj.steps:
        for tc in step.tool_calls:
            if tc.function != "bash":
                continue
            content = _strip_exit_code_marker(tc.content)
            # Infer stdout/stderr split: ATIF collapses them into 'content'
            # We treat the content as stdout unless it looks like only errors
            stdout = content
            stderr = ""
            if tc.exit_code != 0:
                # Best guess: content is stderr-like
                stderr = content
                stdout = ""

            record = {
                "session": traj.session_id[:8],
                "ts": step.timestamp,
                "tool": tc.function,
                "command": tc.arguments.get("command", ""),
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": tc.exit_code,
                "outcome": tc.outcome,
                "has_stderr": bool(stderr.strip()),
                "stdout_lines": stdout.count("\n") + 1 if stdout.strip() else 0,
                "stdout_bytes": len(stdout.encode()),
                "shape": "simple",
                "run": 1,
                "step_id": step.step_id,
            }
            print(json.dumps(record, ensure_ascii=False))


# ── Diagnose integration ──────────────────────────────────────────────────────

def _run_diagnose(traj: Trajectory, challenges_dir: str | None, llm: bool = False) -> None:
    """Run diagnose.py on each failing bash call and aggregate the results.

    Passing all calls as a history lump produces false positives because
    numerical output (frame counts, pixel values) contains substrings that
    match credential/version patterns.  Instead, each call is diagnosed
    independently as a single-event trace; matches are de-duplicated by
    failure_mode_id keeping the highest-confidence entry.
    """
    bash_calls = traj.bash_calls
    if not bash_calls:
        print("no bash tool calls found in trajectory", file=sys.stderr)
        return

    # Only diagnose calls that have a non-zero exit code or non-empty stderr
    candidates = [
        tc for tc in bash_calls
        if tc.exit_code != 0 or tc.outcome == "fail"
    ]

    if not candidates:
        print(json.dumps({
            "schema_version": "1.1",
            "matches": [],
            "no_match": True,
            "trace_insufficient": False,
            "suggested_context": [],
            "trace_summary": f"all {len(bash_calls)} bash call(s) succeeded — no failure signals to diagnose",
        }, indent=2))
        return

    cmd_base = ["uv", "run"]
    if llm:
        cmd_base += ["--with", "anthropic"]
    cmd_base.append(str(_DIAGNOSE))
    if challenges_dir:
        cmd_base += ["--challenges-dir", challenges_dir]
    if llm:
        cmd_base.append("--llm")

    # Aggregate matches: de-dup by failure_mode_id, keep highest confidence
    all_matches: dict[int, dict] = {}

    for tc in candidates:
        content = _strip_exit_code_marker(tc.content)
        # ATIF collapses stdout+stderr; for non-zero exit the content is error output
        stdout = "" if tc.exit_code != 0 else content
        stderr = content if tc.exit_code != 0 else ""

        event = {
            "command": tc.arguments.get("command", ""),
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": tc.exit_code,
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(event, f)
            tmp_path = f.name

        try:
            # --history loads the file and parses the JSON object inside;
            # the positional argument expects a JSON string, not a path
            result = subprocess.run(
                cmd_base + ["--history", f.name],
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()
            if not output:
                continue
            parsed = json.loads(output)
        except (json.JSONDecodeError, OSError):
            continue
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        for m in parsed.get("matches", []):
            fid = m["failure_mode_id"]
            if fid not in all_matches or m["confidence"] > all_matches[fid]["confidence"]:
                all_matches[fid] = m
                all_matches[fid]["_source_command"] = event["command"][:120]

    matches = sorted(all_matches.values(), key=lambda x: x["confidence"], reverse=True)
    # Strip internal tracking key before output
    for m in matches:
        m.pop("_source_command", None)

    no_match = len(matches) == 0
    print(json.dumps({
        "schema_version": "1.1",
        "matches": matches,
        "no_match": no_match,
        "trace_insufficient": False,
        "suggested_context": [],
        "trace_summary": (
            f"{len(candidates)} failing bash call(s) examined; "
            f"{len(matches)} failure mode(s) matched"
        ),
    }, indent=2))


# ── Main ──────────────────────────────────────────────────────────────────────

def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(p) for p in MIN_PYTHON)
        current = ".".join(str(p) for p in sys.version_info[:3])
        print(
            f"traj.py requires Python {required}+; current is {current}. "
            f"Run with `uv run`.",
            file=sys.stderr,
        )
        sys.exit(2)


def main() -> None:
    require_supported_python()

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="Path to ATIF trajectory JSON file")
    parser.add_argument(
        "--show",
        action="store_true",
        help="Human-readable step view (default when --stats/--jsonl/--diagnose not set)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print session statistics",
    )
    parser.add_argument(
        "--steps",
        metavar="RANGE",
        help="Show only these steps: '1-5,10,30-37'",
    )
    parser.add_argument(
        "--tool",
        metavar="NAME",
        help="Filter by tool name: bash, write_file, edit_file, read_file",
    )
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Show only steps that contain errors",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=5,
        metavar="N",
        help="Lines of output to show per step in --show mode (default: 5)",
    )
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit compact JSONL (one record per bash call) for piping to analyze.py",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run diagnose.py on extracted bash invocations and print DiagnoseResult JSON",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Evaluate each bash call for command efficiency and output token waste",
    )
    parser.add_argument(
        "--challenges-dir",
        metavar="DIR",
        help="Override path to challenges/ directory for --diagnose",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM signature routing and scoring in --diagnose (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    traj = _load(Path(args.file))

    # Default to --show if no output mode selected
    show_mode = args.show or (not args.stats and not args.jsonl and not args.diagnose and not args.eval)

    if args.stats:
        _print_stats(traj)
        if show_mode:
            print()

    if args.jsonl:
        _emit_jsonl(traj)
        return

    if args.diagnose:
        _run_diagnose(traj, args.challenges_dir, llm=args.llm)
        return

    if args.eval:
        _print_eval(traj)
        return

    if not show_mode:
        return

    # ── Human-readable step view ──────────────────────────────────────────────

    _print_header(traj)

    step_filter: set[int] | None = _parse_step_range(args.steps) if args.steps else None

    prev_ts = ""
    for step in traj.steps:
        if step_filter is not None and step.step_id not in step_filter:
            prev_ts = step.timestamp
            continue

        if args.errors and not step.has_error and step.source != "user":
            prev_ts = step.timestamp
            continue

        if args.tool:
            if step.source == "user":
                prev_ts = step.timestamp
                continue
            if not any(tc.function == args.tool for tc in step.tool_calls):
                prev_ts = step.timestamp
                continue

        _print_step(step, tail=args.tail, prev_ts=prev_ts)
        prev_ts = step.timestamp
        print()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
