# S1 — List & Extract IDs

**Challenge cluster:** Pagination, context overflow, output format
**Key requirements:** F-018, F-019, F-052, O-001, O-003, O-005

## Task given to agent

> "List all deployments and return me their IDs as a comma-separated string."

## Expected answer

`deploy-001,deploy-002,deploy-003,deploy-004,deploy-005`

(5 deployments across 2 pages of 3)

## Why this stresses the spec

**cli-bad:** Returns all 500 records as an ANSI-colored table on stdout. No pagination. The agent must parse a multi-kilobyte plain-text table to extract IDs. Context grows rapidly. If the tool were returning real production data, this would exhaust the context window.

**cli-good:** Returns page 1 (five items) as a `ResponseEnvelope` whose `meta.pagination` carries `total`, `has_more`, and `next_cursor`. The agent calls `list --cursor <token>` until `has_more` is `false` and extracts `data[].id` directly. Minimal context usage.

## CLI commands exercised

```bash
# bad
deployments list

# good
deployments list
# returns: {"ok":true,"data":[{"id":"deploy-001",...}],"meta":{"exit_code":0,"pagination":{"total":20,"has_more":true,"next_cursor":"cGFnZTI=",...}}}
deployments list --cursor cGFnZTI=
```

## Measured delta hypothesis

| Metric | Expected direction |
|--------|--------------------|
| `input_tokens` | bad >> good (table prose vs compact JSON) |
| `api_calls` | bad = good (but bad may retry on parse failure) |
| `steps` | bad >= good |
