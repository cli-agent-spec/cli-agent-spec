# S5 — Bulk Delete with Dry-Run

**Challenge cluster:** Destructive operations, partial failure, dry-run
**Key requirements:** C-002, C-004, C-008, C-009, O-021

## Task given to agent

> "Delete all staging deployments older than 30 days. Make sure nothing production is touched."

## Expected answer

3 staging deployments deleted (`deploy-021`, `deploy-034`, `deploy-041`). No production resources affected.

## Why this stresses the spec

**cli-bad:** The delete command has no `--dry-run` flag. The agent must either proceed blindly (risking production deletion if its filter is wrong) or refuse and ask for human confirmation. If it proceeds and the filter is wrong, there is no partial failure report — just `exit 1` with no indication of what was deleted before the error.

**cli-good:** The agent calls `deployments delete --filter "env=staging,age>30d" --dry-run --format json` first, verifying the target set. Then calls with `--yes` to confirm. If the bulk delete partially fails mid-way, the response exits `3` with `data.summary` and per-item `data.results[]` (REQ-C-009) so the agent knows exactly what state was reached.

## CLI commands exercised

```bash
# bad
deployments delete --filter "env=staging,age>30d"
# no dry-run; no step manifest; exit 1 on partial failure with no detail

# good
deployments delete --filter "env=staging,age>30d" --dry-run --format json
# returns: {"ok":true,"data":{"effect":"would_delete","would_affect":{"deployments":[{"id":"deploy-021",...},...]}}}
deployments delete --filter "env=staging,age>30d" --yes --format json
# returns: {"ok":true,"data":{"effect":"deleted","summary":{"total":3,"succeeded":3,"failed":0},"results":[{"id":"deploy-021","ok":true},...]}}
```

## Measured delta hypothesis

| Metric | Expected direction |
|--------|--------------------|
| `total_tokens` | bad > good (agent deliberation on safety vs structured dry-run) |
| `api_calls` | bad > good (extra reasoning calls before committing) |
| `success` | bad < good (agent may refuse or corrupt state) |
| `steps` | bad > good |
