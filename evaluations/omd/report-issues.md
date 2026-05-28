# Concrete Issues — omd

**Generated:** 2026-05-28
**CLI version:** `omd 0.1.1`

## Observed Bugs

| Issue | Trigger | Impact |
|---|---|---|
| Invocation errors bypass JSON | `./target/debug/omd patch --output json` | Agents requesting JSON receive clap prose on stderr and no JSON stdout. |
| Timeout taxonomy collapses to `GENERAL_ERROR` | `./target/debug/omd search orders --host http://127.0.0.1:<hanging-port> --timeout 1 --output json` | Agents cannot distinguish timeout from non-retryable general failure. |
| Auth status can emit two JSON envelopes | `./target/debug/omd auth status --host http://localhost:8585 --token invalid-secret-value --output json` | Agents may parse the first `ok: true` envelope and miss the later auth failure. |
| Required scopes are absent | `./target/debug/omd search --schema` | Agents cannot select minimally scoped credentials from the machine-readable interface. |

## Gap Table

| Failure mode | Score | Gap |
|---|---:|---|
| §43 Tool Output Result Size Unboundedness | 0/3 | No truncation metadata or output cap. |
| §74 Credential Scope Declaration Absence | 0/3 | No `required_scopes` or permission report. |
| §11 Timeouts & Hanging Processes | 1/3 | Timeout maps to `GENERAL_ERROR`. |
| §53 Credential Expiry Mid-Session | 1/3 | Expiry not represented as a distinct structured code. |
| §23 Side Effects & Destructive Operations | 1/3 | Dry-run lacks affected scope, danger level, and `effect`. |
| §1 Exit Codes & Status Signaling | 1/3 | JSON errors omit `exit_code`; invocation errors can bypass the envelope. |
