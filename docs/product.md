# CLI Agent Spec

## Mission

The CLI Agent Spec defines how a command-line tool must behave so AI agents can call it reliably: the failure modes agents hit, the requirements that remove them, and machine-readable schemas

## Users

- U-1: Authors of CLI frameworks implementing the spec
- U-2: CLI authors making their tools safe for agents
- U-3: Agent builders who integrate CLI tools and need to know what they can rely on

## Goals

- G-1: Every known agent failure mode documented with its cost and mapped to requirements that remove it
- G-2: A conformance kit that checks a CLI against the spec at each level
- G-3: Frameworks adopt it: the comparison matrix shows real implementations closing the gap
- G-4: Schemas an agent or a code generator consumes directly

## Non-goals

- N-1: Being a CLI framework itself; implementations live in their own repos
- N-2: Requirements for interactive, human-only use
- N-3: Rules for a single language or runtime

## Quality bar

- Q-1: Every requirement traces to a documented failure mode
- Q-2: Every JSON example in the prose validates against the schemas in CI
- Q-3: Every requirement change has a changelog entry and a version bump
- Q-4: Claims about frameworks are dated and reproducible
