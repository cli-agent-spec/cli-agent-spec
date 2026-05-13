# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
# Note: --llm mode requires the anthropic package. Run with:
#   uv run --with anthropic scripts/diagnose.py ... --llm

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic as _anthropic

def _resolve_challenges_dir() -> Path:
    # 1. Explicit env var override (highest priority)
    env_val = os.environ.get("CLI_AGENT_CHALLENGES_DIR")
    if env_val:
        return Path(env_val)
    # 2. Bundled in skill root (installed: ~/.claude/skills/cli-agent-diagnose/challenges/)
    skill_root = Path(__file__).parent.parent  # scripts/ → skill root
    local = skill_root / "challenges"
    if local.is_dir():
        return local
    # 3. Repo layout: scripts/ → skill dir → skills/ → repo root → challenges/
    repo = skill_root.parent.parent / "challenges"
    if repo.is_dir():
        return repo
    # 4. Current working directory contains a challenges/ dir (running installed, cwd is the repo)
    cwd = Path.cwd() / "challenges"
    if cwd.is_dir():
        return cwd
    return repo  # fall through; FileNotFoundError will surface at first load attempt


CHALLENGES_DIR = _resolve_challenges_dir()
CONFIDENCE_DETERMINISTIC_HIGH = 0.80   # skip LLM; report as-is
CONFIDENCE_LLM_THRESHOLD = 0.15        # below this: don't send to LLM


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TraceEvent:
    command: str
    args: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int
    attempt: int = 1            # 1-based; >1 means this is a retry of (command, args)
    timed_out: bool = False


@dataclass(frozen=True)
class TraceInput:
    events: tuple[TraceEvent, ...]
    source_format: str          # "single" | "history" | "langfuse" | "langsmith" | "text"


@dataclass(frozen=True)
class SignalMatch:
    failure_mode_id: int        # §N
    title: str
    confidence: float           # 0.0–1.0
    evidence: str               # one-sentence human-readable explanation
    workaround: str             # from challenges/*/N-*.md ### Agent Workaround
    memory: str                 # one-liner for agent memory store
    skill_patch: str            # reusable rule for system prompt / skill file
    severity: str               # "critical" | "high" | "medium"
    spec_link: str              # relative path to challenge file
    limitation: str             # from ### Agent Workaround **Limitation:** line
    source: str                 # "deterministic" | "llm"


@dataclass(frozen=True)
class DiagnoseResult:
    matches: tuple[SignalMatch, ...]
    no_match: bool
    trace_insufficient: bool
    suggested_context: tuple[str, ...]
    trace_summary: str
    schema_version: str = "1.0"


# ---------------------------------------------------------------------------
# Stage 1: parse_trace
# ---------------------------------------------------------------------------

def parse_trace(raw: str | dict | list) -> TraceInput:
    """Detect input format and extract structured events."""
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return _parse_text(raw)
        return parse_trace(parsed)

    if isinstance(raw, list):
        return _parse_history(raw)

    if not isinstance(raw, dict):
        raise TypeError(f"unsupported trace input type: {type(raw).__name__}")

    # Langfuse span: has "type" == "SPAN" or "GENERATION"
    if raw.get("type") in ("SPAN", "GENERATION", "TRACE"):
        return _parse_langfuse(raw)

    # LangSmith run: has "run_type" key
    if "run_type" in raw:
        return _parse_langsmith(raw)

    # Single tool call: has "stdout" or "exit_code"
    if "stdout" in raw or "exit_code" in raw:
        return _parse_single(raw)

    # Wrapped history: {"messages": [...]}
    if "messages" in raw and isinstance(raw["messages"], list):
        return _parse_history(raw["messages"])

    raise ValueError(
        f"unrecognized trace format — expected keys: stdout/exit_code, messages, "
        f"run_type, or type=SPAN/GENERATION. Got: {sorted(raw.keys())}"
    )


