# S-003: Spec implementations in the comparison matrix

status: approved
serves: G-3

## Problem

`comparison-matrix.md` rates twelve existing solutions against all 76 active failure modes, and none of them implements the spec. It shows the gap but nothing closing it, so G-3 (frameworks adopt it: the comparison matrix shows real implementations closing the gap) has no place to show progress. A framework author who implements the spec cannot be listed, and a reader cannot tell a rating backed by a kit run from a hand rating; Q-4 asks that claims about frameworks be dated and reproducible. This is item W-2 of the accepted plan #100, filed as #117: an implementation appears in the matrix with its published conformance result as the evidence for its ratings. It builds on W-1 (#112, merged in #124), which made the matrix rate the whole catalog.

## Behaviour

Where implementations appear:

- `comparison-matrix.md` gains `## Part 8: Spec Implementations` after Part 7. Part 1, Part 2, and the twelve analysed solutions don't change, and the `matrix` check of `scripts/validate_links.py` keeps reading only Part 1 and Part 2
- Part 8 holds a legend, a listing table, a rating table, and a count table:
  - The listing table has one row per implementation with the columns `Implementation`, `Language`, `Version`, `Repository`, `Evidence`, `Spec version`, `Date`. `Evidence` links the committed result file; `Language` is informational and no rule depends on it (N-3)
  - The rating table has one row per active failure mode (`#`, `Failure mode`, as in Part 1) and one column per listed implementation
  - The count table has one row per implementation with its number of ✓, ~, ✗, and ○ cells. It has no coverage percentage, so an implementation's column is not ranked against Part 2 scores that come from hand ratings
- With no implementation listed, the listing table has no rows, the rating and count tables are absent, and a sentence says no implementation is listed yet. This repo lists and rates implementations; it does not host them (N-1)
- `website/comparison-matrix.md` is a symlink to `comparison-matrix.md`, so the website shows Part 8 with no separate change

What counts as evidence:

- The only evidence is a conformance kit result: the `ResponseEnvelope` that `uv run conformance/run.py <profile>` prints, committed verbatim as `conformance/results/<implementation>.json`. A hand rating, a link alone, or a claim in an implementation's README is not evidence. The committed copy keeps the check offline and survives link rot; the `Repository` cell links where the implementation and its profile live
- `conformance/run.py` stamps every result with a `run` object: `spec_version`, the spec release the kit ran from (the newest released heading of `CHANGELOG.md`, `X.Y.Z`), and `date`, the UTC date of the run (`YYYY-MM-DD`). The kit ships with the spec and has no version of its own, so `spec_version` identifies both
- `schemas/conformance-profile.json` gains an optional `implementation` object (`name`, `version`, `repository`) naming the framework or tool under test; `conformance/run.py` copies it into the result unchanged. A framework is run through a CLI built with it, and the profile says which framework and version that CLI exercises
- `schemas/conformance-result.json` and `schemas/conformance-result.md` describe `run` and `implementation`, and `schemas/conformance-profile.md` describes `implementation`; the changes are additive, so existing profiles and consumers keep working
- A listed result must carry `implementation`; a kit run without it stays valid but cannot be listed

How a result maps to ✓, ~, ✗, and ○ for failure mode §N:

- The requirements of §N are its `requirements` in `challenges/index.json`
- A requirement is checked when at least one check in the result's `checks` maps it and every check that maps it has status `pass` or `fail`; it passes when it is checked and every such check has status `pass`. This is the rule spec 001 (#120) defines for `coverage.checked`, computed here from `checks`, so this spec does not need its `coverage` field
- ✓ when every requirement of §N is checked and passes
- ~ when at least one requirement of §N passes but not all of them do (some failed or were not checked)
- ✗ when at least one requirement of §N is checked and none passes
- ○ (not checked) when no requirement of §N is checked, including a failure mode with no requirements and one added to the catalog after the result was produced. A cell never guesses: an unchecked failure mode is ○, not ✗
- The Part 8 legend states this rule and defines ○; the Part 1 legend and its ✓, ~, ✗ meanings don't change

How a listing stays current:

- Ratings are always computed from the committed result and the current `challenges/index.json`. When the catalog adds a failure mode or remaps requirements, the cells change and the validator names the expected mark; an implementation refreshes its listing by replacing its result file
- A result whose `run.spec_version` is older than the newest released version in `CHANGELOG.md` is still shown, with its `Spec version` cell reading `X.Y.Z (stale)`, never silently counted as current. Staleness alone does not fail the validator, so a spec release never breaks CI for an existing listing

