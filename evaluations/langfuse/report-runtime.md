# Langfuse CLI — Runtime Brief for Agents

**Binary:** `./node_modules/.bin/langfuse`  
**Timeout:** enforce externally with subprocess timeout

## Use

```sh
./node_modules/.bin/langfuse api __schema --json
./node_modules/.bin/langfuse api <resource> --help
./node_modules/.bin/langfuse api <resource> <action> --help
./node_modules/.bin/langfuse api <resource> <action> --json
./node_modules/.bin/langfuse api <resource> <action> --curl
```

## Always Set

- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST` or `LANGFUSE_BASE_URL`
- subprocess timeout
- stdin closed or redirected from `/dev/null`

## Never Assume

- Exit code `1` identifies the failure type.
- `--json` applies to parser/usage errors.
- Delete/create commands are idempotent.
- Destructive commands have a dry-run mode.
- Large API responses are truncated safely.
- Credential scopes are discoverable from the CLI.

## Watch For

| Pattern | Meaning |
|---|---|
| `missing required argument` | Validation failure, not JSON even with `--json`. |
| `unknown command` | Parser failure, not JSON even with `--json`. |
| `Missing --username for basic auth` | Missing credentials/auth mapping issue. |
| `fetch failed` | Ambiguous network/auth/server failure. |

## Score Summary

Failing: §43, §12, §23, §25, §74, §1  
Partial: §34, §42, §45, §71, §11, §24, §2  
Passing: §37, §50, §61, §62, §64, §10  
Indeterminate: §53, §60, §13