def _parse_single(raw: dict) -> TraceInput:
    event = TraceEvent(
        command=str(raw.get("command", "")),
        args=tuple(str(a) for a in raw.get("args", [])),
        stdout=str(raw.get("stdout", "")),
        stderr=str(raw.get("stderr", "")),
        exit_code=int(raw.get("exit_code", 0)),
        timed_out=raw.get("exit_code") == 124,
    )
    return TraceInput(events=(event,), source_format="single")


def _parse_history(messages: list) -> TraceInput:
    """
    Extract tool calls from a run.py-style message history.
    Pairs each tool_use block with its tool_result response.
    Tracks (command, args) repetition to identify retries.
    """
    # Collect tool_use inputs keyed by tool_use_id
    tool_inputs: dict[str, dict] = {}
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if isinstance(content, str):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_inputs[block["id"]] = block.get("input", {})

    # Collect tool_results and pair with inputs
    raw_events: list[tuple[str, dict, str]] = []   # (tool_use_id, input_dict, result_text)
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tid = block.get("tool_use_id", "")
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    result_content = " ".join(
                        c.get("text", "") for c in result_content if isinstance(c, dict)
                    )
                raw_events.append((tid, tool_inputs.get(tid, {}), str(result_content)))

    # Parse each result_text: "exit_code=N\nstdout=...\nstderr=..."
    call_counts: dict[tuple[str, tuple[str, ...]], int] = {}
    events: list[TraceEvent] = []

    for _tid, inp, result_text in raw_events:
        command = str(inp.get("command", ""))
        args = tuple(str(a) for a in inp.get("args", []))
        stdout, stderr, exit_code = _split_result_text(result_text)

        key = (command, args)
        call_counts[key] = call_counts.get(key, 0) + 1

        events.append(TraceEvent(
            command=command,
            args=args,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            attempt=call_counts[key],
            timed_out=exit_code == 124,
        ))

    if not events:
        # Fall back: treat the whole history as plain text for signal extraction
        text = json.dumps(messages)
        return TraceInput(
            events=(_make_text_event(text),),
            source_format="history",
        )

    return TraceInput(events=tuple(events), source_format="history")


def _parse_langfuse(span: dict) -> TraceInput:
    """Extract from a Langfuse span object."""
    inp = span.get("input") or {}
    out = span.get("output") or {}

    if isinstance(inp, str):
        inp = {"command": inp}
    if isinstance(out, str):
        out = {"stdout": out}

    command = str(inp.get("command", span.get("name", "")))
    stdout = str(out.get("stdout", out.get("result", "")))
    stderr = str(out.get("stderr", out.get("error", "")))
    status_message = str(span.get("statusMessage", ""))
    timed_out = status_message == "timeout" or out.get("exit_code") == 124

    level = span.get("level", "DEFAULT")
    exit_code = _langfuse_level_to_exit(level, out.get("exit_code"))

    event = TraceEvent(
        command=command,
        args=tuple(str(a) for a in inp.get("args", [])),
        stdout=stdout,
        stderr=stderr or status_message,
        exit_code=exit_code,
        timed_out=timed_out,
    )
    return TraceInput(events=(event,), source_format="langfuse")


def _parse_langsmith(run: dict) -> TraceInput:
    """Extract from a LangSmith run object."""
    inputs = run.get("inputs") or {}
    outputs = run.get("outputs") or {}
    error = run.get("error") or ""

    command = str(inputs.get("command", inputs.get("tool_name", "")))
    stdout = str(outputs.get("stdout", outputs.get("output", "")))
    stderr = str(outputs.get("stderr", error))
    exit_code = int(outputs.get("exit_code", 1 if error else 0))

    event = TraceEvent(
        command=command,
        args=tuple(str(a) for a in inputs.get("args", [])),
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=exit_code == 124,
    )
    return TraceInput(events=(event,), source_format="langsmith")


def _parse_text(text: str) -> TraceInput:
    """Last resort: treat the whole string as combined stdout+stderr."""
    return TraceInput(
        events=(_make_text_event(text),),
        source_format="text",
    )


