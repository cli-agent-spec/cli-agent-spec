# dokploy — Issues

## Issue 1 — §1 §2 §45: `--json` does not produce structured auth/config errors

**Date:** 2026-05-26
**Trigger:** `dokploy project all --json`
**Observed:** exits 1 with prose: `No configuration found. Please run 'dokploy auth' first or set DOKPLOY_URL and DOKPLOY_AUTH_TOKEN environment variables.`
**Impact:** agents cannot reliably parse auth failure state, distinguish auth-required from other failures, or recover using a machine-readable `auth_methods` field.

## Issue 2 — §2: documented raw JSON mode is `--json`, not `--output json`, and errors remain prose

**Date:** 2026-05-26
**Trigger:** `dokploy project all --output json`
**Observed:** exits 1 with `error: unknown option '--output'`.
**Impact:** agents expecting a conventional output-format flag fail before reaching the API command, and there is no consistent envelope across success and failure paths.

## Issue 3 — §23: destructive commands lack preview or confirmation controls

**Date:** 2026-05-26
**Trigger:** `dokploy application delete --help`
**Observed:** options are only `--applicationId`, `--json`, and help.
**Impact:** an agent cannot safely preview affected scope or force an explicit destructive confirmation before deleting resources.

## Issue 4 — §24 §42: secrets are accepted through command-line arguments

**Date:** 2026-05-26
**Trigger:** `dokploy auth --help`; source scan of generated commands
**Observed:** `auth` requires `-t, --token <token>`, and generated commands include sensitive flags such as `--password`, `--apiKey`, `--sshPrivateKey`, and `--token`.
**Impact:** secrets can appear in shell history, process listings, and agent transcripts.

## Issue 5 — §11 §53: network/auth failures are untyped prose with exit 1

**Date:** 2026-05-26
**Trigger:** `DOKPLOY_URL=http://127.0.0.1:9 DOKPLOY_API_KEY=secret-test-token dokploy project all --json`
**Observed:** exits 1 with prose `connect EPERM 127.0.0.1:9 - Local (0.0.0.0:0)`.
**Impact:** agents cannot distinguish timeout, sandbox/network failure, expired credentials, or permission denial from a generic command failure.

## Issue 6 — version identity mismatch

**Date:** 2026-05-26
**Trigger:** `npm list -g @dokploy/cli --depth=0` and `dokploy --version`
**Observed:** npm reports `@dokploy/cli@0.29.4`; the binary reports `0.3.0`.
**Impact:** agents cannot reliably correlate installed binary behavior with package releases, docs, or generated API surface.
