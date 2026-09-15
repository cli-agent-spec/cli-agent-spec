---
name: validate-links
description: Validate the CLI Agent Spec corpus — broken file links, schema↔requirement symmetry, index completeness, required sections, prose counters, canonical snippets, JSON schemas, and every JSON example in the prose. Use when files have been added or edited, or to check the project is internally consistent.
allowed-tools: Bash
license: MIT
compatibility: Requires git and uv. Designed for the cli-agent-spec repository.
---

# Validate the Spec Corpus

## Runtime requirements

- Requires `git`
- Requires `uv` (the scripts declare their own dependencies through `pyproject.toml`)
- Run from the repository root

Both validators are deterministic scripts; this skill only runs them and explains the results. CI runs the same commands on every push.

---

## Step 1 — Run the validators

```bash
uv run scripts/validate_links.py --json
uv run scripts/validate_schemas.py --json
```

Each exits `0` when clean and `1` when any error exists. Always parse stdout as JSON regardless of exit code.

`validate_links.py` runs six checks; pass `--only <check> ...` to run a subset:

| Check | What it verifies |
|-------|------------------|
| `links` | Every relative markdown link outside code resolves to a file |
| `symmetry` | Each schema's "Used by" requirements link back to the schema; each requirement's `## Schema` links resolve |
| `indexes` | Requirements, schemas, failure modes (master and part indexes), and guides are all listed and all index rows resolve |
| `sections` | Failure modes, requirements, and schema docs carry required sections in order; Agent Workaround opens with **Signature:**, has a pinned **Tier:** gloss, **Limitation:**, and **Fallback:** exactly when Tier C |
| `counts` | Prose counters in README, AGENTS, CLAUDE, and the index files match the corpus on disk, including per-tier and per-priority counts |
| `snippets` | Every embedded `extract_envelope` copy matches the canonical block in `challenges/triage.md` |

`validate_schemas.py` checks that every schema is valid draft-07 with `$id` equal to its filename, resolvable `$ref`s, and a `description` on every property. It then validates every ```` ```json ```` block in `requirements/`, `schemas/`, `guides/`, `README.md`, and `IMPLEMENTING.md` against the spec type its shape identifies. Blocks introduced by an "Invalid" or "Incorrect" label must fail validation. Blocks under `## Schema` in requirements and under `## Common mistakes` are skipped.

---

## Step 2 — Report

```
## Validation results

### Broken file links      — N errors
### Schema ↔ req symmetry  — N errors
### Index completeness     — N errors
### Required sections      — N errors
### Counter consistency    — N errors
### Snippet consistency    — N errors
### Schemas and examples   — N errors

Total: N errors
```

List every error with its file. For each error suggest the fix:

- `BROKEN` → update the link or create the missing file
- `MISSING BACK-LINK` → link the schema from the requirement's `## Schema`, or remove the requirement from the schema's "Used by"
- `MISSING FILE` / `MISSING SCHEMA FILE` → create the file or remove the stale reference
- `UNLISTED` / `MISSING` → add or remove the index row
- `INCOMPLETE` / `OUT OF ORDER` → add or reorder sections; see `AGENTS.md` for the required order
- `NON-CANONICAL TIER` / `STRAY FALLBACK` → use a pinned Tier gloss from `challenges/triage.md`; only Tier C carries **Fallback:**
- `STALE` / `NOT FOUND` → update the counter to match the corpus, or restore the phrase the check looks for
- `DRIFT` → re-sync the `extract_envelope` copy from `challenges/triage.md`
- `UNPARSEABLE` → make the block valid JSON, or relabel an annotated sketch as ```` ```jsonc ````
- `EXAMPLE` → fix the example, or fix the schema if the example is the intended contract
- `INVALID EXAMPLE PASSES` → the example labelled invalid does not violate the schema; tighten the schema or relabel it
- `ID` / `REF` / `DESCRIPTION` / `META-SCHEMA` → fix the schema file itself
