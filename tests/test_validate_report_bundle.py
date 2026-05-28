import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "cli-agent-report" / "scripts" / "validate_report_bundle.py"


FINDINGS = textwrap.dedent(
    """\
    # sample-cli — Findings

    | Failure mode | Title | Severity | Score | Notes |
    |---|---|---|---|---|
    | §11 | Timeouts & Hanging Processes | Critical | 0/3 | No timeout contract. |
    | §12 | Idempotency & Safe Retries | Critical | 0/3 | No idempotency key. |
    | §1 | Exit Codes & Status Signaling | Critical | 1/3 | Errors are prose. |
    | §10 | Interactivity & TTY Requirements | Critical | 3/3 | Non-interactive. |
    | §42 | Debug / Trace Mode Secret Leakage | Critical | ?/3 | Not exposed. |
    """
)


VALID_X = textwrap.dedent(
    """\
    # X Premium Post — sample-cli

    <!-- Copy everything between the lines below into X as one Premium long-form post -->

    ---
    I audited sample-cli against 5 Critical CLI Agent Spec checks. Result: 1.0/3 average across scored Critical checks. Readiness: 12/15 [B]. This matters because agents can start cleanly but still need stronger runtime contracts before retrying or parsing results autonomously.

    The surprising part: install is not the problem.

    The weak points are runtime semantics for agents:

    1. Timeout behavior is not declared, so agents must impose their own deadline.
    2. Mutating operations do not expose idempotency keys or effect fields.
    3. Tool errors can appear as prose inside successful-looking results.
    4. Schema output is not enough to describe success and failure envelopes.
    5. Safe defaults need stronger side-effect and retry contracts.

    Practical guidance for agent builders:
    - enforce client-side timeouts on every invocation
    - never retry a write without your own idempotency policy
    - branch on structured error fields when present
    - validate JSON strictly before parsing
    - avoid browser-auth waits in headless environments

    Fastest CLI-author fixes:
    - structured non-interactive error envelopes
    - invariant JSON for success and failure paths
    - machine-readable schema/manifest for commands, flags, exit codes, scopes, safe defaults, and interactivity
    - dry-run/effect/idempotency contracts for setup and config commands

    Full report: [PASTE LINK HERE]
    ---

    <!-- FORMAT RULES (apply before writing content):
         - Write a single X Premium long-form post, not a numbered thread.
         - Keep the first 280 characters self-contained: tool name, audit result, and why it matters.
         - Target 900-1800 characters unless the findings need more detail; do not exceed X Premium's long-post limit.
         - No emojis unless they appear in source findings; this should read like an engineering field note.
         - Use plain text bullets and numbered lists; no markdown tables.
         - Put the link near the end, not in the opening line.
         - Never guess maintainer @handles. If an @handle is provided by the user, place it on its own line before the link.
         - Ground every claim in findings/readiness/issues; do not invent counts, scores, or bugs.
         - First person singular is allowed ("I audited") when the report was produced by one evaluator. -->
    """
)


INVALID_FREEFORM_X = textwrap.dedent(
    """\
    I audited sample-cli for agent-readiness.

    Score:
    - Failure-mode average: 1.0/3
    - Readiness: 12/15 [B]

    Main fixes needed: typed errors and idempotency.
    """
)


class ValidateReportBundleTest(unittest.TestCase):
    def make_bundle(self, x_text: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        bundle = Path(temp_dir.name) / "sample-cli"
        bundle.mkdir()

        for name in [
            "README.md",
            "report-index.md",
            "report-issues.md",
            "report-runtime.md",
            "report-agent-dev.md",
            "report-dev.md",
            "linkedin.md",
        ]:
            (bundle / name).write_text(f"# {name}\n", encoding="utf-8")

        (bundle / "findings.md").write_text(FINDINGS, encoding="utf-8")
        (bundle / "x.md").write_text(x_text, encoding="utf-8")
        return bundle

    def run_validator(self, bundle: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(bundle), "--cli", "sample-cli"],
            capture_output=True,
            text=True,
        )

    def test_valid_bundle_passes(self) -> None:
        result = self.run_validator(self.make_bundle(VALID_X))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validation passed", result.stdout)

    def test_freeform_x_post_fails(self) -> None:
        result = self.run_validator(self.make_bundle(INVALID_FREEFORM_X))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("x.md must start", result.stderr)
        self.assertIn("x.md missing template copy instruction", result.stderr)
        self.assertIn("x.md missing opening post boundary", result.stderr)

    def test_unreplaced_placeholder_fails(self) -> None:
        broken = VALID_X.replace("Timeout behavior is not declared", "{{SCORE_0_ISSUE_1}}")

        result = self.run_validator(self.make_bundle(broken))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unreplaced {{PLACEHOLDER}}", result.stderr)


if __name__ == "__main__":
    unittest.main()
