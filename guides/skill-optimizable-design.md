# Guide: Designing CLIs for Skill Optimization

> **The principle:** A CLI whose behavior is expressed in domain-semantic terms produces procedures that agents can learn once and reuse across models, runtimes, and execution harnesses. A CLI whose correct usage depends on execution-environment idioms produces knowledge that is opaque, brittle, and non-transferable.

SkillOpt (Yang et al., 2026) makes this empirical. A SpreadsheetBench skill trained entirely inside the Codex execution harness transfers to Claude Code with a +59.7 point gain — slightly exceeding the score of a skill trained natively in Claude Code. The transferred rules are workbook-level: "inspect workbook structure before writing; write evaluated static values, not formula references." They are not harness-specific command sequences. Because the rule encodes a fact about spreadsheets rather than a fact about the execution environment, it survives the harness boundary.

For CLI authors, the implication is design-time: every decision that ties correct usage to execution-environment conventions reduces the transferability of any knowledge an agent builds about that tool.

---

## The Transferable/Non-Transferable Distinction

A procedure transfers when it encodes domain semantics. It does not transfer when it encodes execution-environment facts.

**Transfers:** "To get consistent output from this spreadsheet tool, inspect the workbook structure before writing and use evaluated values rather than formulas."

**Does not transfer:** "In Codex, check for `codex_trace_summary.txt` after each call; in Claude Code, read the workspace `.skill.md` instead."

The first rule is true regardless of how the agent runs — it reflects a fact about spreadsheets. The second requires the agent to know which harness it is in.

| Transfers | Does not transfer |
|---|---|
| `--output json` produces structured data | Output format changes based on `$TERM` or `CI=true` |
| Exit 1 means failure, exit 0 means success | Exit codes vary by OS, shell, or caller env |
| `--dry-run` shows effects without side effects | Dry-run behavior depends on config file presence |
| Error details in stderr as structured JSON | Errors mixed with progress; format depends on verbosity |
| Flag values override config | Config shadows flag silently in some environments |

---

## Prerequisites for Skill Optimization

SkillOpt's training loop — rollout, reflect, edit, validate — requires three prerequisites from any CLI it optimizes against.

### 1. Automatic Verifiers

The held-out validation gate that stabilizes training requires a reliable scalar success signal: did this task succeed? For CLIs, that means exit codes and output must be machine-interpretable without external oracles.

A CLI where "success" requires reading human-formatted text and making a judgment call cannot support automatic validation gating. The optimizer learns from ambiguous signal and produces unstable skills — or cannot train at all.

**What CLI authors must provide:**
- Exit 0 for success, non-zero for failure — no exit 0 with embedded error text (§1)
- Structured, parseable output format (§2)
- Deterministic output — the same successful invocation must produce the same exit code and output shape (§7)

**The concrete cost of ambiguity:** OfficeQA gains +39.0 points from a single accepted edit when the CLI provides clean verifiable output. When verifiers are unreliable, the validation gate cannot distinguish a skill improvement from noise.

### 2. Stable, Bounded Output

SkillOpt compresses trajectories into evidence batches. Verbose, unbounded, or non-deterministic output inflates training cost and degrades signal quality.

From the paper's cost figures: SearchQA costs 213M training tokens at 37.9M tokens per test-point gain — an order of magnitude more expensive than SpreadsheetBench's 0.6M per point. The difference traces directly to trajectory length: longer, more verbose trajectories cost more per training step.

**What CLI authors must provide:**
- Respect `--no-color`, `--quiet`, and `--output json` — do not emit progress text when structured output is requested (§4, §8)
- Paginate or truncate large outputs rather than streaming everything to stdout (§5, §43)
- Separate progress and diagnostic output from result data (§3)

### 3. Harness-Agnostic Behavior

The cross-harness transfer results directly expose CLI design choices that break portability. Codex and Claude Code expose different tool APIs, workspace layouts, and file conventions — yet skills transfer between them when the CLI's correct usage encodes domain knowledge rather than harness knowledge.

**What breaks cross-harness transfer:**
- Output format conditioned on `$TERM`, `CI`, or other env vars the harness happens to set (§28)
- Error messages or output that reference the harness's workspace path conventions (§29)
- Interactive flows that succeed in one harness (which sets up a TTY) and deadlock in another (§10)
- Behavior that changes based on undocumented config file defaults (§28)

---

## The Protected-Region Pattern

SkillOpt separates fast per-step edits from slow epoch-level consolidation using markup fences in the skill document:

```
<!-- SLOW_UPDATE_START -->
When you encounter X, prefer Y over Z. Repeated Z-then-fail patterns indicate...
<!-- SLOW_UPDATE_END -->
```

Step-level optimizer prompts cannot overwrite this region; only the epoch-boundary process manages it. This prevents fast local edits from erasing durable cross-epoch lessons.

The CLI analog is config-layer transparency. If a CLI has multiple behavioral layers — flag values, per-user config, global defaults — the precedence must be explicit and documented, because the optimizer cannot distinguish "this flag has no effect here" from "this flag works but I'm using it wrong."

