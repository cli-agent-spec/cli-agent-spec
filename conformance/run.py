"""Deterministic conformance checks for a CLI against the mechanically verifiable CLI Agent Spec contracts.

The kit runs the probes a profile declares, never an LLM. Each check maps to failure modes (§N),
requirements (REQ-*), and the conformance level that first requires them (requirements/levels.md).

Usage:
  uv run conformance/run.py PROFILE [--only CHECK ...]

Output: one ResponseEnvelope on stdout whose data is a ConformanceResult (schemas/conformance-result.json).

Exit codes:
  0  every check that ran passed
  2  the profile is missing, unparseable, or invalid (no probe ran)
  4  at least one check failed; data carries the full result

Probes run the real command. Point profiles at a sandbox: destructive probes are invoked without
confirmation (expecting refusal) and with their dry-run flag (expecting a side-effect-free preview).
Stream probes read stdout line by line until the process exits or their deadline passes, and may
interrupt the stream with SIGINT after a set number of lines (POSIX only).
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
RESULT_SCHEMA_VERSION = "1.0"

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
ALLOWED_EXIT_CODES = frozenset(range(0, 14)) | frozenset(range(79, 126)) | {130, 143}


class ProbeKind(StrEnum):
    READ = "read"
    DESTRUCTIVE = "destructive"
    INVALID = "invalid"
    STREAM = "stream"


class Status(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class ProfileError(Exception):
    """The profile cannot be used to run probes."""


@dataclass(frozen=True)
class Probe:
    name: str
    argv: tuple[str, ...]
    kind: ProbeKind
    dry_run_flag: str | None
    deadline_seconds: float | None = None
    sigint_after_lines: int | None = None


def resolve_executable(name: str, base: Path) -> str:
    """Paths containing a slash resolve against the profile directory; bare names resolve through PATH."""
    if "/" in name:
        candidate = Path(name) if Path(name).is_absolute() else (base / name).resolve()
        if not candidate.is_file():
            raise ProfileError(f"profile command does not exist: {candidate}")
        return str(candidate)
    found = shutil.which(name)
    if found is None:
        raise ProfileError(f"profile command {name!r} is not on PATH")
    return found


@dataclass(frozen=True)
class ArgumentOrder:
    command_path: tuple[str, ...]
    local_args: tuple[str, ...]
    global_flag: str
    value: str
    alternate_value: str
    positional: str | None


STREAM_ONLY_FIELDS = ("deadline_seconds", "signal", "after_lines")


def load_probe(raw: dict[str, object]) -> Probe:
    """Build a probe, enforcing the cross-field rules the schema also states."""
    name, kind = str(raw["name"]), ProbeKind(str(raw["kind"]))
    if kind is ProbeKind.DESTRUCTIVE and "dry_run_flag" not in raw:
        raise ProfileError(f"destructive probe {name!r} must declare dry_run_flag")
    if kind is ProbeKind.STREAM:
        if "dry_run_flag" in raw:
            raise ProfileError(f"stream probe {name!r} must not declare dry_run_flag")
        if ("signal" in raw) != ("after_lines" in raw):
            raise ProfileError(f"stream probe {name!r} must declare signal and after_lines together")
    else:
        present = [f for f in STREAM_ONLY_FIELDS if f in raw]
        if present:
            raise ProfileError(f"{', '.join(present)} apply only to stream probes, not {kind.value} probe {name!r}")
    argv = raw["argv"]
    if not isinstance(argv, list):
        raise ProfileError(f"probe {name!r} argv must be an array")
    deadline = raw.get("deadline_seconds")
    after = raw.get("after_lines")
    dry_run_flag = raw.get("dry_run_flag")
    return Probe(
        name, tuple(str(a) for a in argv), kind,
        str(dry_run_flag) if dry_run_flag is not None else None,
        float(deadline) if isinstance(deadline, int | float) else None,
        after if isinstance(after, int) else None,
    )


@dataclass(frozen=True)
class Profile:
    tool: str
    command: tuple[str, ...]
    timeout_seconds: float
    manifest: tuple[str, ...] | None
    argument_order: ArgumentOrder | None
    probes: tuple[Probe, ...]

    @classmethod
    def load(cls, path: Path) -> Profile:
        if not path.is_file():
            raise ProfileError(f"profile not found: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ProfileError(f"profile is not valid JSON: {error}") from error
        schema = json.loads((SCHEMAS / "conformance-profile.json").read_text(encoding="utf-8"))
        errors = sorted(Draft7Validator(schema).iter_errors(raw), key=lambda e: list(e.absolute_path))
        if errors:
            details = "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors)
            raise ProfileError(f"profile does not match conformance-profile.json: {details}")
        command = (resolve_executable(raw["command"][0], path.parent), *raw["command"][1:])
        probes = tuple(load_probe(p) for p in raw["probes"])
        names = [p.name for p in probes]
        if len(names) != len(set(names)):
            raise ProfileError("probe names must be unique")
        manifest = tuple(raw["manifest"]) if "manifest" in raw else None
        argument_order = None
        if "argument_order" in raw:
            order = raw["argument_order"]
            if order["value"] == order["alternate_value"]:
                raise ProfileError("argument_order.alternate_value must differ from value")
            argument_order = ArgumentOrder(
                tuple(order["command_path"]), tuple(order["local_args"]),
                order["global_flag"], order["value"], order["alternate_value"], order.get("positional"),
            )
        return cls(raw["tool"], command, float(raw["timeout_seconds"]), manifest, argument_order, probes)


# ---------------------------------------------------------------------------
# Running probes
# ---------------------------------------------------------------------------


class StdinMode(StrEnum):
    CLOSED = "closed"   # /dev/null
    OPEN = "open"       # a pipe that is never written to or closed


@dataclass(frozen=True)
class Run:
    label: str
    argv: tuple[str, ...]
    stdin: StdinMode
    exit_code: int | None
    timed_out: bool
    duration_ms: int
    stdout: str
    stderr: str

    def evidence(self, detail: str) -> dict[str, object]:
        return {
            "probe": self.label,
            "argv": list(self.argv),
            "stdin": self.stdin.value,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_ms": self.duration_ms,
            "detail": detail,
        }


def execute(label: str, argv: tuple[str, ...], stdin: StdinMode, timeout: float, extra_env: dict[str, str]) -> Run:
    env = {**os.environ, **extra_env}
    for tty_hint in ("FORCE_COLOR", "CLICOLOR_FORCE"):
        env.pop(tty_hint, None)
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL if stdin is StdinMode.CLOSED else subprocess.PIPE,
            stdout=out,
            stderr=err,
            env=env,
            start_new_session=True,
        )
        timed_out = False
        try:
            exit_code: int | None = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
            exit_code = None
        finally:
            if process.stdin is not None:
                process.stdin.close()
        duration_ms = int((time.monotonic() - started) * 1000)
        out.seek(0)
        err.seek(0)
        return Run(
            label, argv, stdin, exit_code, timed_out, duration_ms,
            out.read().decode("utf-8", errors="replace"),
            err.read().decode("utf-8", errors="replace"),
        )


@dataclass(frozen=True)
class StreamRun:
    run: Run
    lines: tuple[str, ...]
    signalled_after: int | None   # stdout lines read when SIGINT was sent; None when it never was


def kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Kill the probe and every process in its session, so no grandchild keeps the stdout pipe open."""
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # the whole group already exited between poll() and killpg()
    else:
        process.kill()


