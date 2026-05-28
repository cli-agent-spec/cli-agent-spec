# Runtime Brief — omd

**Generated:** 2026-05-28
**CLI version:** `omd 0.1.1`

## Use

```bash
./target/debug/omd <command> --output json
```

Set:

```bash
OMD_HOST=<server-url>
OMD_TOKEN=<jwt>
```

## Score Summary

| Bucket | Failure modes |
|---|---|
| Passing | §10, §25, §37, §62 |
| Partial | §1, §2, §11, §12, §13, §23, §24, §34, §42, §45, §50, §53, §60, §61, §64, §71 |
| Failing | §43, §74 |
| Indeterminate | none |

## Always Do

| Rule | Reason |
|---|---|
| Pass `--output json` on every command. | Most successful paths return a parseable envelope. |
| Use `--schema` before dynamic commands. | Schema includes typed options and capabilities. |
| Use `--dry-run` before mutations. | Mutation previews are structured and avoid side effects. |
| Apply an outer subprocess timeout. | CLI timeout errors are not yet typed as `TIMEOUT`. |
| Limit captured stdout in the agent runtime. | CLI has no output-size cap. |

## Watch In Output

| Pattern | Meaning |
|---|---|
| `GENERAL_ERROR` after a network wait | May be a timeout despite the generic code. |
| `AUTH_REQUIRED` plus text mentioning expired token | Treat as expired credentials and reauth. |
| Multiple JSON objects on stdout | Parse all envelopes; auth status can emit two. |
| Prose on stderr | Invocation errors can bypass JSON even with `--output json`. |

## Never Do

- Do not rely on schema for credential scopes; `required_scopes` is absent.
- Do not send unbounded output directly into an LLM context.
- Do not put long-lived secrets in shell history when `OMD_TOKEN` or `--token-env-var` can be used.
