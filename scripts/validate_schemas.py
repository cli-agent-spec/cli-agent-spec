"""Validate the JSON schemas and every JSON example in the spec prose.

Schema checks:
  - each file is a valid draft-07 schema whose `$id` equals its filename
  - every `$ref` resolves through the shared registry
  - every declared property carries a `description`
  - `x-enum-varnames` and `x-enum-descriptions` align with `enum`

Example checks, over requirements/, schemas/, guides/, README.md, IMPLEMENTING.md:
  - every ```json block parses as JSON or as JSON Lines (use ```jsonc or ```text for annotated sketches)
  - blocks whose shape identifies a spec type validate against that type
  - blocks introduced by an "Invalid" or "Incorrect" label must fail validation

Usage:
  uv run scripts/validate_schemas.py [--json]

Exit codes: 0 no errors, 1 at least one error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT7
from spec_corpus import ROOT, FencedBlock, fenced_blocks, schema_pairs

EXAMPLE_SOURCES = ("requirements", "schemas", "guides")
EXAMPLE_FILES = ("README.md", "IMPLEMENTING.md")
DRAFT7_URI = "http://json-schema.org/draft-07/schema#"
_INVALID_LABEL = re.compile(r"^(\*\*)?(invalid|incorrect|wrong)\b", re.IGNORECASE)
_EXIT_CODE_KEY = re.compile(r"^(0|[1-9][0-9]*)$")
_CONDITIONAL = re.compile(r"/(if|then|else|not)(/|$)")
SCHEMA_FRAGMENT_SECTIONS = ("Schema",)
DELIBERATE_MISTAKE_SECTIONS = ("Common mistakes",)


@dataclass(frozen=True)
class Problem:
    kind: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.kind}: {self.location} — {self.message}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def load_schemas() -> dict[str, dict[str, object]]:
    return {pair.json_path.name: pair.load() for pair in schema_pairs()}


def build_registry(schemas: dict[str, dict[str, object]]) -> Registry:
    resources = [(name, Resource.from_contents(schema, default_specification=DRAFT7)) for name, schema in schemas.items()]
    return Registry().with_resources(resources)


def validator_for(name: str, schemas: dict[str, dict[str, object]], registry: Registry) -> Draft7Validator:
    return Draft7Validator(schemas[name], registry=registry)


def _walk_properties(node: object, pointer: str) -> Iterator[tuple[str, dict[str, object]]]:
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, value in properties.items():
                if isinstance(value, dict):
                    yield f"{pointer}/properties/{key}", value
        for key, value in node.items():
            yield from _walk_properties(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_properties(value, f"{pointer}/{index}")


def _walk_refs(node: object, pointer: str) -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            yield pointer, ref
        for key, value in node.items():
            yield from _walk_refs(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_refs(value, f"{pointer}/{index}")


def check_schemas(schemas: dict[str, dict[str, object]], registry: Registry) -> list[Problem]:
    problems: list[Problem] = []
    for name, schema in schemas.items():
        location = f"schemas/{name}"
        if schema.get("$schema") != DRAFT7_URI:
            problems.append(Problem("DRAFT", location, f"$schema must be {DRAFT7_URI!r}"))
        if schema.get("$id") != name:
            problems.append(Problem("ID", location, f"$id is {schema.get('$id')!r}, must equal the filename {name!r}"))
        for error in Draft7Validator(Draft7Validator.META_SCHEMA).iter_errors(schema):
            problems.append(Problem("META-SCHEMA", location, error.message))
        for pointer, prop in _walk_properties(schema, "#"):
            if _CONDITIONAL.search(pointer):
                continue
            if "description" not in prop and "$ref" not in prop:
                problems.append(Problem("DESCRIPTION", f"{location}{pointer}", "property has no description"))
        resolver = registry.resolver(base_uri=name)
        for pointer, ref in _walk_refs(schema, "#"):
            try:
                resolver.lookup(ref)
            except Unresolvable as error:
                problems.append(Problem("REF", f"{location}{pointer}", f"$ref {ref!r} does not resolve: {error}"))
        enum = schema.get("enum")
        for extension in ("x-enum-varnames", "x-enum-descriptions"):
            values = schema.get(extension)
            if values is not None and (not isinstance(enum, list) or not isinstance(values, list) or len(values) != len(enum)):
                problems.append(Problem("ENUM", location, f"{extension} must align one-to-one with enum"))
    return problems


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    schema: str
    pointer: str      # where inside the example the validated instance lives
    instance: object


def classify(instance: object) -> list[Target]:
    """Map an example value to the spec types it claims to be, by shape."""
    if isinstance(instance, bool):
        return []
    if isinstance(instance, int):
        return [Target("exit-code.json", "", instance)]
    if not isinstance(instance, dict):
        return []
    keys = set(instance)
    if isinstance(instance.get("ok"), bool):
        targets = [Target("response-envelope.json", "", instance)]
        data = instance.get("data")
        if isinstance(data, dict) and {"etag", "commands"} <= set(data):
            targets.append(Target("manifest-response.json", "/data", data))
        return targets
    if {"schema_version", "etag", "commands"} <= keys:
        return [Target("manifest-response.json", "", instance)]
    if "_cmd" in keys:
        return [Target("dispatch-request.json", "", instance)]
    if {"matches", "no_match", "trace_insufficient"} <= keys:
        return [Target("diagnose-result.json", "", instance)]
    if {"description", "retryable", "side_effects"} <= keys:
        return [Target("exit-code-entry.json", "", instance)]
    exit_codes = instance.get("exit_codes")
    if isinstance(exit_codes, dict):
        return [Target("exit-code-entry.json", f"/exit_codes/{code}", entry) for code, entry in exit_codes.items()]
    return []


def parse_block(block: FencedBlock) -> list[object]:
    """Parse a json block as one document, or as JSON Lines when that fails."""
    try:
        return [json.loads(block.body)]
    except json.JSONDecodeError as whole:
        lines = [line for line in block.body.splitlines() if line.strip()]
        if len(lines) < 2:
            raise whole
        return [json.loads(line) for line in lines]


def example_files() -> list[Path]:
    paths: list[Path] = []
    for directory in EXAMPLE_SOURCES:
        paths.extend(sorted((ROOT / directory).glob("*.md")))
    paths.extend(ROOT / name for name in EXAMPLE_FILES)
    return paths


def check_example_file(path: Path, validators: dict[str, Draft7Validator], stats: dict[str, int]) -> list[Problem]:
    """Validate every JSON block in one markdown file; updates stats in place."""
    problems: list[Problem] = []
    for block in fenced_blocks(path):
        if block.lang not in ("json", "jsonl"):
            continue
        if path.parent.name == "requirements" and block.section in SCHEMA_FRAGMENT_SECTIONS:
            continue
        if block.section in DELIBERATE_MISTAKE_SECTIONS:
            continue
        stats["blocks"] += 1
        location = f"{_display(path)}:{block.line}"
        try:
            documents = parse_block(block)
        except json.JSONDecodeError as error:
            problems.append(Problem("UNPARSEABLE", location, f"{error}; use ```jsonc or ```text for annotated sketches"))
            continue
        expect_invalid = bool(_INVALID_LABEL.match(block.label))
        for document in documents:
            targets = classify(document)
            if not targets:
                stats["unclassified"] += 1
                continue
            errors = [
                f"{target.schema}{target.pointer}{'/' if error.absolute_path else ''}{'/'.join(map(str, error.absolute_path))}: {error.message}"
                for target in targets
                for error in validators[target.schema].iter_errors(target.instance)
            ]
            for target in targets:
                key = target.pointer.rsplit("/", 1)[1] if target.pointer.startswith("/exit_codes/") else None
                if key is not None and not _EXIT_CODE_KEY.match(key):
                    errors.append(f"exit_codes key {key!r} is not an integer string")
            if expect_invalid:
                stats["expected_invalid"] += 1
                if not errors:
                    problems.append(Problem("INVALID EXAMPLE PASSES", location, f"labelled {block.label!r} but validates against {', '.join(t.schema for t in targets)}"))
            else:
                stats["validated"] += 1
                problems.extend(Problem("EXAMPLE", location, message) for message in errors)
    return problems


def _display(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def new_stats() -> dict[str, int]:
    return {"blocks": 0, "validated": 0, "expected_invalid": 0, "unclassified": 0}


def build_validators(schemas: dict[str, dict[str, object]], registry: Registry) -> dict[str, Draft7Validator]:
    return {name: validator_for(name, schemas, registry) for name in schemas}


def check_examples(schemas: dict[str, dict[str, object]], registry: Registry) -> tuple[list[Problem], dict[str, int]]:
    stats = new_stats()
    validators = build_validators(schemas, registry)
    problems: list[Problem] = []
    for path in example_files():
        problems.extend(check_example_file(path, validators, stats))
    return problems, stats


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="emit a JSON report on stdout")
    args = parser.parse_args(argv)

    schemas = load_schemas()
    registry = build_registry(schemas)
    schema_problems = check_schemas(schemas, registry)
    example_problems, stats = check_examples(schemas, registry)
    total = len(schema_problems) + len(example_problems)

    if args.json:
        print(json.dumps({
            "ok": total == 0,
            "errors": total,
            "stats": stats,
            "schemas": [p.__dict__ for p in schema_problems],
            "examples": [p.__dict__ for p in example_problems],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"=== schemas: {len(schema_problems)} error(s)")
        for problem in schema_problems:
            print(f"  {problem.render()}")
        print(f"=== examples: {len(example_problems)} error(s)  {stats}")
        for problem in example_problems:
            print(f"  {problem.render()}")
        print(f"--- total: {total} error(s)")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
