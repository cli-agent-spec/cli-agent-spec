# link-cli — Fix Report

**Generated:** 2026-06-08
**CLI version:** 0.7.1
**Scope:** Critical
**In findings:** 22 failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1-2) | Fail (0) | Indeterminate (?) |
|---|---:|---:|---:|---:|
| Critical | 3 | 11 | 8 | 0 |
| High | 0 | 0 | 0 | 0 |
| Medium | 0 | 0 | 0 | 0 |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

### §1 — Exit Codes & Status Signaling  [Critical · 0/3]
**Gap:** Distinct failure classes all exit 1 and omit `exit_code`.
**Fix:** Define semantic exit codes, document them in help/manifest output, and include `exit_code` in JSON error bodies.

### §11 — Timeouts & Hanging Processes  [Critical · 0/3]
**Gap:** API calls have no general timeout flag or structured timeout error.
**Fix:** Add a global timeout option, emit `TIMEOUT` with a defined exit code, and include elapsed duration in metadata.

### §12 — Idempotency & Safe Retries  [Critical · 0/3]
**Gap:** Mutating commands lack idempotency and effect contracts.
**Fix:** Add `--idempotency-key` for create/update/cancel actions and return `effect` values such as `created`, `updated`, `canceled`, or `noop`.

### §13 — Partial Failure & Atomicity  [Critical · 0/3]
**Gap:** Multi-step flows can return pending states inside success output without partial/resume fields.
**Fix:** Return `partial`, `completed_steps`, `failed_step`, and `resume_command` or `resume_token` for incomplete flows.

### §23 — Side Effects & Destructive Operations  [Critical · 0/3]
**Gap:** No dry-run, danger metadata, or destructive confirmation contract.
**Fix:** Declare `danger_level` in schemas, add `--dry-run` for mutating/destructive commands, and return affected scope plus `effect`.

### §25 — Prompt Injection via Output  [Critical · 0/3]
**Gap:** External data is not separated from CLI metadata.
**Fix:** Wrap API/user/merchant content in a distinct `data` subtree with trust annotations or field-level provenance.

### §60 — OS Output Buffer Deadlock  [Critical · 0/3]
**Gap:** Long-running polling emits output only at process exit.
**Fix:** Emit line-delimited JSON heartbeat/status records during polling or expose a short-polling mode as the default agent path.

### §74 — Credential Scope Declaration Absence  [Critical · 0/3]
**Gap:** Schemas do not declare required scopes and there is no permissions preflight.
**Fix:** Add `required_scopes` to command manifest/schema output and a `check-permissions --for <command>` command.

### Score 1-2 Improvements

- Make `--format json` return the same envelope as `--full-output`, or auto-enable the envelope in non-TTY/CI contexts. (§2)
- Declare interactive requirements, GUI/headless behavior, sensitive fields, max output bytes, auth methods, and credential expiry fields in schema/manifest output. (§10, §37, §42, §43, §45, §53, §64)
- Add `AGENTS.md` with install, verify, auth-file, output-format, timeout, and retry guidance. (§71)
- Harden path-like fields such as `outputFile` against traversal and metacharacter surprises, and surface suggestions in validation errors. (§34)

## Already Passing

§50, §61, §62  _(score 3/3 — no action needed)_
