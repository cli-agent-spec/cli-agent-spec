# S-002: Requirements index JSON

status: approved
serves: G-4

## Problem

An agent or a code generator reads every failure mode, with its severity, tier, signature, and requirements, from one generated file, `challenges/index.json`. The requirements have no such file: their tier, priority, conformance level, failure modes, and schemas live in `requirements/index.md` tables, `requirements/levels.md`, and each requirement file's `## Schema` section, so a consumer has to parse markdown to answer "which schemas does a Level 1 CLI need". This is item W-2 of the accepted plan #101 for G-4, filed as #114.

## Behaviour

- A new generator, `scripts/build_requirement_index.py`, writes `requirements/index.json` from the corpus, as `scripts/build_failure_index.py` writes `challenges/index.json`; `--check` exits 1 when the committed file is stale or doesn't validate, and the CI workflow `.github/workflows/validate.yml` runs it
- The file holds one entry per requirement, sorted by id, with: `id` (`REQ-F-001`), `tier` (`F`, `C`, or `O`), `title`, `priority` (`P0` to `P3`, as the index lists it), `level` (the computed lowest conformance level, `1` to `3`, or `null` for a requirement in no level), `path` (the requirement file, repo-relative), `failure_modes` (the `§N` numbers it removes, as integers), and `schemas` (the schema files its `## Schema` section links, by filename, such as `exit-code-entry.json`)
- A new schema, `schemas/requirement-index.json` with its `schemas/requirement-index.md`, describes the file (draft-07, `$id` equal to its filename, every property with a `description`), and `schemas/index.md` lists it with the tooling schemas
- Each value comes from the same parsing `scripts/validate_links.py` and `scripts/spec_corpus.py` already do, so the file and the markdown can't disagree without a validator failing
- `requirements/index.md` and `AGENTS.md` point consumers at the file, as they do for `challenges/index.json`

## Acceptance criteria

- S-002-1: `uv run scripts/build_requirement_index.py` writes `requirements/index.json` with one entry per requirement file under `requirements/`, sorted by id, and a second run leaves it byte-identical
- S-002-2: Each entry has exactly `id`, `tier`, `title`, `priority`, `level`, `path`, `failure_modes`, and `schemas`, and its `tier`, `priority`, `level`, and `failure_modes` equal what `requirements/index.md` lists for that id
- S-002-3: An entry's `schemas` lists the schema filenames its requirement file's `## Schema` section links, sorted, and is empty when it links none
- S-002-4: `uv run scripts/build_requirement_index.py --check` exits 0 on a fresh build, exits 1 naming the file when a requirement changed without a rebuild, and exits 1 when the file doesn't validate against `schemas/requirement-index.json`
- S-002-5: `schemas/requirement-index.json` is draft-07, its `$id` is its filename, every property has a `description`, its `.md` companion has the eight schema sections, and `uv run scripts/validate_schemas.py` and `uv run scripts/validate_links.py` pass with it listed in `schemas/index.md`
- S-002-6: `.github/workflows/validate.yml` runs `uv run scripts/build_requirement_index.py --check`
- S-002-7: `requirements/index.md` and `AGENTS.md` name `requirements/index.json` as the machine-readable list of requirements

## Out of scope

- Reading levels from this file in the conformance kit: a later change, once #111's coverage report exists
- Any change to a requirement's tier, priority, level, or schemas
- CI that runs the code generators: #113

## Decisions relied on

- none

## Issues

## Verification
