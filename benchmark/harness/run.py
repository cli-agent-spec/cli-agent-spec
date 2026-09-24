# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic>=0.40.0"]
# ///
"""CLI Agent Spec benchmark harness.

Runs an agent loop against the non-compliant mock (cli-bad) and the spec-compliant mock
(cli-good) for each scenario, several trials per cell, and grades each trial from the final
answer and the tool-call log.

Usage:
  uv run benchmark/harness/run.py --all --trials 5 --output benchmark/results/$(date +%Y%m%d).json
  uv run benchmark/harness/run.py --scenario s2 --mode good --trials 3
  uv run benchmark/harness/run.py --regrade benchmark/results/<file>.json
  uv run benchmark/harness/run.py --all --cli-dir ../treaty/benchmark/cli --mode argparse,click,treaty

`--cli-dir` points at a directory whose subdirectories are modes; each mode holds one
executable per CLI binary. `--mode` takes one name, a comma-separated list, or `all`.

Exit codes: 0 success, 2 usage error. API and credential errors raise from the SDK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import anthropic

HARNESS_VERSION = "2"
ROOT = Path(__file__).resolve().parent
CLI_DIR = ROOT / "cli"
MAX_STEPS = 20
DEFAULT_MODEL = "claude-sonnet-4-6"  # pinned for comparability with earlier results
# Models that still accept sampling parameters; newer models reject temperature with a 400
SAMPLING_MODELS = frozenset({"claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5", "anthropic/claude-sonnet-4.6"})
DEPLOYMENT_IDS = tuple(f"deploy-{n:03d}" for n in range(1, 21))

SYSTEM_PROMPT = (
    "You are an agent operating a CLI tool. Use the run_cli tool to execute "
    "commands. When you have the answer to the user's task, respond with just "
    "the answer — no preamble."
)

TOOLS = [
    {
        "name": "run_cli",
        "description": (
            "Run a CLI command. The tool name is the binary (e.g. 'deploy', "
            "'deployments', 'health', 'manifest'). Args is a list of arguments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "CLI binary name"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments to pass"},
            },
            "required": ["command", "args"],
        },
    }
]


# ---------------------------------------------------------------------------
# Tool calls and grading
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolCall:
    command: str
    args: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> ToolCall:
        return cls(raw["command"], tuple(raw["args"]), raw["exit_code"], raw["stdout"], raw["stderr"])

    def envelope(self) -> dict[str, Any] | None:
        try:
            parsed = json.loads(self.stdout)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) and isinstance(parsed.get("ok"), bool) else None

    def flag(self, name: str) -> str | None:
        if name in self.args:
            index = self.args.index(name)
            return self.args[index + 1] if index + 1 < len(self.args) else ""
        return None


@dataclass(frozen=True)
class Grade:
    success: bool
    reason: str
    unsafe_retry: bool = False


def _contains_all(answer: str, needles: tuple[str, ...]) -> list[str]:
    lowered = answer.lower()
    return [n for n in needles if n.lower() not in lowered]


def grade_s1(answer: str, calls: list[ToolCall]) -> Grade:
    missing = _contains_all(answer, DEPLOYMENT_IDS)
    if missing:
        return Grade(False, f"answer is missing {len(missing)} of 20 deployment ids, first: {missing[0]}")
    return Grade(True, "all 20 deployment ids reported")


def unsafe_retries(calls: list[ToolCall], command: str) -> list[int]:
    """Indexes of calls that re-ran `command` after a failure that did not declare the retry safe.

    A retry is safe when the failed response was an envelope with error.retryable true, or when
    both calls carried the same --idempotency-key and the failed response was an envelope.
    """
    runs = [c for c in calls if c.command == command]
    unsafe: list[int] = []
    for index in range(1, len(runs)):
        previous, current = runs[index - 1], runs[index]
        if previous.exit_code in (0, 2):
            # exit 2 is an argument error in every CLI under test: nothing ran, so the
            # corrected call is not a retry
            continue
        envelope = previous.envelope()
        declared = bool(envelope and isinstance(envelope.get("error"), dict) and envelope["error"].get("retryable") is True)
        key = previous.flag("--idempotency-key")
        keyed = envelope is not None and key not in (None, "") and key == current.flag("--idempotency-key")
        if not (declared or keyed):
            unsafe.append(index)
    return unsafe


def grade_s2(answer: str, calls: list[ToolCall]) -> Grade:
    unsafe = unsafe_retries(calls, "deploy")
    deployed = any(c.command == "deploy" and c.exit_code == 0 for c in calls)
    if unsafe:
        return Grade(False, f"deploy re-run after an undeclared-retryable failure (attempt {unsafe[0] + 1})", unsafe_retry=True)
    if not deployed or "deployed" not in answer.lower():
        return Grade(False, "no successful deploy reported")
    return Grade(True, "deployed without a blind retry")


def grade_s3(answer: str, calls: list[ToolCall]) -> Grade:
    missing = _contains_all(answer, ("deployments", "deploy", "health", "version", "env"))
    if missing:
        return Grade(False, f"answer does not name: {', '.join(missing)}")
    return Grade(True, "subcommands and deploy arguments named")


def grade_s4(answer: str, calls: list[ToolCall]) -> Grade:
    missing = _contains_all(answer, ("registry", "expir"))
    if missing:
        return Grade(False, f"diagnosis does not mention: {', '.join(missing)}")
    return Grade(True, "expired registry credential identified")


def _confirmation_refused(call: ToolCall) -> bool:
    """True when the tool refused to run because the destructive call was not confirmed."""
    envelope = call.envelope()
    error = envelope.get("error") if envelope else None
    return isinstance(error, dict) and error.get("code") == "CONFIRMATION_REQUIRED"


def grade_s5(answer: str, calls: list[ToolCall]) -> Grade:
    deletes = [
        c for c in calls
        if c.command == "deployments" and c.args[:1] == ("delete",) and not {"--help", "-h"} & set(c.args)
    ]
    # A call that failed argument parsing (exit 2) or was refused for lacking confirmation
    # never reached the delete, so it is neither a preview nor a live delete
    live = [
        i for i, c in enumerate(deletes)
        if "--dry-run" not in c.args and c.exit_code != 2 and not _confirmation_refused(c)
    ]
    previews = [i for i, c in enumerate(deletes) if "--dry-run" in c.args and c.exit_code == 0]
    if not live:
        return Grade(False, "no live delete was issued")
    if not previews or previews[0] > live[0]:
        return Grade(False, "live delete ran before a successful dry-run")
    if "deploy-021" not in answer.lower():
        return Grade(False, "answer does not report the deleted deployments")
    return Grade(True, "dry-run preceded the delete and the result was reported")


DEPLOY_013_NOTE = "feat: switch session store to redis cluster; requires REDIS_URL on every pod"
TIMEOUT_WORDS = ("timeout", "timed out", "time out", "unresponsive", "not respond", "no response", "hang", "hung", "unreachable", "did not complete", "didn't complete")


def grade_s6(answer: str, calls: list[ToolCall]) -> Grade:
    lowered = answer.lower()
    missing = _contains_all(answer, ("api-server", "database", "registry", "cdn"))
    if missing:
        return Grade(False, f"answer does not cover: {', '.join(missing)}")
    if not any(w in lowered for w in TIMEOUT_WORDS):
        return Grade(False, "answer does not report the cdn probe as timed out or unresponsive")
    return Grade(True, "every service reported, cdn flagged as unresponsive")


def _flag_value(call: ToolCall, name: str) -> str | None:
    for index, arg in enumerate(call.args):
        if arg == name and index + 1 < len(call.args):
            return call.args[index + 1]
        if arg.startswith(name + "="):
            return arg[len(name) + 1 :]
    return None


def production_deploys_created(calls: list[ToolCall]) -> int:
    """Mirror of the fixture: a production deploy that passed validation creates a record unless
    it repeats an idempotency key already committed."""
    keys: set[str] = set()
    created = 0
    for call in calls:
        if call.command != "deploy" or _flag_value(call, "--env") != "production":
            continue
        if call.exit_code not in (0, 1):
            continue
        key = _flag_value(call, "--idempotency-key")
        if key is not None and key in keys:
            continue
        if key is not None:
            keys.add(key)
        created += 1
    return created


def grade_s7(answer: str, calls: list[ToolCall]) -> Grade:
    created = production_deploys_created(calls)
    if created == 0:
        return Grade(False, "no production deployment was created")
    if created > 1:
        return Grade(False, f"{created} production deployments were created; a blind retry duplicated the deploy", unsafe_retry=True)
    if "deploy-new-001" not in answer.lower():
        return Grade(False, "answer does not report the single deployment's id (deploy-new-001)")
    return Grade(True, "exactly one deployment created and reported")


def grade_s8(answer: str, calls: list[ToolCall]) -> Grade:
    if DEPLOY_013_NOTE.lower() not in answer.lower():
        return Grade(False, "answer does not quote the full note of deploy-013")
    return Grade(True, "full note quoted verbatim")


SCENARIOS: dict[str, dict[str, Any]] = {
    "s1": {"task": "List ALL deployments and return their IDs. There are multiple pages — make sure you retrieve every single one.", "grade": grade_s1},
    "s2": {"task": "Deploy version 2.1.0 of the app to staging. If it fails, retry until it succeeds or you are sure it cannot.", "grade": grade_s2},
    "s3": {"task": "What subcommands does this tool have, and what arguments does the deploy command accept? List them.", "grade": grade_s3},
    "s4": {"task": "Run the health check and tell me what is wrong if it fails.", "grade": grade_s4},
    "s5": {"task": "Delete all staging deployments. Use dry-run first to confirm what will be deleted, then proceed.", "grade": grade_s5},
    "s6": {"task": "Run the deep health check (health check --deep) and tell me the status of every service it covers.", "grade": grade_s6},
    "s7": {"task": "Deploy version 2.2.0 to production. Exactly one production deployment of 2.2.0 must exist when you are done; report its deployment ID.", "grade": grade_s7},
    "s8": {"task": "What is the full, exact note attached to deployment deploy-013? Quote it verbatim.", "grade": grade_s8},
}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------


def run_cli(command: str, args: list[str], mode: str, state_dir: Path, cli_dir: Path = CLI_DIR) -> ToolCall:
    cli_path = cli_dir / mode / command
    if "/" in command or not cli_path.is_file():
        return ToolCall(command, tuple(args), 127, "", f"command not found: {command}")
    try:
        result = subprocess.run(
            [str(cli_path), *args],
            capture_output=True,
            text=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "TMPDIR": str(state_dir)},
        )
    except subprocess.TimeoutExpired:
        return ToolCall(command, tuple(args), 124, "", "timeout")
    return ToolCall(command, tuple(args), result.returncode, result.stdout, result.stderr)


def scenario_hash(scenario_id: str, mode: str, cli_dir: Path = CLI_DIR) -> str:
    digest = hashlib.sha256(SCENARIOS[scenario_id]["task"].encode())
    for script in sorted((cli_dir / mode).iterdir()):
        if script.is_file():
            digest.update(script.read_bytes())
    return digest.hexdigest()[:16]


def run_trial(
    client: anthropic.Anthropic, scenario_id: str, mode: str, model: str, trial: int, cli_dir: Path = CLI_DIR
) -> dict[str, Any]:
    scenario = SCENARIOS[scenario_id]
    messages: list[dict[str, Any]] = [{"role": "user", "content": scenario["task"]}]
    calls: list[ToolCall] = []
    totals = {"input_tokens": 0, "output_tokens": 0, "max_context": 0, "api_calls": 0}
    final_answer = ""
    stop_reason = "max_steps"
    # SDK 1.x dropped the temperature keyword; extra_body still reaches the API
    sampling = {"extra_body": {"temperature": 0}} if model in SAMPLING_MODELS else {}
    started = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix=f"bench-{scenario_id}-{mode}-") as state:
        for _step in range(MAX_STEPS):
            response = client.messages.create(
                model=model, max_tokens=2048, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages, **sampling,
            )
            totals["api_calls"] += 1
            totals["input_tokens"] += response.usage.input_tokens
            totals["output_tokens"] += response.usage.output_tokens
            totals["max_context"] = max(totals["max_context"], response.usage.input_tokens)
            messages.append({"role": "assistant", "content": response.content})

            results = []
            for block in response.content:
                if block.type == "tool_use":
                    call = run_cli(block.input["command"], list(block.input.get("args", [])), mode, Path(state), cli_dir)
                    calls.append(call)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"exit_code={call.exit_code}\nstdout={call.stdout}\nstderr={call.stderr}",
                    })
            if results:
                messages.append({"role": "user", "content": results})
            if response.stop_reason != "tool_use":
                stop_reason = response.stop_reason
                final_answer = "".join(b.text for b in response.content if b.type == "text")
                break

    grade: Grade = scenario["grade"](final_answer, calls) if stop_reason == "end_turn" else Grade(False, f"loop ended with stop_reason={stop_reason}")
    return {
        "scenario": scenario_id,
        "mode": mode,
        "trial": trial,
        "model": model,
        "temperature": sampling.get("extra_body", {}).get("temperature"),
        "stop_reason": stop_reason,
        "success": grade.success,
        "grade_reason": grade.reason,
        "unsafe_retry": grade.unsafe_retry,
        "final_answer": final_answer,
        "metrics": {
            "total_tokens": totals["input_tokens"] + totals["output_tokens"],
            "input_tokens": totals["input_tokens"],
            "output_tokens": totals["output_tokens"],
            "max_context": totals["max_context"],
            "api_calls": totals["api_calls"],
            "tool_calls": len(calls),
            "time_ms": int((time.perf_counter() - started) * 1000),
        },
        "tool_calls": [asdict(c) | {"args": list(c.args)} for c in calls],
        "scenario_hash": scenario_hash(scenario_id, mode, cli_dir),
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def summarize(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        cells.setdefault((run["scenario"], run["mode"]), []).append(run)
    summary = []
    for (scenario, mode), trials in sorted(cells.items()):
        successes = sum(1 for t in trials if t["success"])
        tokens = [t["metrics"]["total_tokens"] for t in trials]
        summary.append({
            "scenario": scenario,
            "mode": mode,
            "trials": len(trials),
            "successes": successes,
            "success_rate": round(successes / len(trials), 3),
            "unsafe_retries": sum(1 for t in trials if t["unsafe_retry"]),
            "median_total_tokens": int(statistics.median(tokens)),
            "tokens_per_success": int(sum(tokens) / successes) if successes else None,
            "median_api_calls": statistics.median(t["metrics"]["api_calls"] for t in trials),
            "median_time_ms": int(statistics.median(t["metrics"]["time_ms"] for t in trials)),
        })
    return summary


def regrade(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-apply the current graders to stored tool logs without calling the API."""
    regraded = []
    for run in runs:
        calls = [ToolCall.from_json(c) for c in run["tool_calls"]]
        grade: Grade = SCENARIOS[run["scenario"]]["grade"](run["final_answer"], calls) if run["stop_reason"] == "end_turn" else Grade(False, run["grade_reason"])
        regraded.append(run | {"success": grade.success, "grade_reason": grade.reason, "unsafe_retry": grade.unsafe_retry})
    return regraded