def _make_text_event(text: str) -> TraceEvent:
    return TraceEvent(
        command="",
        args=(),
        stdout=text,
        stderr="",
        exit_code=0,
    )


def _split_result_text(text: str) -> tuple[str, str, int]:
    """Parse 'exit_code=N\\nstdout=...\\nstderr=...' from run.py tool results."""
    exit_code = 0
    stdout = ""
    stderr = ""
    # Try structured parse first
    ec_match = re.search(r"exit_code=(-?\d+)", text)
    if ec_match:
        exit_code = int(ec_match.group(1))
    stdout_match = re.search(r"stdout=(.*?)(?:\nstderr=|$)", text, re.DOTALL)
    if stdout_match:
        stdout = stdout_match.group(1).strip()
    stderr_match = re.search(r"stderr=(.*?)$", text, re.DOTALL)
    if stderr_match:
        stderr = stderr_match.group(1).strip()
    # If no structured parse, treat whole text as stdout
    if not stdout and not stderr:
        stdout = text
    return stdout, stderr, exit_code


def _langfuse_level_to_exit(level: str, explicit: object) -> int:
    if explicit is not None:
        return int(explicit)
    return {"DEFAULT": 0, "DEBUG": 0, "WARNING": 1, "ERROR": 1}.get(level, 0)


# ---------------------------------------------------------------------------
# Stage 2: extract_failures
# ---------------------------------------------------------------------------

def extract_failures(trace: TraceInput) -> tuple[TraceEvent, ...]:
    """
    Return only the events that are relevant for failure classification:
      - exit_code != 0
      - timed_out
      - part of a retry loop (attempt > 1, regardless of exit code)
      - has non-empty stderr

    If no failures are found, return all events (allows trace_insufficient detection).
    """
    failures = [
        e for e in trace.events
        if e.exit_code != 0 or e.timed_out or e.attempt > 1 or e.stderr.strip()
    ]
    return tuple(failures) if failures else trace.events


# ---------------------------------------------------------------------------
# Stage 3: deterministic signal matching
# ---------------------------------------------------------------------------

# ANSI escape code pattern
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB012]")

# Interactive prompt indicators (stdout or stderr)
_INTERACTIVE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\[y/n\]",
        r"\[Y/n\]",
        r"\(yes/no\)",
        r"Are you sure",
        r"Press any key",
        r"Password:",
        r"Enter passphrase",
        r"Confirm:",
        r"\[enter to continue\]",
        r"continue\?",
        r"proceed\?",
    ]
]

# TTY-requirement errors — explicit error messages when a command requires an interactive terminal
_TTY_REQUIREMENT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"requires?\s+a\s+tty",
        r"not\s+a\s+tty",
        r"no\s+tty\s+present",
        r"input\s+device\s+is\s+not\s+a\s+tty",
        r"stdin\s+is\s+not\s+a\s+terminal",
        r"must\s+be\s+connected\s+to\s+a\s+terminal",
        r"terminal\s+required",
        r"tty\s+required",
        r"inappropriate\s+ioctl\s+for\s+device",
        r"device\s+or\s+resource\s+busy.*tty",
    ]
]

# Pager indicators (stdout)
_PAGER_PATTERNS = [
    re.compile(p) for p in [
        r"\(END\)",
        r"^:$",             # less prompt
        r"^More$",
    ]
]

# Runtime version mismatch signals (stderr or stdout)
_VERSION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"SyntaxError:.*module",
        r"RUNTIME_VERSION",
        r"requires\s+(?:python|node|ruby|go)\s+\d",
        r"incompatible.*version",
        r"version.*incompatible",
        r"requires\s+version",
        r"minimum.*version",
    ]
]

# Command tree discovery failure signals
_DISCOVERY_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"unknown (sub)?command",
        r"invalid (sub)?command",
        r"unknown flag",
        r"did you mean",
        r"unrecognized arguments",
        r"command not found",
    ]
]

