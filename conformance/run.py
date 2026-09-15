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
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
class Profile:
    tool: str
    command: tuple[str, ...]
    timeout_seconds: float
    manifest: tuple[str, ...] | None
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
        probes = tuple(
            Probe(p["name"], tuple(p["argv"]), ProbeKind(p["kind"]), p.get("dry_run_flag"))
            for p in raw["probes"]
        )
        names = [p.name for p in probes]
        if len(names) != len(set(names)):
            raise ProfileError("probe names must be unique")
        for probe in probes:
            if probe.kind is ProbeKind.DESTRUCTIVE and probe.dry_run_flag is None:
                raise ProfileError(f"destructive probe {probe.name!r} must declare dry_run_flag")
        manifest = tuple(raw["manifest"]) if "manifest" in raw else None
        return cls(raw["tool"], command, float(raw["timeout_seconds"]), manifest, probes)


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


class Validators:
    def __init__(self) -> None:
        schemas = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in SCHEMAS.glob("*.json")}
        registry = Registry().with_resources(
            (name, Resource.from_contents(schema, default_specification=DRAFT7)) for name, schema in schemas.items()
        )
        self.envelope = Draft7Validator(schemas["response-envelope.json"], registry=registry)
        self.manifest = Draft7Validator(schemas["manifest-response.json"], registry=registry)


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

    def execute_all(self, only: frozenset[str] | None) -> list[dict[str, object]]:
        for probe in self.profile.probes:
            self.check_probe(probe)
        self.check_help()
        self.check_manifest()
        if not any(p.kind is ProbeKind.INVALID for p in self.profile.probes):
            self.outcomes["invalid_input_exit_2"].skipped_reason = "profile declares no invalid probe"
        if not any(p.kind is ProbeKind.DESTRUCTIVE for p in self.profile.probes):
            for check in ("dry_run_preview", "destructive_refuses_unconfirmed"):
                self.outcomes[check].skipped_reason = "profile declares no destructive probe"
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