```
$ tool --output json --config /dev/null
# Should produce JSON unconditionally.
# If --config /dev/null doesn't suppress the config that overrides --output,
# the optimizer learns contradictory rules: "pass --output json → sometimes works."
```

**What CLI authors must provide:**
- Explicit, unconditional flag precedence (flags beat config, always) (§28)
- Document which flags can be silenced by config; better: do not allow that
- Make `--config /dev/null` or equivalent produce a clean default-only environment for testability

---

## What Skill Optimization Cannot Fix

Some failure modes abort rollouts before any trajectory is logged. The optimizer receives no evidence — there is nothing to learn from.

| Failure mode | Why the rollout aborts |
|---|---|
| §10 TTY / interactivity deadlock | CLI reads from TTY; non-TTY rollout blocks forever |
| §11 Hanging process | CLI does not respect timeout; rollout exceeds training budget |
| §25 Prompt injection | CLI embeds malicious content in output; trust boundary is at the CLI layer |
| §34 Shell injection | CLI constructs shell strings from input; validation is at the CLI layer |
| §45 Headless auth deadlock | OAuth browser flow; structural TTY dependency |
| §60 OS output buffer deadlock | 64 KB pipe buffer fills; both ends block waiting for the other |

These failure modes define the practical boundary of what skill optimization can achieve. The spec's requirements for each are the prerequisite layer that must be satisfied before a skill optimizer can operate.

The useful partition for CLI authors: **behavioral** failure modes (format, verbosity, error quality, procedure) can be partially remediated by a well-trained skill. **Structural** failure modes (deadlocks, injections, physical limits) require fixes at the CLI layer — no skill can work around a process that never exits.

---

## For CLI Authors: The Skill-Optimizability Checklist

A CLI is ready for skill optimization when these pass:

| Check | Command | Expected result |
|-------|---------|-----------------|
| Exit codes are reliable | Run a failing command | Non-zero exit with parseable error in stderr |
| JSON output is unconditional | `your-tool --output json \| python3 -c "import sys,json; json.load(sys.stdin)"` | Parses without error |
| No TTY dependence | `your-tool --output json < /dev/null \| cat` | Same JSON output as with TTY |
| Flags beat config | `your-tool --output json --config /dev/null` | JSON output even with no config |
| Output is bounded | Run the largest expected command | Output terminates; does not stream indefinitely |

---

## For AI Agents

When a CLI has no optimized skill available, the failure modes in this list are the ones worth detecting early — they will cause the optimizer's training rollouts to abort with no usable evidence:

```python
import subprocess, signal

def probe_cli_for_optimization(tool: str, test_cmd: list[str]) -> dict:
    """
    Quick structural check: does this CLI produce learnable trajectories?
    Returns a dict describing which prerequisites pass and which fail.
    """
    issues = []

    # Check 1: no TTY dependence
    result = subprocess.run(
        test_cmd,
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
    if result.returncode is None:
        issues.append("hangs — no timeout signal (§11)")

    # Check 2: exit code on failure is non-zero
    fail_result = subprocess.run(
        [tool, "--nonexistent-flag-xyz"],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=5,
    )
    if fail_result.returncode == 0:
        issues.append("exits 0 on invalid input — verifier unreliable (§1)")

    # Check 3: structured output when requested
    json_result = subprocess.run(
        test_cmd + ["--output", "json"],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
    try:
        import json
        json.loads(json_result.stdout)
    except (ValueError, Exception):
        issues.append("--output json does not produce parseable JSON (§2)")

    return {"optimizable": len(issues) == 0, "issues": issues}
```

**Limitation:** This probe only checks structural prerequisites. It cannot assess whether the CLI's domain behavior is rich enough to benefit from skill optimization, or whether the training data volume will be sufficient for the optimizer's validation gate to converge.

---

## Related

| Document | Relationship |
|----------|-------------|
| [§44 Agent Knowledge Packaging Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md) | Provides: the problem SkillOpt-trained skills solve — procedures an agent cannot infer from `--help` |
| [§1 Exit Codes & Status Signaling](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) | Enforces: reliable exit codes are required for the validation gate's scalar score |
| [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) | Enforces: parseable output is a prerequisite for automatic verification |
| [§7 Output Non-Determinism](../challenges/04-critical-output-and-parsing/07-medium-output-nondeterminism.md) | Enforces: deterministic output produces consistent training evidence |
| [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) | Provides: the structural deadlock that terminates rollouts before any trajectory is logged |
| [§11 Timeouts & Hanging Processes](../challenges/02-critical-execution-and-reliability/11-critical-timeouts.md) | Provides: the hanging-process failure that exhausts training budgets |
| [§28 Config File Shadowing & Precedence](../challenges/05-high-environment-and-state/28-high-config-shadowing.md) | Provides: the config-shadowing failure that makes skill-learned flag patterns unreliable |
| [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md) | Enforces: verbose output inflates training cost by an order of magnitude |
| [research/alternatives-landscape.md](../research/alternatives-landscape.md) | Sources: SkillOpt analysis in the alternatives landscape |
