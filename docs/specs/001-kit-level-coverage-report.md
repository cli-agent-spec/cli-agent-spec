# S-001: Kit level coverage report

status: approved
serves: G-2

## Problem

A conformance kit run (`uv run conformance/run.py <profile>`) reports each check as pass, fail, or skip and rolls them up into `level_1`, `level_2`, and `level_3` statuses. It never says which of a level's requirements its checks cover. Level 1 alone holds dozens of requirements and the kit has fourteen checks, so a CLI author reading `level_1: pass` cannot tell which requirements the kit verified and which still need a reviewer, and a published claim overstates what was proven. This is item W-1 of the accepted plan #99 for G-2, filed as #111, and the base that #116 (a Level 2 claim from a kit run) and #118 (more Level 3 opt-in checks) build on.

## Behaviour

- `conformance/run.py` adds a `coverage` object to its result `data`, next to `levels`, with one entry per level: `level_1`, `level_2`, `level_3`
- Each entry holds two sorted arrays of requirement ids (`REQ-F-NNN`, `REQ-C-NNN`, `REQ-O-NNN`): `checked`, the requirements this run verified, and `needs_review`, the rest of the level's requirements, which a reviewer must still verify
- A level's requirements are those whose lowest conformance level is that level, as `requirements/levels.md` and the requirement priorities define it (the computation `scripts/validate_links.py` already uses for the index Level column); the entries are not cumulative, so a Level 2 claim lists the `needs_review` of `level_1` and `level_2`
- A requirement is `checked` when at least one check in `CHECKS` maps it and every check that maps it ran in this run with status `pass` or `fail`; a requirement whose check was skipped, left out with `--only`, or that no check maps is `needs_review`
- `schemas/conformance-result.json` and `schemas/conformance-result.md` describe `coverage`; the change is additive, so existing consumers keep working
- `conformance/README.md` says that a conformance claim lists the `needs_review` requirements of every level it claims
- Exit codes and the existing `levels`, `summary`, and `checks` fields don't change

## Acceptance criteria

- S-001-1: A kit run's result `data.coverage` has exactly the keys `level_1`, `level_2`, `level_3`, each with `checked` and `needs_review` arrays of requirement ids, each array sorted
- S-001-2: For each level, `checked` and `needs_review` are disjoint and their union equals the set of requirements whose computed lowest level is that level
- S-001-3: A requirement is in `checked` only when every check mapping it ran with status `pass` or `fail`; with a profile that declares no stream probe, `REQ-O-004` (mapped by the skipped `stream_contract` and `stream_sigint`) is in `needs_review`
- S-001-4: With `--only json_envelope`, the requirements mapped only by other checks are in `needs_review`, and those `json_envelope` maps are in `checked`
- S-001-5: Every requirement id a check in `CHECKS` maps exists in `requirements/`, and a test fails when one doesn't
- S-001-6: The result of a run against each profile under `conformance/profiles/` validates against `schemas/conformance-result.json`, which describes `coverage` and each of its fields
- S-001-7: Exit codes and the `levels`, `summary`, and `checks` fields are unchanged for every profile under `conformance/profiles/`
- S-001-8: `conformance/README.md` documents `coverage` and says that a claim lists the `needs_review` requirements of every level it claims

## Out of scope

- New checks, and claiming Level 2 from a kit run: #116
- More Level 3 opt-in checks read from a CLI's manifest: #118
- A machine-readable requirements index the kit could read levels from: #114; the kit computes levels from the corpus as `validate_links.py` does until then

## Decisions relied on

- none

## Issues

## Verification
