# link-cli — Trace

## §1 — Exit Codes & Status Signaling
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli spend-request retrieve --format json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid input: expected string, received undefined\n\nDetails: ...",
  "fieldErrors": [
    {
      "code": "invalid_type",
      "missing": true,
      "path": "id"
    }
  ]
}
```

**stderr** (first 20 lines):
```

```

Additional probes: `payment-methods list` without auth, `auth logout --dry-run`, invalid expired token, and network failure all also exited 1 and omitted `exit_code`.

## §2 — Output Format & Parseability
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli auth status --format json`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```json
[
  {
    "authenticated": false,
    "credentials_path": "/Users/roman/Documents/Link-cli/source/tmp/link-auth.json"
  }
]
```

**stderr** (first 20 lines):
```

```

`--full-output` produced an envelope, but the check without that extra flag did not.

## §10 — Interactivity & TTY Requirements
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `perl -e 'alarm 5; exec @ARGV' link-cli demo --format json`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```json
{
  "code": "REQUIRES_TTY",
  "message": "The demo command requires an interactive terminal."
}
```

**stderr** (first 20 lines):
```

```

`onboard` behaved the same way. `auth login --format json` emitted a verification URL and `_next` without opening a browser.

## §11 — Timeouts & Hanging Processes
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_ACCESS_TOKEN=<future-exp-token> LINK_NO_REFRESH=1 LINK_API_BASE_URL=http://127.0.0.1:1 link-cli user-info retrieve --format json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "Request failed: GET http://127.0.0.1:1/userinfo"
}
```

**stderr** (first 20 lines):
```

```

No general API timeout flag, `TIMEOUT` code, or timeout-specific exit code was available.

## §12 — Idempotency & Safe Retries
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli spend-request create --schema | rg -i 'idempotency|dry|effect'`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```

```

The mutating create schema has no idempotency key, effect field, or dry-run support.

## §13 — Partial Failure & Atomicity
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-login-timeout.json link-cli auth login --client-name AgentAudit --interval 1 --timeout 2 --format json --full-output`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```json
{
  "ok": true,
  "data": [
    {
      "verification_url": "https://app.link.com/device/setup?code=...",
      "instruction": "Present the verification_url to the user and ask them to approve in the Link app. Polling has started automatically — no further action needed."
    },
    {
      "authenticated": false,
      "pending": true
    }
  ],
  "meta": {
    "command": "auth login",
    "duration": "3428ms"
  }
}
```

**stderr** (first 20 lines):
```

```

No `partial`, `completed_steps`, `failed_step`, resume token, or timeout failure status was present.

## §23 — Side Effects & Destructive Operations
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli auth logout --dry-run --format json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "Unknown flag: --dry-run"
}
```

**stderr** (first 20 lines):
```

```

No `danger_level`, `effect`, or destructive confirmation metadata was found in command schemas.

## §24 — Authentication & Secret Handling
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_ACCESS_TOKEN=agent-audit-secret-token LINK_NO_REFRESH=1 link-cli user-info retrieve --format json`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "Access token expired. Update LINK_ACCESS_TOKEN and retry."
}
```

**stderr** (first 20 lines):
```

```

The token value was not echoed. Auth configuration is available through env vars and auth file paths.

## §25 — Prompt Injection via Output
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli --llms-full`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```markdown
# link-cli

## link-cli auth
...
### link-cli spend-request retrieve
```

**stderr** (first 20 lines):
```

```

External API/user content returned by list/retrieve commands is modeled as ordinary response fields; no trusted/untrusted annotations or external-content wrappers were found in schema/help.

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli spend-request create --schema | rg -i 'outputFile|path|traversal|agent_hardening'`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
    outputFile:
```

**stderr** (first 20 lines):
```

```

Structured flags are used, but path-like arguments have no schema-level traversal/metacharacter hardening declaration.

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `perl -e 'alarm 5; exec @ARGV' link-cli onboard --format json`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```json
{
  "code": "REQUIRES_TTY",
  "message": "The onboard command requires an interactive terminal."
}
```

**stderr** (first 20 lines):
```

```

The command exits immediately in non-TTY mode; schemas do not declare `requires_interactive`.

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli auth status --token agent-audit-secret-token --debug --format json`
**Exit code:** 1
**Score:** 2/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "Unknown flag: --token"
}
```

**stderr** (first 20 lines):
```

