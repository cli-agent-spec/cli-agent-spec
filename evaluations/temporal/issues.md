# temporal — Issues

### §2 candidate — `--output json` does not apply to validation failures
`temporal --output json workflow start` without required flags prints usage text to stdout and prose errors to stderr.
Discovered during §2 evaluation on 2026-07-07.
Impact: Agents expecting JSON must switch parsers on failure and can accidentally ingest usage text as data.

### §11 candidate — Timeout-like network failures collapse to exit 1 and prose
An unroutable server with 2s command/client timeouts exits 1 with `Error: program interrupted`.
Discovered during §11 evaluation on 2026-07-07.
Impact: Agents cannot distinguish timeout, cancellation, and other failures from the exit code or JSON body.

### §23 candidate — Destructive commands lack dry-run/effect contracts
`workflow delete --dry-run` is rejected as an unknown flag, and query deletes require `--yes` but return only a batch job ID.
Discovered during §23 evaluation on 2026-07-07.
Impact: An agent cannot get a machine-readable would-delete scope or distinguish created/noop/effect outcomes.

### §74 candidate — No machine-readable credential scope declaration
`--schema`, `manifest`, and `check-permissions` probes all fail as unknown.
Discovered during §74 evaluation on 2026-07-07.
Impact: Agents cannot select minimally scoped credentials before invocation.
