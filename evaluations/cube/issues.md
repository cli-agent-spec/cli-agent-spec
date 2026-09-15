# cube — Issues

### §42 candidate — `--token` exposes credentials in process listings
The documented `--token` flag places the credential verbatim in the process command line; the fake value `cli-visible-secret` was visible through `ps` while a request was active. Prefer `CUBE_API_KEY` for agent and CI use.
Discovered during §42 evaluation on 2026-08-06.

### §43 candidate — unbounded single-result output
`cube --json api GET /large` printed a 70 KiB field in full (71,748 stdout bytes) with no `meta.truncated`, total-size metadata, `--max-output`, or field-selection guard. A single API response can therefore overflow an agent context.
Discovered during §43 evaluation on 2026-08-06.

### §45 candidate — `--json` authentication failures are prose-only
With an isolated empty config and closed stdin, `cube --json whoami` failed promptly but wrote a human sentence to stderr and exited 1. It did not emit an `AUTH_REQUIRED` object or enumerate available headless authentication methods.
Discovered during §45 evaluation on 2026-08-06.

### §50 candidate — closed stdin is reported as malformed JSON
`cube api POST /mutate -d -` with stdin closed exits promptly, but reports an EOF parser failure instead of declaring that stdin input is required or suggesting `-d @file.json`/inline JSON.
Discovered during §50 evaluation on 2026-08-06.

### §53 candidate — expired credentials have no machine-readable identity
A mocked 401 yields useful prose (`session expired` and `cube login`) but still exits 1 and emits no `CREDENTIALS_EXPIRED`, `expired_at`, or `reauth_command` field. Agents must parse English text to distinguish expiry from other auth failures.
Discovered during §53 evaluation on 2026-08-06.

### §60 candidate — HTTP responses are fully buffered before output
A streaming mock response flushed one JSON fragment immediately and another three seconds later. Cube emitted nothing at the first observation point, then printed the entire document after completion. Long responses therefore provide no incremental progress or heartbeat.
Discovered during §60 evaluation on 2026-08-06.

### §61 candidate — stdin payloads have no declared or enforced size limit
Cube accepted a 70,014-byte JSON object from stdin and simultaneously returned 71,727 bytes. The run completed, but there was no size ceiling or overflow signal. Agents should switch to the supported `-d @file.json` form before large payloads reach the pipe.
Discovered during §61 evaluation on 2026-08-06.

### §64 candidate — login launches a browser and blocks in headless CI
With `CI=true`, closed stdin, isolated config, and `--json`, `cube login` still invoked the platform browser command and entered its authorization polling loop. The URL was emitted as ANSI-decorated prose, not a machine-readable headless fallback. A harmless local browser shim was used so no real GUI opened.
Discovered during §64 evaluation on 2026-08-06.

### §10 candidate — OAuth login ignores non-TTY execution
`cube login --url ...` with closed stdin and `CI=true` remained active beyond five seconds in its device-flow polling loop and required cancellation. There is no non-TTY guard or structured `INTERACTIVE_REQUIRED` failure; agents must avoid `login` and inject `CUBE_API_KEY` instead.
Discovered during §10 evaluation on 2026-08-06.

### §11 candidate — network operations have no user-configurable timeout
The global parser rejects `--timeout`. Against a localhost endpoint that withheld its response, Cube produced no output and remained active after three seconds until cancelled. There is no structured timeout, duration, heartbeat, or resume data.
Discovered during §11 evaluation on 2026-08-06.

### §12 candidate — mutating commands have no idempotency key
The `api` mutation path rejects `--idempotency-key`, and the global command surface exposes no equivalent. Agents cannot safely identify retries or distinguish a repeated creation from a noop without separately querying state.
Discovered during §12 evaluation on 2026-08-06.

### §13 candidate — deploy partial failures are not structured
A deliberately failed upload step showed useful prose progress and the failing endpoint, but `--json` emitted no JSON at all. The output does not say whether the upload transaction remains open, which steps completed, whether rollback is possible, or where a safe retry should resume.
Discovered during §13 evaluation on 2026-08-06.

### §23 candidate — destructive calls have no preview or confirmation contract
The raw API escape hatch rejects `--dry-run`, while an otherwise identical DELETE executes immediately without confirmation. The observed deletion was confined to the localhost mock; the production-facing command surface offers no machine-readable danger level or affected-scope preview.
Discovered during §23 evaluation on 2026-08-06.

### §25 candidate — external content is returned without trust boundaries
The raw API command emitted instruction-like user content as a normal `message` field alongside identifiers, with no envelope or `trusted: false` marker. Agents cannot distinguish CLI-owned metadata from untrusted external text without endpoint-specific knowledge.
Discovered during §25 evaluation on 2026-08-06.

### §74 candidate — minimum credential scopes are undiscoverable
Cube has no schema/manifest or `check-permissions` command, and its CLI documentation explains credential mechanisms without declaring the minimum permissions required by each command group. Agents cannot pre-flight least privilege or detect an over-privileged token.
Discovered during §74 evaluation on 2026-08-06.

### §1 candidate — runtime failures collapse to exit 1
Argument validation exits 2, but a not-found response and a connection failure both exit 1. The errors contain useful prose yet provide no documented semantic code or JSON `exit_code`, so retry and recovery policies must parse text.
Discovered during §1 evaluation on 2026-08-06.

### §2 candidate — `--json` does not define one success/error envelope
`cube --json regions` returned valid raw API JSON with no `ok`/`data`, while `cube --json api GET /missing` returned no JSON at all—only prose on stderr. Agent integrations need separate parsers for success and failure and cannot rely on one machine contract.
Discovered during §2 evaluation on 2026-08-06.
