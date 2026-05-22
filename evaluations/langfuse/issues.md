# langfuse — Issues

## §1, §2 — `--json` is not honored for parser and validation errors

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api traces get --json`
**Observed:** Missing required arguments and unknown commands print prose usage output and exit 1 even when `--json` is supplied.
**Impact:** Agents cannot reliably parse failure responses. They must special-case Commander/specli usage text separately from API JSON errors.

## §1 — Error exit codes collapse to generic `1`

**Date:** 2026-05-22
**Trigger:** missing argument, unknown command, invalid flag value, missing auth, and network failure checks.
**Observed:** All tested failures exited with code 1.
**Impact:** Agents cannot distinguish validation, auth, not-found, timeout/network, or parser failures from exit status alone.

## §45, §24 — Missing-auth errors do not declare auth methods or semantic code

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api healths list --json`
**Observed:** Output was `{"ok":false,"error":"Missing --username for basic auth"}`.
**Impact:** Agents do not receive `AUTH_REQUIRED`, `auth_methods`, required environment variables, or a reauth/setup command in machine-readable form.

## §23 — Destructive operations lack dry-run or machine-readable danger metadata

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api traces delete-public --help`
**Observed:** Delete commands expose `--curl` and `--json`, but no `--dry-run`, confirmation flag, `danger_level`, or affected-scope preview.
**Impact:** Agents cannot safely preview destructive API effects before execution.

## §12 — Mutating commands lack idempotency contract

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api datasets create --help`
**Observed:** Create commands do not expose `--idempotency-key`, `effect`, or retry/noop semantics.
**Impact:** Retrying after a network failure can create duplicate resources unless the agent performs its own preflight state checks.

## §43 — No output truncation contract for large API responses

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api traces list --help`
**Observed:** Some endpoints expose `--limit` and `--fields`, but there is no universal `--max-output`, `meta.truncated`, or `total_bytes`.
**Impact:** A large trace/session/prompt payload can consume excessive agent context without an explicit truncation signal.

## §74 — No credential scope declaration

**Date:** 2026-05-22
**Trigger:** `./node_modules/.bin/langfuse api __schema --json`
**Observed:** Schema output lists auth schemes and resources, but no per-command `required_scopes` or permission preflight.
**Impact:** Agents cannot choose minimally scoped credentials or detect over-privileged credentials.