How the validator enforces it, as a new `implementations` check of `scripts/validate_links.py`:

- Every listing row's `Evidence` cell names a file under `conformance/results/` that exists, whose `data` validates against `schemas/conformance-result.json`, and which carries `run` and `implementation`
- The `Implementation`, `Version`, `Repository`, `Spec version`, and `Date` cells equal the result's `implementation.name`, `implementation.version`, `implementation.repository`, `run.spec_version` (with ` (stale)` exactly when it is older than the newest release), and `run.date`
- The rating table has one row per active failure mode and one column per listing row, and each cell equals the computed mark; the count table equals the tallies of the rating table
- Every file under `conformance/results/` is listed, so no evidence sits unreferenced
- `conformance/README.md` documents `run`, `implementation`, and `conformance/results/`, and says a listed result is committed verbatim

## Acceptance criteria

- S-003-1: `comparison-matrix.md` has a `## Part 8: Spec Implementations` section after Part 7 with a legend that defines ✓, ~, ✗, and ○ and the mapping rule, and a listing table with the columns `Implementation`, `Language`, `Version`, `Repository`, `Evidence`, `Spec version`, `Date`; Part 1 still has twelve solution columns and the `matrix` check still passes
- S-003-2: With no implementation listed, `uv run scripts/validate_links.py` exits `0`, Part 8 has an empty listing table, no rating or count table, and a sentence saying no implementation is listed yet
- S-003-3: A result printed by `uv run conformance/run.py` for any profile under `conformance/profiles/` has `data.run.spec_version` equal to the newest released version in `CHANGELOG.md` and `data.run.date` equal to the UTC date of the run, and validates against `schemas/conformance-result.json`
- S-003-4: A profile with an `implementation` object validates against `schemas/conformance-profile.json`, and the kit's result carries that object unchanged in `data.implementation`; a profile without it still validates and its result has no `implementation`
- S-003-5: Exit codes and the existing `levels`, `summary`, and `checks` fields are unchanged for every profile under `conformance/profiles/`
- S-003-6: The `implementations` check fails with a `NO EVIDENCE` problem when a listing row's `Evidence` cell names no file, or a file outside `conformance/results/` or one that doesn't exist
- S-003-7: The `implementations` check fails when the evidence file's `data` does not validate against `schemas/conformance-result.json` or lacks `run` or `implementation`
- S-003-8: The `implementations` check fails when a listing row's `Implementation`, `Version`, `Repository`, `Spec version`, or `Date` cell differs from the evidence file
- S-003-9: The rating rule gives ✓, ~, ✗, and ○ as Behaviour defines them; with a result of `conformance/profiles/democli-good.json` and the current `challenges/index.json`, §8 is ✓, §10 is ~, and §79 is ○, and a result in which every check mapping §8's requirements failed gives ✗ for §8
- S-003-10: The `implementations` check fails with a `STALE RATING` problem naming the expected mark when a rating cell differs from the computed mark, and fails when the rating table misses an active failure mode, has a row for an inactive one, or has a column with no listing row
- S-003-11: The `implementations` check fails when a count table row differs from the tallies of that implementation's rating column
- S-003-12: A listing whose result's `run.spec_version` is older than the newest release passes only with a `Spec version` cell of `X.Y.Z (stale)`, and a current one passes only without ` (stale)`; staleness alone does not fail the check
- S-003-13: The `implementations` check fails when a file under `conformance/results/` is not named by any listing row
- S-003-14: `conformance/README.md` documents `run`, `implementation`, and `conformance/results/`, and says a listed result is the kit's output committed verbatim

## Out of scope

- How a framework author gets an implementation listed (what to run, what to publish, where to send it): #119, which builds on this spec
- Listing any real framework or tool: Part 8 starts empty; the first listing is its own change once an implementation publishes a result
- New kit checks, so more of an implementation's column comes from evidence: G-2 items such as #116 and #118
- The `coverage` field of a kit result: spec 001 (#120)
- Re-rating the twelve analysed solutions from kit runs: they don't implement the spec and keep their research-based ratings

## Decisions relied on

- none

## Issues

## Verification
