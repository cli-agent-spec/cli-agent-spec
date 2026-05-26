# dokploy — Concrete Issues and Gaps

**Generated:** 2026-05-26  
**CLI version:** 0.3.0

## Observed Bugs

### 1. `--json` does not produce structured auth/config errors

- Trigger: `dokploy project all --json`
- Observed: prose missing-config message, exit 1
- Impact: agents cannot distinguish auth-required from other failures without brittle text matching.
- Related modes: §1, §2, §45

### 2. Conventional `--output json` is unsupported

- Trigger: `dokploy project all --output json`
- Observed: `error: unknown option '--output'`, exit 1
- Impact: agents using common CLI conventions fail before reaching the API command.
- Related mode: §2

### 3. Destructive commands lack safe preview controls

- Trigger: `dokploy application delete --help`
- Observed: only `--applicationId`, `--json`, and help are available.
- Impact: agents cannot inspect affected scope or do a no-op validation before deletion.
- Related mode: §23

### 4. Secrets are accepted through argv

- Trigger: `dokploy auth --help` and generated command source scan
- Observed: `--token`, `--password`, `--apiKey`, `--sshPrivateKey`, and similar flags are accepted.
- Impact: secrets can leak into process listings, shell history, and agent transcripts.
- Related modes: §24, §42

### 5. Network/auth failures are untyped prose

- Trigger: `DOKPLOY_URL=http://127.0.0.1:9 DOKPLOY_API_KEY=secret-test-token dokploy project all --json`
- Observed: prose connection error, exit 1
- Impact: agents cannot separate timeout, credential expiry, permission denial, and network failure.
- Related modes: §11, §53

### 6. Binary version and package version disagree

- Trigger: `npm list -g @dokploy/cli --depth=0`; `dokploy --version`
- Observed: package `0.29.4`, binary `0.3.0`
- Impact: agents cannot map behavior to release notes or generated docs reliably.

## Gap Table

| Mode | Gap | Workaround Exists |
|---|---|---|
| §1 | No semantic exit code table; generic exit 1 failures. | Partial |
| §11 | No CLI timeout flag or structured timeout error. | Partial |
| §12 | No idempotency key or effect field. | Partial |
| §23 | No dry-run/confirm-destructive contract. | Partial |
| §43 | No max-output or truncation metadata. | Partial |
| §74 | No schema with required scopes. | No |
