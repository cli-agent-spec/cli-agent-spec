import json
import subprocess
import sys
import textwrap
from pathlib import Path

import spec_corpus as corpus
import validate_links as vl

ROOT = Path(__file__).resolve().parents[1]

WORKAROUND_OK = """\
    ### The Problem
    x
    ### Impact
    x
    ### Solutions
    x
    ### Evaluation
    x
    ### Agent Workaround

    **Signature:** process hangs until killed

    **Tier:** B (one observable check, then one command)

    **Limitation:** none
    """


def failure_mode(tmp_path: Path, body: str) -> corpus.FailureModeFile:
    part = tmp_path / "challenges" / "02-critical-execution-and-reliability"
    part.mkdir(parents=True)
    path = part / "10-critical-sample.md"
    path.write_text(textwrap.dedent(body))
    return corpus.FailureModeFile(corpus.FailureModeId(10), path, part.name, merged=False)


def kinds(problems: list[vl.Problem]) -> list[str]:
    return [p.kind for p in problems]


def test_corpus_is_clean() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_links.py"), "--json"], capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert report["errors"] == 0, json.dumps(report["checks"], indent=2)
    assert result.returncode == 0


def test_corpus_counts_match_disk() -> None:
    counts = vl.corpus_counts()
    assert counts["failure_modes"] == len(corpus.active_failure_modes())
    assert counts["tier_f"] + counts["tier_c"] + counts["tier_o"] == counts["requirements"]
    assert sum(counts[p] for p in ("P0", "P1", "P2", "P3")) == counts["requirements"]


def test_well_formed_failure_mode_passes() -> None:
    fm = corpus.FailureModeFile(corpus.FailureModeId(10), ROOT / "challenges/02-critical-execution-and-reliability/10-critical-interactivity.md", "02", merged=False)
    assert vl._failure_mode_problems(fm) == []


def test_sections_out_of_order_detected() -> None:
    headings = ["### Impact", "### The Problem", "### Solutions", "### Evaluation", "### Agent Workaround"]
    problem = vl._order_problem(ROOT / "README.md", headings, vl.FAILURE_MODE_SECTIONS)
    assert problem is not None and problem.kind == "OUT OF ORDER"


def test_missing_section_detected() -> None:
    headings = ["## Description", "## Acceptance Criteria", "## Schema", "## Wire Format", "## Related"]
    problem = vl._order_problem(ROOT / "README.md", headings, vl.REQUIREMENT_SECTIONS)
    assert problem is not None and "## Example" in problem.message


def test_headings_inside_nested_fences_are_ignored() -> None:
    text = textwrap.dedent("""\
        ## Wire Format

        ````markdown
        ## Installation
        ```bash
        pip install x
        ```
        ````

        ## Example
        """)
    assert vl._headings(text) == ["## Wire Format", "## Example"]


def test_tier_c_without_fallback(tmp_path: Path) -> None:
    body = WORKAROUND_OK.replace("**Tier:** B (one observable check, then one command)", "**Tier:** C (stateful logic; weak models apply the fallback below)")
    fm = failure_mode(tmp_path, body)
    problems = [p for p in vl._failure_mode_problems(fm)]
    assert "INCOMPLETE" in kinds(problems)


def test_non_canonical_tier_gloss(tmp_path: Path) -> None:
    body = WORKAROUND_OK.replace("(one observable check, then one command)", "(check then run)")
    fm = failure_mode(tmp_path, body)
    assert "NON-CANONICAL TIER" in kinds(vl._failure_mode_problems(fm))


def test_signature_must_open_workaround(tmp_path: Path) -> None:
    body = WORKAROUND_OK.replace("### Agent Workaround\n\n", "### Agent Workaround\n\n    Some prose first.\n\n")
    fm = failure_mode(tmp_path, body)
    assert "OUT OF ORDER" in kinds(vl._failure_mode_problems(fm))


def test_stray_fallback(tmp_path: Path) -> None:
    body = WORKAROUND_OK + "\n    **Fallback:** retry once\n"
    fm = failure_mode(tmp_path, body)
    assert "STRAY FALLBACK" in kinds(vl._failure_mode_problems(fm))


def test_fenced_blocks_track_section_and_label(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text(textwrap.dedent("""\
        ## Examples

        **Invalid — bad**
        ```json
        {}
        ```
        """))
    [block] = list(corpus.fenced_blocks(path))
    assert (block.section, block.label, block.lang, block.body) == ("Examples", "**Invalid — bad**", "json", "{}")


def test_level_one_is_a_subset_of_p0() -> None:
    levels = vl.requirement_levels()
    assert sorted(levels[r] for r in vl.level_one_ids()) == [1] * 12
    assert sum(1 for level in levels.values() if level <= 2) == vl.corpus_counts()["P0"]
