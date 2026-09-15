# resend — Fix Report

**Generated:** 2026-07-06
**CLI version:** resend-cli v2.8.1
**Scope:** Critical
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | 4 | 12 | 5 | 1 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |

---

## Required Fixes

### Highest Priority

| §N | Score | Gap | Recommended fix |
|---|---:|---|---|
| §1 | 0/3 | All failures exit 1 and JSON lacks numeric `exit_code`. | Add semantic exit codes and include `exit_code` in every error body. |
| §25 | 0/3 | External/user content is returned as ordinary JSON fields. | Mark external fields with `trusted:false` or wrap them in a dedicated `external_data` envelope. |
| §43 | 0/3 | Dry-run can emit large file contents without truncation metadata. | Add `--max-output`/`--fields` and emit `meta.truncated` plus `meta.total_bytes`. |
| §64 | 0/3 | Browser commands call the OS opener even with `--quiet`/`--json`. | In headless/JSON/quiet mode, return `{ "url": "...", "opened": false }` and skip the opener. |
| §74 | 0/3 | No command-level credential-scope declaration. | Extend `resend commands` with `required_scopes` and add a `check-permissions` preflight. |

### Next Fixes

| §N | Score | Gap | Recommended fix |
|---|---:|---|---|
| §2 | 1/3 | JSON envelopes vary by command. | Standardize on `ok`, `data`, `error`, `warnings`, and `meta` for all commands. |
| §11 | 1/3 | Timeout behavior is internal and not caller-controlled. | Add `--timeout` and emit a dedicated `TIMEOUT` code with duration metadata. |
| §12 | 1/3 | Idempotency only covers send/batch. | Add idempotency/effect contracts to all mutating commands. |
| §13 | 1/3 | No resume/rollback information for partial failures. | Emit per-item results, `completed_steps`, and `resume_from` where relevant. |
| §23 | 1/3 | Destructive commands have `--yes` but no dry-run/danger metadata. | Add dry-run previews and `danger_level` to command metadata. |
| §24 | 1/3 | Secret-bearing flags are accepted. | Prefer env/file secret inputs and make `whoami` distinguish present vs validated credentials. |
| §34 | 1/3 | File flags accept traversal-like paths. | Reject `../`, percent-encoding, null bytes, and URL metacharacters where inappropriate. |
| §45 | 1/3 | Auth errors lack `auth_methods`. | Return `AUTH_REQUIRED`/`AUTH_EXPIRED` with actionable methods and reauth hints. |
| §50 | 1/3 | Stdin parse errors lack stdin-specific hints. | Emit `STDIN_REQUIRED` or `STDIN_INVALID` with the exact flag/file alternative. |
| §60 | 1/3 | Long-running commands have no heartbeat. | Emit JSON heartbeat lines with elapsed time and current step. |
| §61 | 1/3 | Large stdin has no size guard. | Enforce stdin byte limits and provide `--file` hints for large payloads. |
| §42 | 2/3 | No debug leakage observed, but no sensitive schema/trace-safe mode. | Mark sensitive fields in command metadata and keep debug output redacted by construction. |

## Already Passing

§10, §37, §62, §71 _(score 3/3 — no action needed)_

## Could Not Verify

§53 _(credential expiry behavior could not be reproduced without an expired credential)_