# Credential / auth expiry signals
_CREDENTIAL_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"token expired",
        r"credentials? expired",
        r"auth(?:entication)? failed",
        r"unauthorized",
        r"401",
        r"403.*forbidden",
        r"re-?auth(?:enticate)?",
        r"login required",
    ]
]

# Retry loop: no retryable field in JSON output
_RETRYABLE_RE = re.compile(r'"retryable"\s*:', re.IGNORECASE)


@dataclass
class _RawSignal:
    failure_mode_id: int
    confidence: float
    evidence: str


def match_signals(events: tuple[TraceEvent, ...]) -> tuple[_RawSignal, ...]:
    """
    Deterministic signal matching. Returns candidates sorted by confidence desc.
    Each matched §N appears at most once (highest confidence wins across events).
    """
    best: dict[int, _RawSignal] = {}

    def _keep(sig: _RawSignal) -> None:
        existing = best.get(sig.failure_mode_id)
        if existing is None or sig.confidence > existing.confidence:
            best[sig.failure_mode_id] = sig

    # Check each event individually
    for event in events:
        combined = (event.stdout + "\n" + event.stderr).strip()
        stdout = event.stdout
        stderr = event.stderr

        # §10 — Interactivity / TTY (timeout + interactive prompt)
        if event.timed_out or event.exit_code == 124:
            has_prompt = any(p.search(combined) for p in _INTERACTIVE_PATTERNS)
            has_pager = any(p.search(stdout) for p in _PAGER_PATTERNS)
            if has_prompt or has_pager:
                _keep(_RawSignal(10, 0.95, "timeout + interactive prompt or pager indicator detected"))
            else:
                # §11 — Timeouts (timeout without clear interactive prompt)
                _keep(_RawSignal(11, 0.85, f"exit_code=124 (timeout) with no interactive prompt"))

        if not event.timed_out:
            for pat in _INTERACTIVE_PATTERNS:
                if pat.search(combined):
                    _keep(_RawSignal(10, 0.90, f"interactive prompt pattern in output: {pat.pattern!r}"))
                    break

        # §10 — TTY-requirement errors (explicit "requires a TTY"-style messages in stderr or stdout)
        for pat in _TTY_REQUIREMENT_PATTERNS:
            if pat.search(combined):
                _keep(_RawSignal(10, 0.95, f"TTY-requirement error: {pat.pattern!r}"))
                break

        # §43 — Output unboundedness (large stdout)
        if len(stdout) > 50_000:
            conf = min(0.95, 0.75 + (len(stdout) - 50_000) / 200_000)
            _keep(_RawSignal(43, conf, f"stdout size {len(stdout):,} chars exceeds 50 KB"))

        # §68 — Stdout pollution: ANSI codes in stdout
        if _ANSI_RE.search(stdout):
            _keep(_RawSignal(68, 0.90, "ANSI escape sequences detected in stdout"))
        # ANSI in stderr only is a lower-confidence §68 signal
        elif _ANSI_RE.search(stderr):
            _keep(_RawSignal(68, 0.65, "ANSI escape sequences detected in stderr"))

        # §38 — Runtime version mismatch
        for pat in _VERSION_PATTERNS:
            if pat.search(combined):
                _keep(_RawSignal(38, 0.85, f"runtime version mismatch pattern: {pat.pattern!r}"))
                break

        # §52 — Command tree discovery failure
        for pat in _DISCOVERY_PATTERNS:
            if pat.search(combined):
                _keep(_RawSignal(52, 0.85, f"command discovery failure: {pat.pattern!r}"))
                break

        # §53 — Credential / auth expiry
        for pat in _CREDENTIAL_PATTERNS:
            if pat.search(combined):
                _keep(_RawSignal(53, 0.85, f"credential/auth signal: {pat.pattern!r}"))
                break

        # §56 — Pipeline exit masking: exit 0 but error-like stderr
        if event.exit_code == 0 and stderr.strip():
            error_words = ("error", "fail", "exception", "traceback", "panic", "fatal")
            if any(w in stderr.lower() for w in error_words):
                _keep(_RawSignal(56, 0.75, "exit_code=0 but stderr contains error-like content"))

    # Cross-event signals (require full event list)
    _keep_retry_signal(events, best)
    _keep_discovery_loop_signal(events, best)

    return tuple(sorted(best.values(), key=lambda s: s.confidence, reverse=True))


