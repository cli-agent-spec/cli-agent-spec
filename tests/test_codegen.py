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


@pytest.mark.parametrize("lang", sorted(codegen.GENERATORS))
def test_skip_list_is_canonical_explained_and_in_the_guide(lang: str) -> None:
    gen = codegen.GENERATORS[lang]
    canonical = codegen.canonical_schemas()
    guide = GUIDE.read_text(encoding="utf-8")
    for stem, reason in gen.skip.items():
        assert stem in canonical
        assert reason
        assert f"`{stem}`" in guide, f"the guide does not name {stem}, which {lang} skips"
        if "if/then/else" in reason:
            schema = (ROOT / "schemas" / f"{stem}.json").read_text(encoding="utf-8")
            assert '"if"' in schema, f"{stem} no longer uses if/then; drop it from the {lang} skip list"
    skipped_commands = {command for _, command in gen.skipped(gen.guide_out, canonical)}
    assert skipped_commands.isdisjoint(_guide_lines()), "the guide prints a command for a skipped schema"
    assert len(gen.targets(canonical)) == len(canonical) - len(gen.skip)


def test_rust_skips_exactly_the_if_then_schemas() -> None:
    assert sorted(codegen.GENERATORS["rust"].skip) == ["exit-code-entry", "manifest-response", "response-envelope"]


def test_skip_list_naming_a_non_canonical_schema_fails() -> None:
    gen = codegen.Generator("rust", "src/types", (), {"no-such-schema": "reason"})
    with pytest.raises(codegen.CodegenError, match="no-such-schema"):
        gen.targets(codegen.canonical_schemas())


def test_ci_matrix_covers_every_generator() -> None:
    match = re.search(r"^\s*lang: \[([a-z, ]+)\]\s*$", WORKFLOW.read_text(encoding="utf-8"), re.M)
    assert match is not None, "validate.yml has no codegen lang matrix"
    assert sorted(lang.strip() for lang in match.group(1).split(",")) == sorted(codegen.GENERATORS)


def test_unknown_lang_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        codegen.main(["generate", "cobol"])
    assert exc.value.code == 2
