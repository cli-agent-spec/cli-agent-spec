# link-cli — Issues

### §1 candidate — semantic failures all exit 1
Validation errors, auth-required errors, unknown flags, network failures, and expired token failures all returned process exit code 1 with no `exit_code` field in the JSON body. Agents cannot branch reliably on the process status alone.
Discovered during §1 evaluation on 2026-06-08.

### §2 candidate — JSON mode is not consistently enveloped by default
`--format json` returns a bare array for successful commands and a bare object for errors. The consistent `ok`/`data`/`meta` envelope is available only when callers also know to pass `--full-output`.
Discovered during §2 evaluation on 2026-06-08.

### §11 candidate — API calls do not expose a command-level timeout
Authenticated API calls did not accept a general timeout flag. An unreachable API endpoint returned `UNKNOWN` rather than a structured `TIMEOUT` with a defined exit code.
Discovered during §11 evaluation on 2026-06-08.

### §13 candidate — polling timeout returns success with pending states
`auth login --interval 1 --timeout 2 --format json --full-output` exited 0 and returned a success envelope containing pending auth states, rather than a timeout/partial status that agents can branch on.
Discovered during §13 evaluation on 2026-06-08.

### §45 candidate — auth-required shape does not match machine-actionable auth schema
Auth-gated commands return `NOT_AUTHENTICATED` with a CTA command, but no `AUTH_REQUIRED` code, `auth_methods` array, or machine-readable declaration of supported credential mechanisms.
Discovered during §45 evaluation on 2026-06-08.

### §60 candidate — polling output is buffered until command exit
A Node spawn probe of `auth login --interval 1 --timeout 3 --format json` received the first stdout chunk after about five seconds, immediately before process exit, instead of incremental heartbeat/status output while the command was still running.
Discovered during §60 evaluation on 2026-06-08.
