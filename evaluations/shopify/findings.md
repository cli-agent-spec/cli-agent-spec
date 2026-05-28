# shopify — Findings

| Failure mode | Title | Severity | Score | Notes |
|---|---|---|---|---|
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 | Oclif flags are typed, but path/name hardening is not declared and no structured validation rejects traversal/metacharacter payloads. |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 0/3 | `shopify theme console` under non-TTY did not exit within 3s and emitted prose release notes before being killed. |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 1/3 | Secret-bearing `--password` flags are accepted; tested verbose output did not echo the fake credential but no framework-level sensitive schema or safe trace mode is exposed. |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 | `shopify commands --json` emitted 7,528 lines with no `meta.truncated`, `total_bytes`, default cap, or `--max-output` control. |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 0/3 | `shopify auth login` in non-TTY printed a device-code URL and kept running until terminated; no structured `AUTH_REQUIRED` response. |
| §50 | Stdin Consumption Deadlock | Critical | 0/3 | Interactive stdin-consuming path (`theme console`) blocked under non-TTY instead of returning a structured `STDIN_REQUIRED` error. |
| §53 | Credential Expiry Mid-Session | Critical | ?/3 | Could not evaluate without an expiring authenticated Shopify session; no manifest-level expiry/error contract was discoverable. |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 | Long-running interactive commands provide no JSON heartbeat or line-buffered progress contract; tested `theme console` blocked after prose release notes. |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 1/3 | Some commands expose file alternatives such as `--query-file`, but no stdin size limit or `STDIN_TOO_LARGE` structured error is declared. |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 | No editor-launching Shopify command was found in the command inventory or help probes, so this trap surface was not present. |
| §64 | Headless Display and GUI Launch Blocking | Critical | 1/3 | Browser/GUI-oriented commands exist (`auth login`, `theme open`); headless behavior is prose output or blocking flow, not JSON URL emission with schema declarations. |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 | Non-interactive npm install is documented and idempotent, and `shopify --version` verifies; no `AGENTS.md` install/verify contract exists. |
| §10 | Interactivity & TTY Requirements | Critical | 0/3 | Auth and REPL paths block or wait in non-TTY; no universal `--non-interactive`/`--yes` flag or automatic structured failure. |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 | No generic `--timeout`, JSON timeout error, defined timeout exit code, heartbeat interval, or resume token was found. |
| §12 | Idempotency & Safe Retries | Critical | 0/3 | Mutating commands do not expose `--idempotency-key`, universal `--dry-run`, or `effect` fields in structured responses. |
| §13 | Partial Failure & Atomicity | Critical | 0/3 | Multi-step commands do not expose structured `completed_steps`, `failed_step`, `partial`, resume tokens, or rollback flags. |
| §23 | Side Effects & Destructive Operations | Critical | 1/3 | Destructive commands prompt and may support `--force`, but no `--dry-run`, machine-readable `danger_level`, or `effect` output is present. |
| §24 | Authentication & Secret Handling | Critical | 1/3 | Env var alternatives exist, but `--password` is accepted; errors are prose and no structured auth code/secret redaction contract is declared. |
| §25 | Prompt Injection via Output | Critical | 0/3 | External API/file/user content is not wrapped in a trusted/untrusted envelope distinct from CLI metadata. |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 | No `--schema`/manifest required-scope declaration or `check-permissions` machine-readable preflight exists. |
| §1 | Exit Codes & Status Signaling | Critical | 1/3 | Validation uses exit 2 and many runtime failures use exit 1, but exit codes are undocumented and absent from JSON error bodies. |
| §2 | Output Format & Parseability | Critical | 1/3 | JSON output exists for command inventory and some commands, but there is no consistent `ok`/`data`/`error` envelope and prose notifications/errors can pollute output. |