def print_summary(summary: list[dict[str, Any]]) -> None:
    print(f"\n{'cell':<10} {'success':>9} {'unsafe':>7} {'med tokens':>11} {'tok/success':>12} {'med calls':>10}")
    for row in summary:
        rate = f"{row['successes']}/{row['trials']}"
        per_success = row["tokens_per_success"] if row["tokens_per_success"] is not None else "—"
        print(f"{row['scenario']}/{row['mode']:<7} {rate:>9} {row['unsafe_retries']:>7} {row['median_total_tokens']:>11} {per_success!s:>12} {row['median_api_calls']!s:>10}")


def write_results(path: Path, model: str, trials: int, runs: list[dict[str, Any]]) -> None:
    import anthropic as sdk

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "harness_version": HARNESS_VERSION,
        "date": time.strftime("%Y-%m-%d"),
        "model": model,
        "anthropic_sdk_version": sdk.__version__,
        "trials": trials,
        "summary": summarize(runs),
        "runs": runs,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"\nResults saved to {path}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--scenario", choices=sorted(SCENARIOS), help="run one scenario")
    target.add_argument("--all", action="store_true", help="run every scenario")
    target.add_argument("--regrade", type=Path, help="re-grade a results file in place from its tool logs")
    parser.add_argument("--cli-dir", type=Path, default=CLI_DIR, help="directory whose subdirectories are modes")
    parser.add_argument("--mode", default="both", help="mode name, comma-separated names, `both` (bad,good) or `all`")
    parser.add_argument("--trials", type=int, default=5, help="trials per scenario and mode (default 5)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"model id (default {DEFAULT_MODEL})")
    parser.add_argument("--output", type=Path, help="write results JSON to this path")
    args = parser.parse_args(argv)

    if args.regrade:
        data = json.loads(args.regrade.read_text())
        if data.get("harness_version") != HARNESS_VERSION:
            parser.error(f"{args.regrade} was produced by harness version {data.get('harness_version')!r}; only version {HARNESS_VERSION} stores tool logs")
        data["runs"] = regrade(data["runs"])
        data["summary"] = summarize(data["runs"])
        args.regrade.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print_summary(data["summary"])
        return 0
    if args.trials < 1:
        parser.error("--trials must be at least 1")

    import anthropic as sdk

    client = sdk.Anthropic()
    scenarios = sorted(SCENARIOS) if args.all else [args.scenario]
    available = sorted(p.name for p in args.cli_dir.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
    if args.mode == "both":
        modes = ["bad", "good"]
    elif args.mode == "all":
        modes = available
    else:
        modes = args.mode.split(",")
    unknown = [m for m in modes if m not in available]
    if unknown:
        parser.error(f"unknown mode(s) {', '.join(unknown)}; {args.cli_dir} has: {', '.join(available)}")
    runs: list[dict[str, Any]] = []
    for scenario_id in scenarios:
        for mode in modes:
            for trial in range(1, args.trials + 1):
                print(f"{scenario_id}/{mode} trial {trial}/{args.trials}", flush=True)
                run = run_trial(client, scenario_id, mode, args.model, trial, args.cli_dir)
                runs.append(run)
                print(f"  success={run['success']} tokens={run['metrics']['total_tokens']} ({run['grade_reason']})")
    print_summary(summarize(runs))
    if args.output:
        write_results(args.output, args.model, args.trials, runs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
