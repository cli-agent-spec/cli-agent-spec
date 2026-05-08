# gh — Findings

| Failure mode | Title | Severity | Score | Date | Notes |
|---|---|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 | 2026-05-07 | HTTP 404 and 401 both exit 0; `gh issue view <nonexistent>` exits 0; documented exit 4 for auth not emitted on invalid token |
| §2 | Output Format & Parseability | Critical | 2/3 | 2026-05-07 | `--json` works and returns valid JSON; no response envelope (`ok`/`error`/`meta`); JSON not auto-activated in non-TTY |
| §8 | ANSI & Color Code Leakage | High | 3/3 | 2026-05-07 | `NO_COLOR=1 TERM=dumb` fully suppresses ANSI; 0 escape sequences in output |
| §10 | Interactivity & TTY Requirements | Critical | 2/3 | 2026-05-07 | No hang with stdin=DEVNULL; `GH_PAGER=cat` suppresses pager; `GH_PROMPT_DISABLED=1` disables prompts; no `--non-interactive` flag |
| §11 | Timeouts & Hanging Processes | Critical | 2/3 | 2026-05-07 | Completes within 10s timeout; no built-in timeout flag or env var documented; no structured timeout exit code |
| §12 | Idempotency & Safe Retries | Critical | 1/3 | 2026-05-07 | No idempotency guarantees documented; create commands offer no `--idempotency-key`; write-permission check skipped (can't write to cli/cli) |
| §43 | Tool Output Result Size Unboundedness | Critical | 2/3 | 2026-05-07 | Default `--limit 30` on list commands; no JSON pagination metadata (`next_page`, `total_count` missing from envelope) |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 | 2026-05-07 | Uses stored credentials silently (good); invalid token exits 0 with human-readable error, not exit 4; no `AUTH_REQUIRED` JSON error |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 | 2026-05-07 | Does not read stdin silently; piped input ignored correctly |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 | 2026-05-07 | `GH_TOKEN=invalid` → HTTP 401, exits 0 (should be exit 4); error is plain text, no JSON structure; no machine-readable auth method hint |
| §60 | OS Output Buffer Deadlock | Critical | 3/3 | 2026-05-07 | Piped stdout completes normally; 460 bytes returned without hang |
| §62 | $EDITOR and $VISUAL Trap | Critical | 2/3 | 2026-05-07 | Editor bypassed when `--title` and `--body` provided; not documented for agents; `gh issue create` without --body triggers editor |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 | 2026-05-07 | `gh browse --no-browser` prints URL to stdout instead of launching browser; exit 0 |