def execute_stream(label: str, argv: tuple[str, ...], deadline: float, sigint_after: int | None) -> StreamRun:
    """Read stdout line by line until EOF and exit, or kill the process tree when the deadline passes.

    A thread reads the pipe so the deadline holds even when the command blocks without writing;
    stderr goes to a file, so a chatty command cannot fill a pipe and stall.
    """
    env = dict(os.environ)
    for tty_hint in ("FORCE_COLOR", "CLICOLOR_FORCE"):
        env.pop(tty_hint, None)
    with tempfile.TemporaryFile() as err:
        started = time.monotonic()
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err, env=env, start_new_session=True,
        )
        stdout = process.stdout
        if stdout is None:
            raise RuntimeError("stream probe started without a stdout pipe")
        lines_read: queue.Queue[bytes | None] = queue.Queue()

        def pump() -> None:
            for raw in stdout:
                lines_read.put(raw)
            lines_read.put(None)

        reader = threading.Thread(target=pump, name=f"stream:{label}", daemon=True)
        reader.start()
        lines: list[str] = []
        signalled_after: int | None = None
        timed_out = False
        exit_code: int | None = None
        try:
            while True:
                remaining = started + deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                try:
                    raw = lines_read.get(timeout=remaining)
                except queue.Empty:
                    timed_out = True
                    break
                if raw is None:
                    break
                lines.append(raw.decode("utf-8", errors="replace").rstrip("\n"))
                if sigint_after is not None and signalled_after is None and len(lines) >= sigint_after:
                    process.send_signal(signal.SIGINT)
                    signalled_after = len(lines)
            if not timed_out:
                try:
                    exit_code = process.wait(timeout=max(started + deadline - time.monotonic(), 0.0))
                except subprocess.TimeoutExpired:
                    timed_out = True
        finally:
            # On a timeout stdout may still be open in a child that outlived the probe, so kill the
            # whole group even when the probe itself has exited; otherwise the reader never sees EOF
            if timed_out or process.poll() is None:
                kill_tree(process)
                process.wait()
            reader.join(timeout=5)
            stdout.close()
        duration_ms = int((time.monotonic() - started) * 1000)
        err.seek(0)
        run = Run(
            label, argv, StdinMode.CLOSED, exit_code, timed_out, duration_ms,
            "\n".join(lines), err.read().decode("utf-8", errors="replace"),
        )
        return StreamRun(run, tuple(lines), signalled_after)


