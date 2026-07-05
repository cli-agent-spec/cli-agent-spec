# neon - Issues

### §45 candidate - browser OAuth blocks headless authenticated commands
`neon projects list --output json` with an empty temporary config and stdin closed launched browser OAuth, printed an auth URL, and did not exit before the 3 second probe timeout. An agent cannot recover from this without an out-of-band browser login.
Discovered during §45 evaluation on 2026-07-05.

### §64 candidate - headless auth has no JSON URL fallback
`neon auth` with `DISPLAY=` and stdin closed still launched the browser OAuth path and timed out. The command did not emit a structured JSON response containing the URL and next action.
Discovered during §64 evaluation on 2026-07-05.

### §10 candidate - documented offline link path still triggers login
`neon link --no-checks --org-id org-abc123 --project-id polished-snowflake-12345678 --no-env-pull --context-file tmp/neon-link-context` launched browser OAuth and timed out, despite the README describing `--no-checks` as an offline write with no API calls.
Discovered during §10 evaluation on 2026-07-05.

### §50 candidate - documented stdin sentinel is parsed as a command
`neon api /projects --data - --output json --api-key SECRET_CANARY_NEON_AUDIT_12345` exited with `ERROR: Unknown command: -` instead of treating `-` as stdin as documented by `neon api --help`.
Discovered during §50 evaluation on 2026-07-05.

### §2 candidate - JSON output mode does not apply to error paths
Commands run with `--output json` for missing arguments, invalid API keys, and validation errors emitted prose to stderr and empty stdout instead of a parseable JSON error envelope.
Discovered during §2 evaluation on 2026-07-05.

### §1 candidate - distinct failures collapse to exit code 1
Invalid output value, missing required positional argument, and invalid API key probes all exited with code 1 and no documented semantic error code in the output body.
Discovered during §1 evaluation on 2026-07-05.