def _keep_retry_signal(
    events: tuple[TraceEvent, ...],
    best: dict[int, _RawSignal],
) -> None:
    """§19 — Retry hints: detect stuck retry loops with no retryable field."""
    # Group events by (command, args)
    groups: dict[tuple[str, tuple[str, ...]], list[TraceEvent]] = {}
    for e in events:
        key = (e.command, e.args)
        groups.setdefault(key, []).append(e)

    for key, group in groups.items():
        if len(group) < 2:
            continue
        all_failed = all(e.exit_code != 0 for e in group)
        if not all_failed:
            continue
        # Check if any output contained a retryable hint
        any_retryable = any(_RETRYABLE_RE.search(e.stdout) for e in group)
        if any_retryable:
            continue
        cmd_str = f"{key[0]} {' '.join(key[1])}"
        sig = _RawSignal(
            19,
            0.90,
            f"{cmd_str!r} called {len(group)}× all returning exit_code≠0 with no "
            f'"retryable" field — agent is looping without retry guidance',
        )
        existing = best.get(19)
        if existing is None or sig.confidence > existing.confidence:
            best[19] = sig


def _keep_discovery_loop_signal(
    events: tuple[TraceEvent, ...],
    best: dict[int, _RawSignal],
) -> None:
    """§52 — Command tree: boost confidence if agent called --help multiple times."""
    help_calls = [e for e in events if "--help" in e.args or "-h" in e.args]
    if len(help_calls) >= 2:
        sig = _RawSignal(
            52,
            0.92,
            f"agent called --help {len(help_calls)}× — schema not available in one call",
        )
        existing = best.get(52)
        if existing is None or sig.confidence > existing.confidence:
            best[52] = sig


# ---------------------------------------------------------------------------
# Challenge file reader
# ---------------------------------------------------------------------------

@dataclass
class _ChallengeContent:
    failure_mode_id: int
    title: str
    severity: str
    problem_text: str
    workaround_text: str
    limitation: str
    memory: str         # derived: one-sentence fact for agent memory
    skill_patch: str    # derived: reusable rule for system prompt / skill file
    spec_link: str