@dataclass(frozen=True)
class StreamParse:
    terminal: dict[str, object] | None
    terminal_line: int | None
    terminal_valid: bool   # the terminal line is a summary line or a valid error envelope with ok: false
    problems: tuple[str, ...]


class Validators:
    def __init__(self) -> None:
        schemas = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in SCHEMAS.glob("*.json")}
        registry = Registry().with_resources(
            (name, Resource.from_contents(schema, default_specification=DRAFT7)) for name, schema in schemas.items()
        )
        # date-time needs rfc3339-validator; without it every timestamp would pass unchecked
        checker = Draft7Validator.FORMAT_CHECKER
        if "date-time" not in checker.checkers:
            raise SystemExit("format date-time is unchecked: install rfc3339-validator (uv sync)")
        self.envelope = Draft7Validator(schemas["response-envelope.json"], registry=registry, format_checker=checker)
        self.manifest = Draft7Validator(schemas["manifest-response.json"], registry=registry, format_checker=checker)


def parse_envelope(run: Run, validators: Validators) -> tuple[dict[str, object] | None, str | None]:
    """Return the envelope, or None with the reason stdout is not exactly one valid envelope."""
    text = run.stdout.strip()
    if not text:
        return None, "stdout is empty"
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        return None, f"stdout is not a single JSON document ({error.msg} at char {error.pos})"
    if not isinstance(document, dict):
        return None, "stdout JSON is not an object"
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in validators.envelope.iter_errors(document)]
    if errors:
        return None, "envelope invalid: " + "; ".join(errors[:3])
    return document, None


