"""Run the code generators schemas/codegen-guide.md names against the canonical schemas.

This file is the single source of the install and generate commands: the guide prints
them verbatim (tests/test_codegen.py fails when the two drift) and CI runs them through
this script, so a schema change that breaks a generator, or its output's compiler,
fails the build.

The canonical schemas are the rows of the "Canonical types" table in schemas/index.md;
tooling schemas are not part of the CLI contract and are not generated.

Usage:
  uv run scripts/codegen.py install  LANG               install the pinned generator
  uv run scripts/codegen.py generate LANG [--out DIR]   generate bindings into DIR
  uv run scripts/codegen.py compile  LANG [--out DIR]   compile what generate wrote
  uv run scripts/codegen.py commands LANG [--out DIR]   print the install and generate commands

LANG is one of: python, typescript, rust, go, java. DIR defaults to the guide's
output directory for the language.

Exit codes: 0 success, 1 a command failed or wrote no output, 2 usage error.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from spec_corpus import ROOT

INDEX_PATH = ROOT / "schemas" / "index.md"

DATAMODEL_CODE_GENERATOR = "0.102.0"
JSON_SCHEMA_TO_TYPESCRIPT = "16.0.0"
CARGO_TYPIFY = "0.10.2"
GO_JSONSCHEMA = "v0.24.1"
JSONSCHEMA2POJO = "1.3.3"

# Compilers and runtime libraries the compile step needs; not part of the guide
PYTHON = "3.14"
PYDANTIC = "2.12.5"
TYPESCRIPT = "5.9.2"

_CANONICAL_ROW = re.compile(r"^\| \w+ \| [\d.]+ \| \[`([a-z-]+\.json)`\]", re.M)


class CodegenError(Exception):
    """A generator or compiler failed, or wrote no output."""


def canonical_schemas() -> list[str]:
    """Return the canonical schema stems, in the order schemas/index.md lists them."""
    text = INDEX_PATH.read_text(encoding="utf-8")
    start = text.index("## Canonical types")
    end = text.index("\n## ", start + 1)
    names = _CANONICAL_ROW.findall(text[start:end])
    if not names:
        raise CodegenError(f"{INDEX_PATH}: no rows in the Canonical types table")
    return [name.removesuffix(".json") for name in names]


def _module(stem: str) -> str:
    return stem.replace("-", "_")


@dataclass(frozen=True)
class Generator:
    lang: str
    guide_out: str
    install: tuple[str, ...]

    def generate(self, out: str, schemas: list[str]) -> list[str]:
        """Return the shell commands that write the bindings for schemas into out."""
        return [f"mkdir -p {out}", *self._generate(out, schemas)]

    def _generate(self, out: str, schemas: list[str]) -> list[str]:
        if self.lang == "python":
            return [
                f"datamodel-codegen --input schemas/{s}.json --input-file-type jsonschema"
                f" --output {out}/{_module(s)}.py --output-model-type pydantic_v2.BaseModel"
                " --use-annotated --enum-field-as-literal all"
                for s in schemas
            ]
        if self.lang == "typescript":
            return [
                f'json2ts --input schemas/{s}.json --output {out}/{s}.ts --bannerComment ""'
                for s in schemas
            ]
        if self.lang == "rust":
            return [f"cargo typify schemas/{s}.json --output {out}/{_module(s)}.rs" for s in schemas]
        if self.lang == "go":
            inputs = " ".join(f"schemas/{s}.json" for s in schemas)
            return [f"go-jsonschema --package framework --output {out}/types.go {inputs}"]
        if self.lang == "java":
            inputs = " ".join(f"schemas/{s}.json" for s in schemas)
            return [
                f"jsonschema2pojo --source {inputs} --target {out}"
                " --package com.example.framework --annotation-style JACKSON2"
                " --generate-builders --target-version 11"
            ]
        raise CodegenError(f"no generate command for {self.lang}")

    def outputs(self, out: Path, schemas: list[str]) -> list[Path]:
        """Return the files generate must have written, non-empty."""
        if self.lang == "python":
            return [out / f"{_module(s)}.py" for s in schemas]
        if self.lang == "typescript":
            return [out / f"{s}.ts" for s in schemas]
        if self.lang == "rust":
            return [out / f"{_module(s)}.rs" for s in schemas]
        if self.lang == "go":
            return [out / "types.go"]
        if self.lang == "java":
            found = sorted(out.rglob("*.java"))
            if not found:
                raise CodegenError(f"jsonschema2pojo wrote no .java file under {out}")
            return found
        raise CodegenError(f"no outputs for {self.lang}")


GENERATORS: dict[str, Generator] = {
    g.lang: g
    for g in (
        Generator(
            "python",
            "src/models",
            (f"uv tool install datamodel-code-generator=={DATAMODEL_CODE_GENERATOR}",),
        ),
        Generator(
            "typescript",
            "src/types",
            (f"npm install -g json-schema-to-typescript@{JSON_SCHEMA_TO_TYPESCRIPT}",),
        ),
        Generator(
            "rust",
            "src/types",
            (f"cargo install cargo-typify@{CARGO_TYPIFY} --locked",),
        ),
        Generator(
            "go",
            "pkg/framework",
            (f"go install github.com/atombender/go-jsonschema@{GO_JSONSCHEMA}",),
        ),
        Generator(
            "java",
            "src/main/java",
            (
                'mkdir -p "$HOME/.local/share/jsonschema2pojo" "$HOME/.local/bin"',
                "curl -fsSL https://github.com/joelittlejohn/jsonschema2pojo/releases/download/"
                f"jsonschema2pojo-{JSONSCHEMA2POJO}/jsonschema2pojo-{JSONSCHEMA2POJO}.tar.gz"
                " | tar -xz --strip-components=1 --exclude '._*'"
                ' -C "$HOME/.local/share/jsonschema2pojo"',
                'ln -sf "$HOME/.local/share/jsonschema2pojo/bin/jsonschema2pojo"'
                ' "$HOME/.local/bin/jsonschema2pojo"',
            ),
        ),
    )
}


def _run(command: str | list[str], cwd: Path = ROOT) -> None:
    shown = command if isinstance(command, str) else " ".join(command)
    print(f"$ {shown}", flush=True)
    argv = ["bash", "-euo", "pipefail", "-c", command] if isinstance(command, str) else command
    result = subprocess.run(argv, cwd=cwd, check=False)
    if result.returncode != 0:
        raise CodegenError(f"exit {result.returncode}: {shown}")


def install(gen: Generator) -> None:
    for command in gen.install:
        _run(command)


def generate(gen: Generator, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    schemas = canonical_schemas()
    # Run every command before failing, so one run names every schema a generator rejects
    failures = []
    for command in gen.generate(_shell_path(out), schemas):
        try:
            _run(command)
        except CodegenError as exc:
            print(f"codegen: {exc}", file=sys.stderr, flush=True)
            failures.append(str(exc))
    if failures:
        raise CodegenError(f"{gen.lang}: {len(failures)} generate command(s) failed:\n  " + "\n  ".join(failures))
    for path in gen.outputs(out, schemas):
        if not path.is_file() or path.stat().st_size == 0:
            raise CodegenError(f"{gen.lang}: generator wrote no output to {path}")
        print(f"ok {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


def _shell_path(out: Path) -> str:
    return str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)


def compile_output(gen: Generator, out: Path) -> None:
    schemas = canonical_schemas()
    files = gen.outputs(out, schemas)
    if gen.lang == "python":
        imports = ", ".join(path.stem for path in files)
        _run(
            ["uv", "run", "--no-project", "--python", PYTHON, "--with", f"pydantic=={PYDANTIC}",
             "python", "-c", f"import {imports}"],
            cwd=out,
        )
    elif gen.lang == "typescript":
        _run(
            ["npx", "--yes", "-p", f"typescript@{TYPESCRIPT}", "tsc", "--noEmit", "--strict",
             *(str(path) for path in files)]
        )
    elif gen.lang == "rust":
        crate = out.parent / f"{out.name}-check"
        if crate.exists():
            shutil.rmtree(crate)
        (crate / "src").mkdir(parents=True)
        (crate / "Cargo.toml").write_text(
            "[package]\n"
            'name = "codegen-check"\n'
            'version = "0.0.0"\n'
            'edition = "2024"\n'
            "publish = false\n\n"
            "[dependencies]\n"
            'chrono = { version = "0.4", features = ["serde"] }\n'
            'regress = "0.12"\n'
            'serde = { version = "1", features = ["derive"] }\n'
            'serde_json = "1"\n',
            encoding="utf-8",
        )
        (crate / "src" / "lib.rs").write_text(
            "".join(f'#[path = "{path.resolve()}"]\npub mod {path.stem};\n' for path in files),
            encoding="utf-8",
        )
        _run(["cargo", "check", "--quiet", "--manifest-path", str(crate / "Cargo.toml")])
    elif gen.lang == "go":
        (out / "go.mod").write_text("module example.com/framework\n\ngo 1.25\n", encoding="utf-8")
        # The output imports github.com/go-viper/mapstructure/v2; tidy records it in go.mod
        _run(["go", "mod", "tidy"], cwd=out)
        _run(["go", "build", "./..."], cwd=out)
    elif gen.lang == "java":
        tool = shutil.which("jsonschema2pojo")
        if tool is None:
            raise CodegenError("jsonschema2pojo is not on PATH; run install first")
        lib = Path(tool).resolve().parent.parent / "lib"
        classes = out.parent / f"{out.name}-classes"
        _run(["javac", "-d", str(classes), "-cp", f"{lib}/*", *(str(path) for path in files)])
    else:
        raise CodegenError(f"no compile step for {gen.lang}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("action", choices=("install", "generate", "compile", "commands"))
    parser.add_argument("lang", choices=sorted(GENERATORS))
    parser.add_argument("--out", type=Path, help="output directory (default: the guide's)")
    args = parser.parse_args(argv)
    gen = GENERATORS[args.lang]
    out = (args.out or Path(gen.guide_out)).absolute()
    try:
        if args.action == "install":
            install(gen)
        elif args.action == "generate":
            generate(gen, out)
        elif args.action == "compile":
            compile_output(gen, out)
        else:
            for command in (*gen.install, *gen.generate(_shell_path(out), canonical_schemas())):
                print(command)
    except CodegenError as exc:
        print(f"codegen: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
