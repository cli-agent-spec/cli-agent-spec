# neonctl — Issues and Failure-Mode Gaps

**Date:** 2026-06-06
**Version:** 2.22.2

## Observed Bugs

### Browser auth blocks non-TTY execution

Tags: §45, §64, §10.

Trigger: `neonctl auth --config-dir <isolated> --no-analytics --color false`.

The command emitted an OAuth URL and waited beyond the timeout instead of exiting with a structured JSON fallback. Agents should avoid this command unless a human is present.

### `init` prompts under stdin=DEVNULL

Tags: §50, §10.

Trigger: `neonctl init --api-key <fake> --config-dir <isolated>`.

The command rendered an interactive editor-selection prompt and timed out. `--agent` is needed, but even `init --agent cursor` produced terminal UI and auth progress rather than a stable JSON contract.

### Invalid explicit API key can delete stored credentials

Tags: §24.

Trigger: `neonctl projects list --output json --api-key <fake>`.

The CLI printed that authentication failed and credentials were being deleted from the configured credentials path. When the fake key was passed through `--api-key`, deleting stored credentials is surprising and dangerous for agents.

### JSON mode does not cover common errors

Tags: §1, §2.

Trigger: `neonctl projects list --output json --api-key <fake> --config-dir <isolated>`.

stdout was empty and stderr contained prose messages. Agents still need text parsing for common failure paths.

### Progress output is terminal UI, not machine-readable heartbeat

Tags: §60.

Trigger: `neonctl init --agent cursor --api-key <fake> --config-dir <isolated>`.

Captured output contained spinner frames and ANSI cursor control. Agents should cap output and use timeouts.

## Gap Table

| § | Title | Score | Workaround exists |
|---|---|---:|---|
| §1 | Exit Codes & Status Signaling | 0/3 | Partial |
| §2 | Output Format & Parseability | 1/3 | Partial |
| §10 | Interactivity & TTY Requirements | 0/3 | Partial |
| §11 | Timeouts & Hanging Processes | 0/3 | Partial |
| §12 | Idempotency & Safe Retries | 0/3 | Partial |
| §13 | Partial Failure & Atomicity | 0/3 | Partial |
| §23 | Side Effects & Destructive Operations | 0/3 | Partial |
| §24 | Authentication & Secret Handling | 1/3 | Partial |
| §25 | Prompt Injection via Output | 0/3 | Partial |
| §34 | Shell Injection via Agent-Constructed Commands | 1/3 | Partial |
| §37 | REPL / Interactive Mode Accidental Triggering | 1/3 | Partial |
| §42 | Debug / Trace Mode Secret Leakage | 1/3 | Partial |
| §43 | Tool Output Result Size Unboundedness | 0/3 | Partial |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | 0/3 | Partial |
| §50 | Stdin Consumption Deadlock | 0/3 | Partial |
| §53 | Credential Expiry Mid-Session | 0/3 | Partial |
| §60 | OS Output Buffer Deadlock | 1/3 | Partial |
| §61 | Bidirectional Pipe Payload Deadlock | ?/3 | Unknown |
| §62 | $EDITOR and $VISUAL Trap | ?/3 | Unknown |
| §64 | Headless Display and GUI Launch Blocking | 0/3 | Partial |
| §71 | Non-Interactive Installation Absence | 2/3 | Yes |
| §74 | Credential Scope Declaration Absence | 0/3 | Partial |
| §75 | Safe-Default Execution Mode Absent | 0/3 | Partial |