def parse_stream(lines: tuple[str, ...], validators: Validators) -> StreamParse:
    """Classify stream lines by REQ-O-004: items, then exactly one terminal line.

    The terminal line is the summary line ("_summary": true) or an error ResponseEnvelope, recognised
    by an "ok" boolean beside an "error" key. Heartbeat lines (REQ-O-038) are JSON objects like items.
    """
    problems: list[str] = []
    terminal: dict[str, object] | None = None
    terminal_line: int | None = None
    terminal_valid = False
    for number, line in enumerate(lines, start=1):
        if terminal_line is not None:
            problems.append(f"line {number} follows the terminal line {terminal_line}; a stream ends with exactly one terminal line")
            break
        if not line.strip():
            problems.append(f"line {number} is blank; every stream line is one JSON object")
            continue
        try:
            document = json.loads(line)
        except json.JSONDecodeError as error:
            problems.append(f"line {number} is not JSON ({error.msg} at char {error.pos})")
            continue
        if not isinstance(document, dict):
            problems.append(f"line {number} is JSON but not an object")
            continue
        if document.get("_summary") is True:
            terminal, terminal_line, terminal_valid = document, number, True
        elif isinstance(document.get("ok"), bool) and "error" in document:
            terminal, terminal_line = document, number
            errors = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in validators.envelope.iter_errors(document)]
            if errors:
                problems.append(f"line {number} is an error envelope that does not validate: " + "; ".join(errors[:3]))
            elif document["ok"] is not False:
                problems.append(f"line {number} has ok: true beside error; a stream's error line is an envelope with ok: false")
            else:
                terminal_valid = True
    return StreamParse(terminal, terminal_line, terminal_valid, tuple(problems))


def envelope_meta(document: dict[str, object]) -> dict[str, object]:
    meta = document.get("meta")
    if not isinstance(meta, dict):
        raise RuntimeError("validated envelope has a non-object meta")
    return meta


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckSpec:
    id: str
    title: str
    level: int
    failure_modes: tuple[int, ...]
    requirements: tuple[str, ...]


@dataclass
class Outcome:
    spec: CheckSpec
    checked: int = 0
    failures: list[dict[str, object]] = field(default_factory=list)
    skipped_reason: str | None = None

    def fail(self, run: Run, detail: str) -> None:
        self.failures.append(run.evidence(detail))

    def to_json(self) -> dict[str, object]:
        status = Status.SKIP if self.skipped_reason else (Status.FAIL if self.failures else Status.PASS)
        result: dict[str, object] = {
            "id": self.spec.id,
            "title": self.spec.title,
            "status": status.value,
            "level": self.spec.level,
            "failure_modes": [f"§{n}" for n in self.spec.failure_modes],
            "requirements": list(self.spec.requirements),
            "runs_checked": self.checked,
            "failures": self.failures,
        }
        if self.skipped_reason:
            result["skipped_reason"] = self.skipped_reason
        return result


CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec("no_hang_stdin_closed", "Completes with stdin closed", 1, (10, 11), ("REQ-F-009", "REQ-F-010")),
    CheckSpec("no_hang_stdin_open", "Completes with an open, silent stdin pipe", 1, (50, 10), ("REQ-F-009",)),
    CheckSpec("json_envelope", "Non-TTY stdout is exactly one valid ResponseEnvelope without flags", 1, (2, 3, 18), ("REQ-F-003", "REQ-F-004", "REQ-F-006", "REQ-C-013")),
    CheckSpec("exit_code_contract", "Exit codes come from the table and match meta.exit_code", 1, (1,), ("REQ-F-001",)),
    CheckSpec("stdout_no_ansi", "No ANSI escape sequences on stdout in a non-TTY", 1, (8,), ("REQ-F-007",)),
    CheckSpec("no_color_honored", "NO_COLOR=1 removes ANSI from stdout and stderr", 1, (8,), ("REQ-F-008",)),
    CheckSpec("help_off_stdout", "--help keeps stdout free of prose and exits 0", 1, (3,), ("REQ-F-048",)),
    CheckSpec("invalid_input_exit_2", "Invalid input exits 2 before side effects", 1, (14, 1), ("REQ-F-002",)),
    CheckSpec("dry_run_preview", "Destructive commands preview with their dry-run flag", 1, (23,), ("REQ-C-004",)),
    CheckSpec("destructive_refuses_unconfirmed", "Destructive commands refuse with exit 2, before side effects, without confirmation", 2, (23, 10), ("REQ-C-005", "REQ-O-021")),
    CheckSpec("manifest_valid", "tool manifest returns a valid ManifestResponse", 3, (52, 21), ("REQ-O-041",)),
    CheckSpec("argument_order", "A global option means the same before and after the command path; conflicting repeats exit 2", 3, (69,), ("REQ-F-067", "REQ-F-079")),
    CheckSpec("stream_contract", "Every stream line is a JSON object and the stream ends on exactly one terminal line that matches the exit code", 3, (5, 76), ("REQ-O-004",)),
    CheckSpec("stream_sigint", "SIGINT mid-stream ends the stream on a CANCELLED error envelope and exit 130, as REQ-F-069 defines", 3, (16,), ("REQ-O-004",)),
)


