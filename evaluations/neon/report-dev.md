# neon - Fix Report

**Generated:** 2026-07-05
**CLI version:** 2.30.1
**Scope:** Critical
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Indeterminate (?) |
|---|---:|---:|---:|---:|
| Critical | 0 | 7 | 12 | 3 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |

## Highest Priority Fixes

### §45 / §64 / §10 - Headless auth and interactivity

**Gap:** Unauthenticated commands launched browser OAuth and waited until killed. `link --no-checks`, expected to be offline, also entered auth.

**Fix:** In non-TTY or CI contexts, never start browser OAuth automatically. Return a structured JSON error with a stable code such as `AUTH_REQUIRED`, a list of auth methods, and the exact non-interactive next step. Ensure `--no-checks` truly performs no auth, API calls, or env pull.

### §1 / §2 - Error envelopes and exit codes

**Gap:** Validation, missing-argument, and auth failures collapsed to exit code 1 and prose stderr, even with `--output json`.

**Fix:** Make `--output json` apply to success and failure paths. Include `ok`, `data`, `error`, `warnings`, and `meta`, and embed `exit_code` plus a stable `error.code`. Publish the exit-code table in help and the manifest.

### §74 - Manifest and credential scopes

**Gap:** No schema/manifest command declares commands, flags, exit codes, required scopes, interactivity, or danger level.

**Fix:** Add `neon --manifest` or `neon --schema` returning a versioned JSON document with `commands`, typed `flags`, `exit_codes`, `required_scopes`, `requires_auth`, `requires_interactive`, and `danger_level`.

### §23 / §12 / §13 - Mutation safety contracts

**Gap:** Mutating/destructive workflows lack dry-run, idempotency, effect, partial-failure, and resume contracts.

**Fix:** Add `--dry-run` and `effect` to destructive operations, `--idempotency-key` to mutating operations, and structured `partial`, `completed_steps`, `failed_step`, and `resume_from` fields for multi-step flows.

### §50 / §61 - Stdin contract

**Gap:** `neon api --data -` is documented as stdin but was parsed as `Unknown command: -`.

**Fix:** Accept `--data -` and `--data=-` consistently, enforce a stdin size limit, and return structured `STDIN_REQUIRED` or `STDIN_TOO_LARGE` errors with file-based alternatives.

## Already Passing

None in the Critical scope.

## Could Not Verify

§53 Credential Expiry Mid-Session, §60 OS Output Buffer Deadlock, §62 $EDITOR and $VISUAL Trap. Treat these as unverified risk until they can be tested with a controlled credentialed environment.
