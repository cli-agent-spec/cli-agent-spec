# Shared Schemas

> Canonical type definitions for the CLI agent ergonomics framework.
> These schemas are **implementation-agnostic** — they define structure, constraints, and invariants without prescribing a language or library.

---

## Canonical types

Wire contracts a conforming CLI emits or accepts. Contract versions follow the rules in [`CHANGELOG.md`](../CHANGELOG.md#versioning).

| Schema | Contract | JSON | Notes | Used by |
|--------|----------|------|-------|---------|
| ExitCode | 1.0 | [`exit-code.json`](exit-code.json) | [`exit-code.md`](exit-code.md) | REQ-F-001, REQ-C-001, REQ-C-013, REQ-O-041 |
| ExitCodeEntry | 1.0 | [`exit-code-entry.json`](exit-code-entry.json) | [`exit-code-entry.md`](exit-code-entry.md) | REQ-C-001, REQ-O-041 |
| ResponseEnvelope | 2.0 | [`response-envelope.json`](response-envelope.json) | [`response-envelope.md`](response-envelope.md) | REQ-F-004, all commands |
| ManifestResponse | 2.0 | [`manifest-response.json`](manifest-response.json) | [`manifest-response.md`](manifest-response.md) | REQ-O-041, Command Contract declarations |
| DispatchRequest | 1.0 | [`dispatch-request.json`](dispatch-request.json) | [`dispatch-request.md`](dispatch-request.md) | REQ-O-050 |

## Tooling types

Output of this repository's skills and scripts. Not part of the CLI contract.

| Schema | JSON | Notes | Used by |
|--------|------|-------|---------|
| DiagnoseResult | [`diagnose-result.json`](diagnose-result.json) | [`diagnose-result.md`](diagnose-result.md) | `cli-agent-diagnose` skill |
| FailureModeIndex | [`failure-mode-index.json`](failure-mode-index.json) | [`failure-mode-index.md`](failure-mode-index.md) | `challenges/index.json`, `cli-agent-diagnose` skill |
| ConformanceProfile | [`conformance-profile.json`](conformance-profile.json) | [`conformance-profile.md`](conformance-profile.md) | `conformance/run.py` input |
| ConformanceResult | [`conformance-result.json`](conformance-result.json) | [`conformance-result.md`](conformance-result.md) | `conformance/run.py` output |

---

## Using the schemas

**Validate** your implementation's wire output:
```
ajv validate -s schemas/response-envelope.json -d output.json --spec=draft7 --strict=false
```

**Generate bindings** for your language:
```
# Python
datamodel-codegen --input schemas/ --input-file-type jsonschema --output src/models/

# TypeScript
json2ts --input schemas/ --output src/types/

# Rust
cargo typify schemas/<name>.json > src/types/<name>.rs

# Go
go-jsonschema --package framework schemas/*.json > pkg/framework/types.go

# Java
jsonschema2pojo --source schemas/ --target src/main/java/ --package com.example.framework
```

See **[codegen-guide.md](codegen-guide.md)** for full installation instructions, options, and post-generation validation for each language.

## Adding a new type

1. Create `schemas/<name>.json` — JSON Schema draft-07, `$id` equal to `<name>.json`.
2. Create `schemas/<name>.md` — field table and implementation notes.
3. Add a row to the Canonical or Tooling table in this index.
4. Reference `<name>.json` from the requirement that introduces the type.
5. Run `uv run scripts/validate_schemas.py` and `uv run scripts/validate_links.py`.
