# S3 — Discover Command Surface

**Challenge cluster:** Schema discoverability, token spend, manifest
**Key requirements:** C-015, O-013, O-041, F-022, F-023

## Task given to agent

> "What subcommands does this tool have, and what arguments does the `deploy` command accept?"

## Expected answer

A correct list of subcommands (`deployments`, `services`, `config`, `logs`) and the flags accepted by `deploy` (`--version`, `--env`, `--dry-run`, `--idempotency-key`, `--timeout`, `--format`).

## Why this stresses the spec

**cli-bad:** The agent must call `--help` to get top-level subcommands, then `deploy --help` to get deploy's flags. Both return formatted plain-text help to stdout. The agent parses prose to extract structure. Two API round-trips minimum, more if parsing fails.

**cli-good:** One call to `manifest --format json` returns the complete command tree with typed flag definitions, descriptions, exit code maps, and examples. The agent extracts the answer in a single step.

## CLI commands exercised

```bash
# bad
--help
deploy --help

# good
manifest --format json
```

## Measured delta hypothesis

| Metric | Expected direction |
|--------|--------------------|
| `total_tokens` | bad > good (help prose vs compact manifest JSON) |
| `api_calls` | bad > good (2+ help calls vs 1 manifest call) |
| `steps` | bad > good |
