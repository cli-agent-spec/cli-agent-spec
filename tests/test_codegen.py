import re
from pathlib import Path

import pytest

import codegen

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "schemas" / "codegen-guide.md"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"


def _guide_lines() -> set[str]:
    """Every line of the guide, with backslash continuations joined and runs of spaces collapsed."""
    text = re.sub(r"\\\n\s*", " ", GUIDE.read_text(encoding="utf-8"))
    return {re.sub(r"\s+", " ", line).strip() for line in text.splitlines()}


def test_canonical_schemas_are_the_index_canonical_table() -> None:
    assert codegen.canonical_schemas() == [
        "exit-code",
        "exit-code-entry",
        "response-envelope",
        "manifest-response",
        "dispatch-request",
        "audit-log-entry",
    ]
    for stem in codegen.canonical_schemas():
        assert (ROOT / "schemas" / f"{stem}.json").is_file()


@pytest.mark.parametrize("lang", sorted(codegen.GENERATORS))
def test_guide_prints_the_commands_ci_runs(lang: str) -> None:
    gen = codegen.GENERATORS[lang]
    commands = [*gen.install, *gen.generate(gen.guide_out, codegen.canonical_schemas())]
    missing = [command for command in commands if command not in _guide_lines()]
    assert missing == [], f"schemas/codegen-guide.md lacks the {lang} commands CI runs"


def test_ci_matrix_covers_every_generator() -> None:
    match = re.search(r"^\s*lang: \[([a-z, ]+)\]\s*$", WORKFLOW.read_text(encoding="utf-8"), re.M)
    assert match is not None, "validate.yml has no codegen lang matrix"
    assert sorted(lang.strip() for lang in match.group(1).split(",")) == sorted(codegen.GENERATORS)


def test_unknown_lang_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        codegen.main(["generate", "cobol"])
    assert exc.value.code == 2