def _load_challenge(failure_mode_id: int, challenges_dir: Path) -> _ChallengeContent:
    """Find and parse the challenge file for a given §N code."""
    pattern = f"{failure_mode_id}-*.md"
    matches = list(challenges_dir.rglob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"no challenge file found for §{failure_mode_id} in {challenges_dir}"
        )
    path = matches[0]

    text = path.read_text(encoding="utf-8")

    # Title: "## N. Title Text"
    title_match = re.search(rf"^## {failure_mode_id}\.\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"§{failure_mode_id}"

    # Severity from the bold line after title
    severity_match = re.search(r"\*\*Severity:\*\*\s*(\w+)", text)
    severity = (severity_match.group(1).lower() if severity_match else "unknown")

    # ### The Problem section
    problem_match = re.search(
        r"### The Problem\n(.*?)(?=\n###|\Z)", text, re.DOTALL
    )
    problem_text = problem_match.group(1).strip() if problem_match else ""

    # ### Agent Workaround section
    workaround_match = re.search(
        r"### Agent Workaround\n(.*?)(?=\n###|\Z)", text, re.DOTALL
    )
    workaround_text = workaround_match.group(1).strip() if workaround_match else ""

    # **Limitation:** line
    limitation_match = re.search(r"\*\*Limitation:\*\*\s*(.+)", workaround_text)
    limitation = limitation_match.group(1).strip() if limitation_match else ""

    spec_link = str(path.relative_to(challenges_dir.parent))

    # Derive memory: first non-empty sentence from The Problem (≤120 chars)
    memory = _derive_memory(failure_mode_id, title, problem_text)

    # Derive skill_patch: first actionable line from Agent Workaround (≤120 chars)
    skill_patch = _derive_skill_patch(workaround_text)

    return _ChallengeContent(
        failure_mode_id=failure_mode_id,
        title=title,
        severity=severity,
        problem_text=problem_text[:2000],   # cap to stay within prompt budget
        workaround_text=workaround_text,
        limitation=limitation,
        memory=memory,
        skill_patch=skill_patch,
        spec_link=spec_link,
    )


def _derive_memory(failure_mode_id: int, title: str, problem_text: str) -> str:
    """One-sentence fact for agent memory: what to remember about §N."""
    # First prose sentence from The Problem, stripped of code blocks
    clean = re.sub(r"```.*?```", "", problem_text, flags=re.DOTALL)
    clean = re.sub(r"`[^`]+`", "", clean)
    for sentence in re.split(r"(?<=[.!?])\s+", clean):
        sentence = sentence.strip()
        if len(sentence) > 20:
            return sentence[:120]
    return f"§{failure_mode_id} ({title}): see spec for details"


def _derive_skill_patch(workaround_text: str) -> str:
    """Reusable rule for system prompt: first bold instruction from Agent Workaround."""
    _skip = re.compile(r"limitation|note:|warning:", re.IGNORECASE)
    for m in re.finditer(r"\*\*([^*]{10,200})\*\*", workaround_text):
        candidate = m.group(1).rstrip(":").strip()
        if not _skip.search(candidate):
            return candidate[:120]
    # Fall back to first prose line (not code, not list)
    for line in workaround_text.splitlines():
        line = line.strip()
        if line and not line.startswith(("```", "#", "-", "*", ">")) and not _skip.search(line):
            return line[:120]
    return ""


# ---------------------------------------------------------------------------
# Stage 4: LLM classification (one call per candidate)
# ---------------------------------------------------------------------------

def classify_with_llm(
    event: TraceEvent,
    candidates: tuple[_RawSignal, ...],
    client: _anthropic.Anthropic,
    challenges_dir: Path,
) -> tuple[SignalMatch, ...]:
    """
    For each candidate §N, issue one focused LLM call.
    Returns SignalMatch objects with updated confidence from LLM.
    Only sends candidates below CONFIDENCE_DETERMINISTIC_HIGH and above
    CONFIDENCE_LLM_THRESHOLD.
    """
    results: list[SignalMatch] = []

    for raw_sig in candidates:
        source = "deterministic"
        confidence = raw_sig.confidence

        if confidence < CONFIDENCE_LLM_THRESHOLD:
            continue

        try:
            challenge = _load_challenge(raw_sig.failure_mode_id, challenges_dir)
        except FileNotFoundError:
            challenge = None

        workaround = challenge.workaround_text if challenge else ""
        limitation = challenge.limitation if challenge else ""
        spec_link = challenge.spec_link if challenge else ""
        title = challenge.title if challenge else f"§{raw_sig.failure_mode_id}"
        severity = challenge.severity if challenge else "unknown"

        if confidence < CONFIDENCE_DETERMINISTIC_HIGH and challenge is not None:
            llm_confidence, llm_evidence = _llm_score(event, challenge, client)
            if llm_confidence > confidence:
                confidence = llm_confidence
            source = "llm"
        else:
            llm_evidence = raw_sig.evidence

        if confidence >= CONFIDENCE_LLM_THRESHOLD:
            results.append(SignalMatch(
                failure_mode_id=raw_sig.failure_mode_id,
                title=title,
                confidence=round(confidence, 3),
                evidence=llm_evidence if source == "llm" else raw_sig.evidence,
                workaround=workaround,
                memory=challenge.memory if challenge else "",
                skill_patch=challenge.skill_patch if challenge else "",
                severity=severity,
                spec_link=spec_link,
                limitation=limitation,
                source=source,
            ))

    return tuple(sorted(results, key=lambda m: m.confidence, reverse=True))


def _llm_score(
    event: TraceEvent,
    challenge: _ChallengeContent,
    client: _anthropic.Anthropic,
) -> tuple[float, str]:
    """Single focused LLM call: does this trace exhibit §N?"""
    # Truncate large outputs before sending
    stdout = event.stdout[:4000] + (" [truncated]" if len(event.stdout) > 4000 else "")
    stderr = event.stderr[:2000] + (" [truncated]" if len(event.stderr) > 2000 else "")

    prompt = (
        f"TRACE:\n"
        f"command: {event.command} {' '.join(event.args)}\n"
        f"exit_code: {event.exit_code}\n"
        f"stdout: {stdout!r}\n"
        f"stderr: {stderr!r}\n"
        f"\nFAILURE MODE §{challenge.failure_mode_id} — {challenge.title}:\n"
        f"{challenge.problem_text}\n"
        f"\nDoes this trace exhibit the §{challenge.failure_mode_id} failure mode above?\n"
        f'Respond with JSON only (no prose): '
        f'{{"matches": true/false, "confidence": 0.0-1.0, "evidence": "one sentence"}}'
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text = block.text.strip()
            break

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    parsed = json.loads(text)   # intentionally strict: let JSONDecodeError propagate
    confidence = float(parsed["confidence"]) if parsed.get("matches") else 0.0
    evidence = str(parsed.get("evidence", ""))
    return confidence, evidence


# ---------------------------------------------------------------------------
# Suffix: build SignalMatch for high-confidence deterministic hits
# ---------------------------------------------------------------------------

def _deterministic_match(
    raw_sig: _RawSignal,
    challenges_dir: Path,
) -> SignalMatch:
    """Build a SignalMatch for a high-confidence deterministic hit without LLM."""
    try:
        challenge = _load_challenge(raw_sig.failure_mode_id, challenges_dir)
        return SignalMatch(
            failure_mode_id=raw_sig.failure_mode_id,
            title=challenge.title,
            confidence=round(raw_sig.confidence, 3),
            evidence=raw_sig.evidence,
            workaround=challenge.workaround_text,
            memory=challenge.memory,
            skill_patch=challenge.skill_patch,
            severity=challenge.severity,
            spec_link=challenge.spec_link,
            limitation=challenge.limitation,
            source="deterministic",
        )
    except FileNotFoundError:
        return SignalMatch(
            failure_mode_id=raw_sig.failure_mode_id,
            title=f"§{raw_sig.failure_mode_id}",
            confidence=round(raw_sig.confidence, 3),
            evidence=raw_sig.evidence,
            workaround="",
            memory="",
            skill_patch="",
            severity="unknown",
            spec_link="",
            limitation="",
            source="deterministic",
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

_INSUFFICIENT_HINTS = (
    "Add stderr output — it often contains the actionable error message",
    "Include the full command with all arguments",
    "If the process timed out, note exit_code=124",
    "For retry loops, provide the full message history not just one event",
)


def diagnose(
    raw: str | dict | list,
    *,
    client: _anthropic.Anthropic | None = None,
    challenges_dir: Path = CHALLENGES_DIR,
) -> DiagnoseResult:
    """
    Full pipeline: parse → extract failures → match signals → (optionally) LLM classify.

    client=None skips the LLM stage (deterministic only).
    """
    trace = parse_trace(raw)
    failures = extract_failures(trace)

    # Insufficient trace: single event with empty stdout + empty stderr + exit 0
    all_empty = all(
        not e.stdout.strip() and not e.stderr.strip() and e.exit_code == 0
        for e in failures
    )
    if all_empty:
        return DiagnoseResult(
            matches=(),
            no_match=False,
            trace_insufficient=True,
            suggested_context=_INSUFFICIENT_HINTS,
            trace_summary="trace contains no output or error signals",
        )

    raw_signals = match_signals(failures)

    if not raw_signals:
        return DiagnoseResult(
            matches=(),
            no_match=True,
            trace_insufficient=False,
            suggested_context=(),
            trace_summary=_summarize(failures),
        )

    # Split: high-confidence gets deterministic match directly; rest go to LLM
    high = tuple(s for s in raw_signals if s.confidence >= CONFIDENCE_DETERMINISTIC_HIGH)
    ambiguous = tuple(s for s in raw_signals if s.confidence < CONFIDENCE_DETERMINISTIC_HIGH)

    final: list[SignalMatch] = [_deterministic_match(s, challenges_dir) for s in high]

    if ambiguous and client is not None:
        representative = failures[0]   # use first failure event for LLM context
        llm_matches = classify_with_llm(representative, ambiguous, client, challenges_dir)
        final.extend(llm_matches)
    elif ambiguous:
        # No LLM: include ambiguous as deterministic matches with their current confidence
        final.extend(_deterministic_match(s, challenges_dir) for s in ambiguous)

    final.sort(key=lambda m: m.confidence, reverse=True)

    return DiagnoseResult(
        matches=tuple(final),
        no_match=False,
        trace_insufficient=False,
        suggested_context=(),
        trace_summary=_summarize(failures),
    )


def _summarize(events: tuple[TraceEvent, ...]) -> str:
    commands = {e.command for e in events if e.command}
    failures = [e for e in events if e.exit_code != 0]
    retries = [e for e in events if e.attempt > 1]
    parts = []
    if commands:
        parts.append(f"commands: {', '.join(sorted(commands))}")
    if failures:
        codes = sorted({e.exit_code for e in failures})
        parts.append(f"{len(failures)} failure(s) with exit codes {codes}")
    if retries:
        parts.append(f"{len(retries)} retry attempt(s)")
    return "; ".join(parts) if parts else "trace parsed"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _result_to_dict(result: DiagnoseResult) -> dict:
    return {
        "schema_version": result.schema_version,
        "matches": [
            {
                "failure_mode_id": m.failure_mode_id,
                "title": m.title,
                "confidence": m.confidence,
                "evidence": m.evidence,
                "workaround": m.workaround,
                "memory": m.memory,
                "skill_patch": m.skill_patch,
                "severity": m.severity,
                "spec_link": m.spec_link,
                "limitation": m.limitation,
                "source": m.source,
            }
            for m in result.matches
        ],
        "no_match": result.no_match,
        "trace_insufficient": result.trace_insufficient,
        "suggested_context": list(result.suggested_context),
        "trace_summary": result.trace_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify a failed agent tool call against the CLI Agent Spec failure taxonomy"
    )
    parser.add_argument(
        "trace",
        nargs="?",
        help="JSON trace string (single event dict, message history, or Langfuse/LangSmith span)",
    )
    parser.add_argument(
        "--history",
        metavar="FILE",
        help="Path to a JSON file containing a message history list",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM classification for ambiguous candidates (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--challenges-dir",
        default=str(CHALLENGES_DIR),
        help=f"Path to challenges/ directory (default: {CHALLENGES_DIR})",
    )
    args = parser.parse_args()

    challenges_dir = Path(args.challenges_dir)

    if args.history:
        raw: str | dict | list = json.loads(Path(args.history).read_text())
    elif args.trace:
        raw = args.trace
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            parser.error("provide a trace argument, --history FILE, or pipe via stdin")

    client = None
    if args.llm:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)

    result = diagnose(raw, client=client, challenges_dir=challenges_dir)
    print(json.dumps(_result_to_dict(result), indent=2))

    if result.trace_insufficient:
        sys.exit(2)
    elif result.no_match:
        sys.exit(3)


if __name__ == "__main__":
    main()
