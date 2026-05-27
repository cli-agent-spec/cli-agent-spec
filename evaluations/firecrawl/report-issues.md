# Firecrawl CLI - Issues Report

**Generated:** 2026-05-27
**Version:** 1.18.1
**Scope:** Critical

## Observed Bugs

See [issues.md](issues.md) for raw issue entries. The highest-impact confirmed issues are:

| Failure mode | Problem | Agent impact |
|---|---|---|
| §1 / §45 | Auth-required scrape exits 0 with a prompt | False success and prompt parsing risk |
| §2 | `--json` does not cover auth/error paths | JSON parsers fail or consume prose |
| §64 | Browser auth waits in headless mode | Requires external timeout and URL extraction |
| §13 | `init --skip-skills` reports skills installed | Agents cannot trust setup step status |
| §23 | `logout --dry-run` is unsupported | No side-effect preview path |

## Gaps By Severity

All evaluated rows are Critical. Failing rows need CLI-side fixes because wrappers cannot reliably infer semantics from prose output.

| Bucket | Count | Sections |
|---|---:|---|
| Failing 0/3 | 12 | §1, §10, §12, §13, §23, §25, §43, §45, §53, §64, §74, §75 |
| Partial 1-2/3 | 9 | §2, §11, §24, §34, §42, §50, §60, §61, §71 |
| Indeterminate | 2 | §37, §62 |

## Workaround Coverage

Most gaps have partial agent-side workarounds: enforce subprocess timeouts, set `FIRECRAWL_API_KEY` via environment, set `FIRECRAWL_NO_TELEMETRY=1`, avoid browser auth in headless runs, and treat any stdout prompt as failure even when exit code is 0. These workarounds do not replace a structured CLI contract.
