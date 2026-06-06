# neonctl — Issues

## §45 / §64 / §10 — Browser auth blocks non-TTY execution

**Date:** 2026-06-06
**Command:** `neonctl auth --config-dir <isolated> --no-analytics --color false`
**Observed:** The command emitted `Awaiting authentication in web browser` and an OAuth URL, then did not exit within the subprocess timeout. The output was prose on stderr, not a JSON `AUTH_REQUIRED` or `headless_behavior` response.
**Impact:** Agents can hang during auth and cannot parse a structured fallback or token/API-key instruction.

## §50 / §10 — `init` prompts under stdin=DEVNULL

**Date:** 2026-06-06
**Command:** `neonctl init --api-key <fake> --config-dir <isolated>`
**Observed:** The command rendered an interactive editor-selection prompt and timed out under `stdin=DEVNULL`.
**Impact:** Agents can block unless they know to pass `--agent`, and the CLI does not fail fast with a structured non-interactive error.

## §24 — Invalid auth deletes configured credentials

**Date:** 2026-06-06
**Command:** `neonctl projects list --output json --api-key <fake> --no-analytics --color false`
**Observed:** The CLI printed `Authentication failed, deleting credentials...` and referenced the default credentials file path. This happened even though the failing credential came from the explicit `--api-key` option.
**Impact:** A bad per-invocation API key can affect stored user credentials, creating cross-session state contamination and recovery work for agents.

## §2 / §1 — JSON mode does not apply to common errors

**Date:** 2026-06-06
**Command:** `neonctl projects list --output json --api-key <fake> --config-dir <isolated>`
**Observed:** stdout was empty and stderr contained prose auth messages; exit code was `1`.
**Impact:** Agents requesting JSON still need stderr text parsing for common failure paths.

## §60 — Progress output uses terminal control sequences

**Date:** 2026-06-06
**Command:** `neonctl init --agent cursor --api-key <fake> --config-dir <isolated>`
**Observed:** Captured output included spinner frames and ANSI cursor-control sequences while the command remained running.
**Impact:** Agents receive noisy, token-heavy terminal UI instead of structured heartbeats.