```

No debug/trace or token CLI flag is accepted, and the supplied token value was not echoed.

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli auth status --format json --full-output --token-limit 5`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```json
{
  "ok": true,
  "data": "[\n  {\n    \"authenticated\"\n[truncated: showing tokens 0–5 of 37]",
  "meta": {
    "command": "auth status",
    "duration": "103ms",
    "nextOffset": 5
  }
}
```

**stderr** (first 20 lines):
```

```

Truncation exists, but not as `meta.truncated: true` plus `meta.total_bytes`.

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-auth.json link-cli payment-methods list --format json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{
  "code": "NOT_AUTHENTICATED",
  "message": "Not authenticated. Run \"link-cli auth login\" first.",
  "cta": {
    "description": "Suggested command:",
    "commands": [
      {
        "command": "link-cli auth login",
        "description": "Log in to Link"
      }
    ]
  }
}
```

**stderr** (first 20 lines):
```

```

No hang or browser launch occurred, but `auth_methods` was absent and the code was not `AUTH_REQUIRED`.

## §50 — Stdin Consumption Deadlock
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `perl -e 'alarm 4; exec @ARGV' link-cli user-info retrieve --format json`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "EPERM: operation not permitted, mkdir '/Users/roman/Library/Preferences/link-cli-nodejs'"
}
```

**stderr** (first 20 lines):
```

```

The probed command exited immediately and did not read from stdin. The ordinary CLI command tree does not expose stdin-required payload commands.

## §53 — Credential Expiry Mid-Session
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_ACCESS_TOKEN=agent-audit-secret-token LINK_NO_REFRESH=1 link-cli user-info retrieve --format json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{
  "code": "UNKNOWN",
  "message": "Access token expired. Update LINK_ACCESS_TOKEN and retry."
}
```

**stderr** (first 20 lines):
```

```

The error text mentions expiry, but the structured code is not `CREDENTIALS_EXPIRED` and no `reauth_command` is present.

## §60 — OS Output Buffer Deadlock
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `node -e "<spawn link-cli auth login --interval 1 --timeout 3 and log stdout chunk timestamps>"`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
STDOUT 5064 884 "[\n  {\n    \"verification_url\": \"https://app.link.com/device/setup?code=relent-lik"
EXIT 5086 0 null
```

**stderr** (first 20 lines):
```

```

The first stdout chunk arrived at about 5064 ms, just before process exit, so polling updates were buffered until completion.

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli --llms-full | rg -i 'stdin|input-file|data|payload'`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
| `--data` | `string` |  | Request body (implies POST if --method is not set) |
```

**stderr** (first 20 lines):
```

```

The ordinary CLI surface uses flags such as `--data`; no stdin payload path was found.

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli --llms-full | rg -i 'editor|visual|edit'`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```

```

No editor-requiring command was found.

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `LINK_AUTH_FILE=tmp/link-login.json link-cli auth login --client-name AgentAudit --format json`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```json
[
  {
    "verification_url": "https://app.link.com/device/setup?code=...",
    "phrase": "...",
    "instruction": "Present the verification_url to the user and ask them to approve in the Link app. Then call `auth status --interval 5 --max-attempts 60` to poll until authenticated. Do not wait for the user to reply — start polling immediately.",
    "_next": {
      "command": "auth status --interval 5 --max-attempts 60"
    }
  }
]
```

**stderr** (first 20 lines):
```

```

The URL is emitted in output instead of opening a browser; schema lacks GUI/headless declarations.

## §71 — Non-Interactive Installation Absence
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `npm install -g @stripe/link-cli --no-fund --no-audit`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
changed 144 packages in 12s
```

**stderr** (first 20 lines):
```

```

The install command is documented in README and the second run exited 0. No `AGENTS.md` install/verify command exists.

## §74 — Credential Scope Declaration Absence
**Date:** 2026-06-08
**CLI version:** 0.7.1
**Check command:** `link-cli --llms-full | rg -i 'required_scopes|scope|check-permissions|active_scopes|over_privileged'`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```

```

**stderr** (first 20 lines):
```

```

No required-scope declarations or check-permissions command were found.
