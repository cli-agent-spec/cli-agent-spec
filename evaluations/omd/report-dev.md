# CLI Author Fix Report — omd

**Generated:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Scope:** 22 Critical CLI Agent Spec failure modes

`omd` has a strong agent-first base: non-TTY JSON output, schema introspection, dry-run previews, MCP mode, packaged skills, and prompt-injection tagging. The main work is tightening the machine-readable contracts around failures, auth, output limits, and credential scope.

## Priority Fixes

| Priority | Failure mode | Current score | Fix |
|---|---|---:|---|
| P0 | §74 Credential Scope Declaration Absence | 0/3 | Add `required_scopes` to every command in `--schema`; add `omd check-permissions --for <command>` returning `required_scopes`, `active_scopes`, and `over_privileged`. |
| P0 | §43 Tool Output Result Size Unboundedness | 0/3 | Add default output caps, `--max-output-bytes`, and truncation metadata (`meta.truncated`, `meta.total_bytes`, per-field `_truncated`). |
| P1 | §1 Exit Codes & Status Signaling | 1/3 | Route clap/invocation errors through the JSON envelope when JSON is requested or non-TTY; include `exit_code` in JSON errors and expose an exit-code table in schema/help. |
| P1 | §11 Timeouts & Hanging Processes | 1/3 | Map request timeouts to a dedicated `TIMEOUT` code and timeout exit code; mark `retryable: true` where appropriate. |
| P1 | §53 Credential Expiry Mid-Session | 1/3 | Emit `CREDENTIALS_EXPIRED` with `expired_at`, `reauth_command`, and a distinct exit code. |
| P1 | §45 Headless Authentication | 1/3 | Include `auth_methods` in auth-required errors and `requires_auth`/`auth_methods` in schema. |
| P2 | §23 Destructive Operations | 1/3 | Add `danger_level`, affected scope, and `effect: would_delete` to dry-run mutation output. |
| P2 | §12 Idempotency | 1/3 | Return `effect` (`created`, `updated`, `noop`) from mutating operations and document retry semantics. |

## Preserve

- Keep the non-TTY SSO guard; it prevented browser launch deadlocks.
- Keep `--schema`, scoped schemas, and command capabilities.
- Keep `_source: external` / `_trusted: false` tagging and the `--no-injection-protection` escape hatch.
- Keep same-package MCP and bundled skill artifacts.

## Acceptance Checks

Run these after fixes:

```bash
./target/debug/omd patch --output json
./target/debug/omd search orders --host http://127.0.0.1:<hanging-port> --timeout 1 --output json
./target/debug/omd search --schema | jq '.data.commands.search.required_scopes'
./target/debug/omd check-permissions --for search --output json
./target/debug/omd --skills --skills-content --max-output-bytes 4096
```
