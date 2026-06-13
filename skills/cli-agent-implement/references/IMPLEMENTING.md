# IMPLEMENTING.md — Implementation Guide for AI Agents

This file is for AI agents helping someone **implement the CLI Agent Spec specification** in their own project. It covers how to read the spec, generate language-specific types, and validate your output.

If you are helping to **maintain or extend the specification itself**, read [`AGENTS.md`](AGENTS.md) instead.

---

## What this spec is

The **CLI Agent Spec** specification defines the contracts a CLI tool must satisfy to be reliably orchestrated by an AI agent. It covers exit codes, structured output, error envelopes, command discovery, and more. Implementing it means building a CLI framework (or extending an existing one) that enforces these contracts automatically.

---

## Where to start

| You want to… | Start here |
|--------------|------------|
| Understand what problems the spec solves | [`challenges/index.md`](challenges/index.md) |
| See all requirements at a glance | [`requirements/index.md`](requirements/index.md) |
| Implement a specific requirement | The requirement file `requirements/<id>.md` |
| Get the type definitions for your language | [`schemas/codegen-guide.md`](schemas/codegen-guide.md) |
| Validate your JSON output against a schema | [`schemas/index.md`](schemas/index.md) |

---

## Requirement tiers

Requirements are grouped into three tiers. Implement them in this order:

| Tier | Prefix | Meaning | When to implement |
|------|--------|---------|-------------------|
| Framework-Automatic | `REQ-F` | Enforced by the framework without command author action | First — these are the foundation |
| Command Contract | `REQ-C` | Declared by the command author at registration | Second — per-command declarations |
| Opt-In | `REQ-O` | Explicitly enabled by the application | Last — advanced or optional features |

Start with all `REQ-F` requirements. They establish the exit code table, response envelope, and phase boundary that everything else depends on.

---

## Reading a requirement file

Each requirement file (`requirements/<id>.md`) contains:

1. **Description** — what the requirement is and why it exists
2. **Acceptance Criteria** — testable conditions; use these to verify your implementation
3. **Schema** — links to the JSON Schema file(s) the requirement uses
4. **Wire Format** — exact JSON the implementation must emit
5. **Example** — language-agnostic pseudocode showing the pattern
6. **Related** — other requirements that compose or depend on this one

Read the **Schema** link to get the machine-readable type definition. Read **Wire Format** to know exactly what your output must look like. Use **Acceptance Criteria** as your test checklist.

---

## Generating types from schemas

The `schemas/` directory contains JSON Schema draft-07 files. Generate language-specific types once, then use them throughout your implementation.

**Full guide:** [`schemas/codegen-guide.md`](schemas/codegen-guide.md)

**Quick reference:**

| Language | Tool | Install | Generate |
|----------|------|---------|----------|
| Any | `ajv-cli` | `npm install -g ajv-cli` | `ajv validate -s schemas/... -d output.json` |
| Python | `datamodel-code-generator` | `pip install datamodel-code-generator` | `datamodel-codegen --input schemas/ --output src/models/` |
| TypeScript | `json-schema-to-typescript` | `npm install -g json-schema-to-typescript` | `json2ts --input schemas/ --output src/types/` |
| Rust | `cargo-typify` | `cargo install cargo-typify` | `cargo typify schemas/<name>.json > src/types/<name>.rs` |
| Go | `go-jsonschema` | `go install github.com/atombender/go-jsonschema@latest` | `go-jsonschema --package framework schemas/*.json > types.go` |
| Java | `jsonschema2pojo` | `brew install jsonschema2pojo` | `jsonschema2pojo --source schemas/ --target src/main/java/` |

**Always validate before generating:**

```bash
npm install -g ajv-cli
ajv compile -s "schemas/*.json" --spec=draft7
```

**Post-generation invariant:** Code generators do not enforce the `ExitCodeEntry` constraint that `retryable: true` implies `side_effects: "none"`. After generating, add the validation snippet for your language — see the "Validation after generation" section in [`schemas/codegen-guide.md`](schemas/codegen-guide.md).

---

## Key invariants to enforce

These constraints are not checked by code generators. Enforce them at registration time in your framework:

| Invariant | Where defined | Rule |
|-----------|--------------|------|
| `retryable: true` implies `side_effects: "none"` | `ExitCodeEntry` | Hard schema invariant — reject at registration |
| Exit code map must include key `"0"` (SUCCESS) | REQ-C-001 | Every command must declare a SUCCESS entry |
| `ARG_ERROR (2)` may only be emitted before any side effect | REQ-F-001 | Phase boundary between validation and execution |
| `PARTIAL_FAILURE (3)` is never retryable | REQ-F-001 | Some writes occurred — state is unknown |
| Literal integers not permitted at call sites | REQ-F-001 | Use `ExitCode` enum constants only |

---

## Suggested implementation order

1. **`REQ-F-001`** — define the `ExitCode` enum and register the 14-code table
2. **`REQ-F-004`** — implement the JSON response envelope (`ok`, `result`, `error`)
3. **`REQ-C-001`** — implement command registration with `exit_codes` map
4. **`REQ-C-013`** — wire `ExitCode` into the error envelope (`error.code`)
5. **`REQ-F-002`** — enforce the validation/execution phase boundary for `ARG_ERROR`
6. Remaining `REQ-F` requirements
7. `REQ-C` requirements
8. `REQ-O` requirements (opt-in, implement as needed)
