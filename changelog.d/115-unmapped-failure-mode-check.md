### Fixed

- `scripts/validate_links.py` no longer passes when an active failure mode maps to no requirement: a new `mapping` check reads the mapping from the `requirements/index.md` rows, as `challenges/index.json` does, and reports each such failure mode as `UNMAPPED`; merged stubs stay exempt (#115)
