# REQ-O-033: --headless and --token-env-var Flags for Auth Commands

**Tier:** Opt-In | **Priority:** P0

**Source:** [§45 Headless Authentication / OAuth Browser Flow Blocking](../challenges/01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

Any command that performs authentication MUST support `--headless` and `--token-env-var <VAR_NAME>` flags (automatically registered by the framework for commands with `auth: true` in their metadata). When `--headless` is passed, the command MUST skip any browser redirect and instead check the environment variable named by `--token-env-var` (or the default token env vars declared in REQ-C-021). If `--headless` is active and no token is found, the command MUST exit with code 4 and a structured error listing the expected env var name and how to populate it. When stdin is not a TTY, `--headless` behavior MUST be the default.

## Acceptance Criteria

- `command login --headless --token-env-var MY_TOKEN` reads `MY_TOKEN` from environment without opening a browser
- `command login --headless` without a token exits with code 4, listing the expected env var
- In non-TTY mode, browser auth is suppressed automatically (equivalent to `--headless`)
- `--token-env-var` accepts any valid env var name; the framework reads that variable's value as the token

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

On headless auth failure, the error includes `auth_methods[]` listing available non-browser authentication methods and their required env var names.

---

## Wire Format

```bash
$ tool auth login --headless --token-env-var MY_TOKEN --format json
```

Success:

```json
{
  "ok": true,
  "data": { "logged_in": true, "user": "alice@example.com" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 312 }
}
```

Headless failure (token not found):

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Headless auth requires MY_TOKEN environment variable",
    "auth_methods": [{ "type": "env_var", "name": "MY_TOKEN", "hint": "Set MY_TOKEN to your API token" }]
  },
  "warnings": [],
  "meta": { "exit_code": 8, "duration_ms": 12 }
}
```

---

## Example

Opt-in: automatically available on commands that declare `auth: true`.

```
register command "auth login":
  auth: true   # --headless and --token-env-var are auto-registered

# Agent authenticates without browser:
$ tool auth login --headless --token-env-var TOOL_API_TOKEN

# Non-TTY: headless is the automatic default
$ echo "" | tool auth login --token-env-var TOOL_API_TOKEN
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-021](c-021-auth-commands-declare-headless-mode-support.md) | C | Provides: command-level headless mode declaration this requirement enforces |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Provides: non-TTY detection that activates headless mode automatically |
| [REQ-F-057](f-057-headless-environment-detection-and-gui-suppression.md) | F | Composes: framework-level headless detection complements command-level auth flags |