class Kit:
    def __init__(self, profile: Profile) -> None:
        self.profile = profile
        self.validators = Validators()
        self.outcomes = {spec.id: Outcome(spec) for spec in CHECKS}

    def run(self, label: str, argv: tuple[str, ...], stdin: StdinMode = StdinMode.CLOSED, env: dict[str, str] | None = None) -> Run:
        return execute(label, self.profile.command + argv, stdin, self.profile.timeout_seconds, env or {})

    def completed(self, outcome: Outcome, run: Run) -> bool:
        outcome.checked += 1
        if run.timed_out:
            outcome.fail(run, f"no exit within {self.profile.timeout_seconds:g}s; killed")
            return False
        return True

    def envelope_checks(self, run: Run) -> dict[str, object] | None:
        envelope_outcome = self.outcomes["json_envelope"]
        envelope_outcome.checked += 1
        envelope, reason = parse_envelope(run, self.validators)
        if envelope is None:
            envelope_outcome.fail(run, reason or "invalid envelope")
        exit_outcome = self.outcomes["exit_code_contract"]
        exit_outcome.checked += 1
        if run.exit_code is None:
            raise RuntimeError("envelope_checks requires a completed run")
        if run.exit_code not in ALLOWED_EXIT_CODES:
            exit_outcome.fail(run, f"exit code {run.exit_code} is outside 0–13, 79–125, and signal codes 130/143")
        elif envelope is not None:
            meta = envelope["meta"]
            if not isinstance(meta, dict):
                raise RuntimeError("validated envelope has a non-object meta")
            if meta["exit_code"] != run.exit_code:
                exit_outcome.fail(run, f"meta.exit_code is {meta['exit_code']} but the process exited {run.exit_code}")
        ansi_outcome = self.outcomes["stdout_no_ansi"]
        ansi_outcome.checked += 1
        if ANSI.search(run.stdout):
            ansi_outcome.fail(run, "stdout contains ANSI escape sequences")
        return envelope

    def check_probe(self, probe: Probe) -> None:
        closed = self.run(probe.name, probe.argv)
        if not self.completed(self.outcomes["no_hang_stdin_closed"], closed):
            return
        open_pipe = self.run(probe.name, probe.argv, StdinMode.OPEN)
        self.completed(self.outcomes["no_hang_stdin_open"], open_pipe)
        self.envelope_checks(closed)

        no_color = self.run(probe.name, probe.argv, env={"NO_COLOR": "1"})
        outcome = self.outcomes["no_color_honored"]
        if self.completed(outcome, no_color) and (ANSI.search(no_color.stdout) or ANSI.search(no_color.stderr)):
            outcome.fail(no_color, "ANSI escape sequences present with NO_COLOR=1")

        if probe.kind is ProbeKind.INVALID:
            outcome = self.outcomes["invalid_input_exit_2"]
            outcome.checked += 1
            if closed.exit_code != 2:
                outcome.fail(closed, f"expected exit 2 for invalid input, got {closed.exit_code}")

        if probe.kind is ProbeKind.DESTRUCTIVE:
            outcome = self.outcomes["destructive_refuses_unconfirmed"]
            outcome.checked += 1
            if closed.exit_code != 2:
                outcome.fail(closed, f"expected exit 2 (refused before side effects) without confirmation, got {closed.exit_code}")
            if probe.dry_run_flag is None:
                raise RuntimeError(f"destructive probe {probe.name!r} has no dry_run_flag")
            preview = self.run(f"{probe.name} {probe.dry_run_flag}", (*probe.argv, probe.dry_run_flag))
            outcome = self.outcomes["dry_run_preview"]
            if self.completed(outcome, preview):
                envelope = self.envelope_checks(preview)
                if preview.exit_code != 0:
                    outcome.fail(preview, f"dry-run exited {preview.exit_code}, expected 0")
                elif envelope is None:
                    outcome.fail(preview, "dry-run output is not a valid envelope")

    def check_help(self) -> None:
        outcome = self.outcomes["help_off_stdout"]
        run = self.run("--help", ("--help",))
        if not self.completed(outcome, run):
            return
        if run.exit_code != 0:
            outcome.fail(run, f"--help exited {run.exit_code}, expected 0")
        elif run.stdout.strip():
            envelope, _reason = parse_envelope(run, self.validators)
            if envelope is None:
                outcome.fail(run, "--help wrote prose to stdout in a non-TTY; route it to stderr")

    def check_manifest(self) -> None:
        outcome = self.outcomes["manifest_valid"]
        if self.profile.manifest is None:
            outcome.skipped_reason = "profile declares no manifest command"
            return
        run = self.run("manifest", self.profile.manifest)
        if not self.completed(outcome, run):
            return
        envelope, reason = parse_envelope(run, self.validators)
        if envelope is None:
            outcome.fail(run, reason or "invalid envelope")
            return
        errors = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in self.validators.manifest.iter_errors(envelope["data"])]
        if errors:
            outcome.fail(run, "data is not a valid ManifestResponse: " + "; ".join(errors[:3]))

    def check_argument_order(self) -> None:
        outcome = self.outcomes["argument_order"]
        order = self.profile.argument_order
        if order is None:
            outcome.skipped_reason = "profile declares no argument_order"
            return
        path, local, flag = order.command_path, order.local_args, order.global_flag

        def placements(value: str) -> dict[str, tuple[str, ...]]:
            return {
                "before the command path": (flag, value, *path, *local),
                "between path and local option": (*path, flag, value, *local),
                "after the local option": (*path, *local, flag, value),
            }

        runs: dict[tuple[str, str], Run] = {}
        for value in (order.value, order.alternate_value):
            for where, argv in placements(value).items():
                run = self.run(f"argument_order {flag} {value} {where}", argv)
                if not self.completed(outcome, run):
                    return
                if run.exit_code != 0:
                    outcome.fail(run, f"{flag} {value} {where} exited {run.exit_code}, expected 0")
                    return
                runs[(value, where)] = run

        reference, _reason = parse_envelope(runs[(order.value, "after the local option")], self.validators)
        for where in placements(order.value):
            run = runs[(order.value, where)]
            envelope, reason = parse_envelope(run, self.validators)
            if envelope is None:
                outcome.fail(run, f"{flag} {order.value} {where}: {reason}")
            elif reference is not None and envelope["data"] != reference["data"]:
                outcome.fail(run, f"data differs from the run with {flag} {order.value} after the local option")
            alternate = runs[(order.alternate_value, where)]
            if alternate.stdout == run.stdout:
                outcome.fail(alternate, f"{flag} {order.alternate_value} {where} printed the same stdout as {flag} {order.value}: the value was ignored or overwritten by a default")
            if alternate.stdout != runs[(order.alternate_value, "after the local option")].stdout:
                outcome.fail(alternate, f"stdout differs from the run with {flag} {order.alternate_value} after the local option")

        conflict = self.run(f"argument_order conflicting {flag}", (flag, order.value, *path, *local, flag, order.alternate_value))
        if self.completed(outcome, conflict) and conflict.exit_code != 2:
            outcome.fail(conflict, f"{flag} given twice with different values exited {conflict.exit_code}, expected 2")

        if order.positional is not None:
            self.check_option_after_positional(outcome, order)

    def check_option_after_positional(self, outcome: Outcome, order: ArgumentOrder) -> None:
        """A local option after a positional takes effect instead of being read as another positional."""
        path, local, positional = order.command_path, order.local_args, order.positional
        variants = {
            "local option after the positional": (*path, positional, *local),
            "local option before the positional": (*path, *local, positional),
            "positional without the local option": (*path, positional),
        }
        data: dict[str, object] = {}
        runs: dict[str, Run] = {}
        for where, argv in variants.items():
            run = self.run(f"argument_order {where}", argv)
            if not self.completed(outcome, run):
                return
            envelope, reason = parse_envelope(run, self.validators)
            if run.exit_code != 0 or envelope is None:
                outcome.fail(run, f"{where}: exit {run.exit_code}, {reason or 'envelope reports failure'}")
                return
            data[where] = envelope["data"]
            runs[where] = run
        after = runs["local option after the positional"]
        if data["local option after the positional"] != data["local option before the positional"]:
            outcome.fail(after, f"{' '.join(local)} after {positional!r} gives different data than before it")
        if data["local option after the positional"] == data["positional without the local option"]:
            outcome.fail(after, f"{' '.join(local)} after {positional!r} had no effect: read as a positional or ignored")

    def check_stream(self, probe: Probe) -> None:
        """Run a stream probe once, interrupting it when the probe declares a signal, and check REQ-O-004's line contract."""
        if probe.sigint_after_lines is not None and os.name != "posix":
            return  # stream_sigint is skipped as a whole in execute_all
        deadline = probe.deadline_seconds if probe.deadline_seconds is not None else self.profile.timeout_seconds
        label = probe.name if probe.sigint_after_lines is None else f"{probe.name} (SIGINT after {probe.sigint_after_lines} lines)"
        stream = execute_stream(label, self.profile.command + probe.argv, deadline, probe.sigint_after_lines)
        run = stream.run
        parsed = parse_stream(stream.lines, self.validators)

        contract = self.outcomes["stream_contract"]
        contract.checked += 1
        for problem in parsed.problems[:3]:
            contract.fail(run, problem)
        if len(parsed.problems) > 3:
            contract.fail(run, f"{len(parsed.problems) - 3} more stream lines break the contract")
        if run.timed_out:
            seen = "its terminal line" if parsed.terminal is not None else f"{len(stream.lines)} lines and no terminal line"
            contract.fail(run, f"still running at the {deadline:g}s deadline after {seen}; killed")
        elif parsed.terminal is None:
            contract.fail(run, f"stdout ended after {len(stream.lines)} lines without a terminal line (\"_summary\": true or an error envelope)")
        elif parsed.terminal.get("_summary") is True:
            if run.exit_code != 0:
                contract.fail(run, f"stream ended on its summary line but exited {run.exit_code}, expected 0")
        elif parsed.terminal_valid:
            declared = envelope_meta(parsed.terminal)["exit_code"]
            if declared != run.exit_code:
                contract.fail(run, f"terminal error envelope declares meta.exit_code {declared} but the process exited {run.exit_code}")

        if probe.sigint_after_lines is not None:
            self.check_sigint(probe.sigint_after_lines, stream, parsed, deadline)

    def check_sigint(self, after_lines: int, stream: StreamRun, parsed: StreamParse, deadline: float) -> None:
        outcome = self.outcomes["stream_sigint"]
        outcome.checked += 1
        run = stream.run
        if stream.signalled_after is None:
            if run.timed_out:
                outcome.fail(run, f"only {len(stream.lines)} of {after_lines} lines before the {deadline:g}s deadline; SIGINT never sent")
            else:
                outcome.fail(run, f"stream ended after {len(stream.lines)} lines, before after_lines {after_lines}; SIGINT never sent, lower after_lines")
            return
        if run.timed_out:
            outcome.fail(run, f"no exit within the {deadline:g}s deadline after SIGINT; killed")
            return
        if run.exit_code != 130:
            outcome.fail(run, f"exited {run.exit_code} after SIGINT, expected 130")
        terminal = parsed.terminal
        if terminal is None:
            outcome.fail(run, "no terminal line after SIGINT; expected an error envelope with error.code CANCELLED")
        elif terminal.get("_summary") is True:
            outcome.fail(run, "stream ended on its summary line after SIGINT; expected an error envelope with error.code CANCELLED")
        else:
            error = terminal.get("error")
            code = error.get("code") if isinstance(error, dict) else None
            if code != "CANCELLED":
                outcome.fail(run, f"terminal error envelope after SIGINT has error.code {code!r}, expected 'CANCELLED'")

    def execute_all(self, only: frozenset[str] | None) -> list[dict[str, object]]:
        for probe in self.profile.probes:
            if probe.kind is ProbeKind.STREAM:
                self.check_stream(probe)
            else:
                self.check_probe(probe)
        self.check_help()
        self.check_manifest()
        self.check_argument_order()
        if not any(p.kind is ProbeKind.INVALID for p in self.profile.probes):
            self.outcomes["invalid_input_exit_2"].skipped_reason = "profile declares no invalid probe"
        if not any(p.kind is ProbeKind.DESTRUCTIVE for p in self.profile.probes):
            for check in ("dry_run_preview", "destructive_refuses_unconfirmed"):
                self.outcomes[check].skipped_reason = "profile declares no destructive probe"
        streams = [p for p in self.profile.probes if p.kind is ProbeKind.STREAM]
        if not streams:
            self.outcomes["stream_contract"].skipped_reason = "profile declares no stream probe"
        if not any(p.sigint_after_lines is not None for p in streams):
            self.outcomes["stream_sigint"].skipped_reason = "profile declares no stream probe with signal"
        elif os.name != "posix":
            self.outcomes["stream_sigint"].skipped_reason = "SIGINT delivery to a probe needs POSIX signals"
        if os.name != "posix" and self.outcomes["stream_contract"].checked == 0 and streams:
            self.outcomes["stream_contract"].skipped_reason = "every stream probe declares a signal, which needs POSIX signals"
        return [o.to_json() for spec_id, o in self.outcomes.items() if only is None or spec_id in only]


