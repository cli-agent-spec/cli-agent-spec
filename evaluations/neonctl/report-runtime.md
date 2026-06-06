# neonctl — Runtime Brief for Agents

**Version:** 2.22.2
**Binary:** `/Users/roman/.hermes/node/bin/neonctl`

## Always Include

```bash
--config-dir <isolated-temp-dir>
--no-analytics
--color false
```

For parseable output, request:

```bash
--output json
```

For credentials, prefer:

```bash
NEON_API_KEY=<token>
```

Use subprocess timeout on every call.

## Score Summary

| Score | Sections |
|---|---|
| 0/3 | §1, §10, §11, §12, §13, §23, §25, §43, §45, §50, §53, §64, §74, §75 |
| 1-2/3 | §2, §24, §34, §37, §42, §60, §71 |
| ?/3 | §61, §62 |
| 3/3 | None |

## Never Do

- Do not call `neonctl auth` unattended in a headless/non-TTY session.
- Do not run `neonctl init` without `--agent`.
- Do not pass high-value secrets as `--api-key` when `NEON_API_KEY` is available.
- Do not assume `--output json` makes error output JSON.
- Do not run delete/reset/restore commands without explicit user approval.
- Do not retry mutating commands blindly; no idempotency key or `effect` contract exists.

## Watch In Output

| Pattern | Meaning |
|---|---|
| `Authentication failed, deleting credentials...` | Auth failure can mutate credentials/config state. |
| `Awaiting authentication in web browser` | Command entered browser OAuth path and may hang. |
| `Not enough non-option arguments` | Common prose parser error; no structured validation body. |
| ANSI cursor sequences / spinner frames | Terminal UI output, not structured progress. |

## Preferred Workflows

Use `link --agent` for project linking because it returns a JSON state machine with a `status` discriminator.

Use `--config-dir` pointed at a temporary directory for every run. Remove the temp directory after the session if it may contain credentials.
