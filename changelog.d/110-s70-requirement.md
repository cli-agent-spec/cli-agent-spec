### Added

- REQ-C-037 Item-Wise Commands Accept Every Item in One Call (P1, Level 3): a command whose operation applies to each of several items takes them all in one invocation, through a variadic last positional declared `variadic: true` in the manifest's `positionals`, or a declared batch input on stdin or `--input-file`. Every item is validated before any is acted on, and the response reports each item in `summary` and `results[]` as REQ-C-009 does, the same shape for one item or many. §70 (single-argument arity) now maps to a requirement; the corpus has 168 requirements (#110)
