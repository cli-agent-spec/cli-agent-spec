# langfuse — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | 2026-05-22 | CLI appears to pass arguments without shell execution, but encoded slash, traversal, query, fragment, and literal `null` prompt names are accepted into curl-preview URLs rather than rejected with structured validation. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 | 2026-05-22 | No REPL/shell/interactive subcommand or flag was exposed in help output; non-TTY help paths exit immediately. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | 2026-05-22 | No debug mode was found and curl preview redacts Basic auth, but secret values are accepted as CLI flags and no sensitive-field schema exists. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | 2026-05-22 | Read commands expose `--limit`/`--fields` on some endpoints, but there is no `--max-output`, truncation envelope, `meta.truncated`, or preflight output-size declaration. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | 2026-05-22 | Missing credentials exit quickly, but errors are unstructured beyond `ok:false,error` and do not include `AUTH_REQUIRED` or `auth_methods`. |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 | 2026-05-22 | No stdin-reading fallback was found; missing required arguments fail immediately with usage output instead of blocking. |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 | 2026-05-22 | Could not test without a real expired Langfuse credential; command surface does not expose a distinct expiry code or reauth command. |
| §60 | OS Output Buffer Deadlock | Critical | ?/3 | 2026-05-22 | Could not test without a long-running streaming command; no heartbeat or streaming contract is documented. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 | 2026-05-22 | No command accepting large stdin payloads was found, so the bidirectional pipe deadlock pattern is not exposed. |
| §62 | `$EDITOR` and `$VISUAL` Trap | Critical | 3/3 | 2026-05-22 | No editor-requiring command was found. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 | 2026-05-22 | No GUI/browser-opening command was found; auth uses environment variables/flags rather than browser OAuth. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | 2026-05-22 | README documents non-interactive npm/npx install paths and local reinstall is idempotent; no `AGENTS.md` install contract and `--version` prints help rather than a parseable CLI version. |
| §10 | Interactivity & TTY Requirements | Critical | 3/3 | 2026-05-22 | Non-TTY invocations tested did not hang; missing auth and missing args exit immediately. |
| §11 | Timeouts & Hanging Processes | Critical | 1/3 | 2026-05-22 | Unreachable-host test exited quickly with JSON error, but there is no `--timeout`, defined timeout code, duration metadata, or heartbeat/resume support. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | 2026-05-22 | Mutating commands expose no visible `--idempotency-key`, `effect`, or universal `--dry-run` contract. |
| §13 | Partial Failure & Atomicity | Critical | ?/3 | 2026-05-22 | Could not safely trigger a multi-step mid-run API failure without credentials and side effects; no resume/rollback/partial fields are visible in help/schema. |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 | 2026-05-22 | Destructive trace delete commands expose no `--dry-run`, machine-readable `danger_level`, confirmation flag, or affected-scope preview. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | 2026-05-22 | Env vars are supported and curl preview masks Basic auth, but secrets are accepted via CLI args and auth failures use generic exit 1 without a defined auth error code. |
| §25 | Prompt Injection via Output | Critical | 0/3 | 2026-05-22 | API data is returned in a generic `data` envelope with no `trusted:false`, content-type annotation, or structural distinction for untrusted user/API content. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | 2026-05-22 | No manifest or schema includes `required_scopes`; no `check-permissions` command or over-privilege warning was found. |
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-05-22 | Missing args, unknown commands, auth failures, validation failures, and network failures all collapse to exit 1; exit codes are not documented or included in JSON errors. |
| §2 | Output Format & Parseability | Critical | 1/3 | 2026-05-22 | `api __schema --json` and API auth failures can emit JSON, but parser/validation errors ignore `--json` and print prose usage; top-level `--json` prints help and exits 0. |
