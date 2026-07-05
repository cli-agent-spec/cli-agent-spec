# neon - Issues Report

**Generated:** 2026-07-05
**CLI version:** 2.30.1
**Scope:** Critical
**Findings in scope:** 22 failure modes

## Observed Bugs

### §45 - browser OAuth blocks headless authenticated commands

**Discovered during:** §45 evaluation - 2026-07-05
**Symptom:** `neon projects list --output json` with an empty temporary config and stdin closed launched browser OAuth and did not exit before the 3 second probe timeout.
**Impact:** An agent blocks waiting for an out-of-band browser login and receives no parseable auth-required response.
**Trigger:** `/Users/roman/.hermes/node/bin/neon projects list --output json --config-dir tmp/neon-empty-config --context-file tmp/missing-neon-context --no-color --no-analytics`

### §64 - headless auth has no JSON URL fallback

**Discovered during:** §64 evaluation - 2026-07-05
**Symptom:** `neon auth` with `DISPLAY=` and stdin closed still launched browser OAuth and timed out.
**Impact:** Headless environments cannot recover programmatically; the URL is buried in stderr prose.
**Trigger:** `/Users/roman/.hermes/node/bin/neon auth --config-dir tmp/neon-auth-config --no-color --no-analytics`

### §10 - documented offline link path still triggers login

**Discovered during:** §10 evaluation - 2026-07-05
**Symptom:** `neon link --no-checks --org-id org-abc123 --project-id polished-snowflake-12345678 --no-env-pull --context-file tmp/neon-link-context` launched browser OAuth and timed out.
**Impact:** Agents cannot rely on the documented offline write path for CI or reproducible setup.
**Trigger:** `/Users/roman/.hermes/node/bin/neon link --no-checks --org-id org-abc123 --project-id polished-snowflake-12345678 --no-env-pull --context-file tmp/neon-link-context --no-color --no-analytics`

### §50 - documented stdin sentinel is parsed as a command

**Discovered during:** §50 evaluation - 2026-07-05
**Symptom:** `neon api /projects --data - --output json --api-key SECRET_CANARY_NEON_AUDIT_12345` exited with `ERROR: Unknown command: -`.
**Impact:** Agents following help text for stdin input hit an argument parser failure instead of a structured stdin contract.
**Trigger:** `/Users/roman/.hermes/node/bin/neon api /projects --data - --output json --api-key SECRET_CANARY_NEON_AUDIT_12345 --no-color --no-analytics`

### §2 - JSON output mode does not apply to error paths

**Discovered during:** §2 evaluation - 2026-07-05
**Symptom:** Commands run with `--output json` for missing arguments, invalid credentials, and validation errors emitted prose stderr and empty stdout.
**Impact:** Agent parsers must branch into brittle stderr parsing for common failures.
**Trigger:** `/Users/roman/.hermes/node/bin/neon projects get --output json --no-color --no-analytics`

### §1 - distinct failures collapse to exit code 1

**Discovered during:** §1 evaluation - 2026-07-05
**Symptom:** Invalid output value, missing required argument, and invalid API key probes all exited with code 1.
**Impact:** Agents cannot distinguish validation, auth, not-found, timeout, or permission failures from exit code alone.
**Trigger:** multiple probes; see [trace.md](trace.md)

## Failure-Mode Gaps

| Section | Score | What fails | Workaround exists |
|---|---:|---|---|
| §1 | 0/3 | No semantic exit-code table or JSON error body. | Partial |
| §10 | 0/3 | Non-TTY paths entered OAuth instead of suppressing prompts. | Partial |
| §11 | 0/3 | No general user-facing timeout or structured timeout response. | Partial |
| §12 | 0/3 | No idempotency-key or effect contract on mutating commands. | Partial |
| §13 | 0/3 | No partial-failure or resume contract for multi-step flows. | Partial |
| §23 | 0/3 | Destructive command help exposes no dry-run or affected scope preview. | Partial |
| §25 | 0/3 | External API content is not wrapped as untrusted data. | Partial |
| §37 | 0/3 | REPL-like `psql` path could not reach an interactive guard before auth. | Partial |
| §43 | 0/3 | No output truncation contract or max-output flag was found. | Partial |
| §45 | 0/3 | Browser OAuth blocks headless commands. | Partial |
| §64 | 0/3 | Headless auth lacks structured URL fallback. | Partial |
| §74 | 0/3 | No schema/manifest or permission scope declaration exists. | Partial |
| §2 | 1/3 | JSON mode exists but not for errors or envelopes. | Partial |
| §24 | 1/3 | Env auth exists, but `--api-key` accepts secrets in argv. | Partial |
| §34 | 1/3 | Validation is type/choice oriented, not structured hardening. | Partial |
| §42 | 1/3 | Canary not echoed, but no safe trace/schema sensitive-field contract. | Partial |
| §50 | 1/3 | Stdin sentinel failed as a parser error. | Partial |
| §61 | 1/3 | Large stdin failed early with no size-limit contract. | Partial |
| §71 | 2/3 | Install is documented and idempotent, but not in agent-specific docs. | Yes |
| §53 | ?/3 | Expired credential behavior was not safely mockable. | Partial |
| §60 | ?/3 | Long-running streaming behavior was not safely testable. | Partial |
| §62 | ?/3 | Editor behavior requires a live psql session. | Partial |

## Passing

None in the Critical scope.

## Risk Summary

| Category | Count | Sections |
|---|---:|---|
| Observed bugs | 6 | §1, §2, §10, §45, §50, §64 |
| Score 0 - complete failure | 12 | §1, §10, §11, §12, §13, §23, §25, §37, §43, §45, §64, §74 |
| Score 1 - major gap | 6 | §2, §24, §34, §42, §50, §61 |
| Score 2 - minor gap | 1 | §71 |
| Score 3 - passing | 0 | none |
| Indeterminate | 3 | §53, §60, §62 |

**Highest-risk combination:** headless browser auth, prose-only error handling, and absent machine-readable schema make naive agent integrations brittle unless they wrap Neon CLI defensively.
