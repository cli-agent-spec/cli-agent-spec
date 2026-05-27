# Firecrawl CLI - Runtime Brief for Agents

**Generated:** 2026-05-27
**Binary:** `./node_modules/.bin/firecrawl`
**Version:** 1.18.1

## Invocation Rules

- Prefer `FIRECRAWL_API_KEY` in the environment over `--api-key` to avoid exposing secrets in process listings.
- Set `FIRECRAWL_NO_TELEMETRY=1`, `CI=true`, `NO_COLOR=1`, `PAGER=cat`, `EDITOR=true`, and `VISUAL=true` for every invocation.
- Always run Firecrawl under an external subprocess timeout.
- Do not rely on exit code 0 as success. Auth-required commands may exit 0 with a prompt.
- Do not assume `--json` is valid JSON until parsed. Auth and error paths can emit prose.
- Avoid `login --browser` in headless runs unless your wrapper extracts the URL and owns the timeout.

## Score Summary

| Bucket | Sections |
|---|---|
| Do not trust / 0 score | §1, §10, §12, §13, §23, §25, §43, §45, §53, §64, §74, §75 |
| Partial support | §2, §11, §24, §34, §42, §50, §60, §61, §71 |
| Indeterminate | §37, §62 |

## Output Checks

Before using any result, reject stdout that contains `Welcome! To get started`, `Enter choice`, `Opening browser for authentication`, `Error: Unauthorized`, or `error: unknown option`. Parse JSON only after confirming the whole stdout payload is valid JSON.