def level_status(checks: list[dict[str, object]], level: int) -> str:
    relevant = [c for c in checks if isinstance(c["level"], int) and c["level"] <= level]
    if any(c["status"] == Status.FAIL for c in relevant):
        return "fail"
    if any(c["status"] == Status.SKIP for c in relevant):
        return "incomplete"
    return "pass"


def envelope(ok: bool, exit_code: int, data: dict[str, object] | None, error: dict[str, object] | None, started: float) -> str:
    return json.dumps({
        "ok": ok,
        "data": data,
        "error": error,
        "warnings": [],
        "meta": {"exit_code": exit_code, "duration_ms": int((time.monotonic() - started) * 1000), "schema_version": RESULT_SCHEMA_VERSION},
    }, indent=2, ensure_ascii=False)


def main(argv: list[str]) -> int:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("profile", type=Path, help="conformance profile JSON (schemas/conformance-profile.json)")
    parser.add_argument("--only", nargs="+", choices=[c.id for c in CHECKS], help="report only these checks")
    args = parser.parse_args(argv)

    try:
        profile = Profile.load(args.profile)
    except ProfileError as error:
        print(envelope(False, 2, None, {
            "code": "INVALID_PROFILE", "message": str(error), "retryable": False, "phase": "validation",
            "fix_required": "Correct the profile so it validates against schemas/conformance-profile.json",
        }, started))
        return 2

    checks = Kit(profile).execute_all(frozenset(args.only) if args.only else None)
    summary = {status.value: sum(1 for c in checks if c["status"] == status) for status in Status}
    result: dict[str, object] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "tool": profile.tool,
        "levels": {f"level_{n}": level_status(checks, n) for n in (1, 2, 3)},
        "summary": {"passed": summary["pass"], "failed": summary["fail"], "skipped": summary["skip"]},
        "checks": checks,
    }
    if summary["fail"]:
        print(envelope(False, 4, result, {
            "code": "CONFORMANCE_CHECKS_FAILED",
            "message": f"{summary['fail']} of {len(checks)} checks failed",
            "retryable": False,
            "fix_required": "Fix each failing check listed in data.checks; failures carry the probe argv and evidence",
        }, started))
        return 4
    print(envelope(True, 0, result, None, started))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
