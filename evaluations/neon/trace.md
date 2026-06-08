# neonctl — Trace

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-06-06
**CLI version:** 2.22.2
**Check command:** `neonctl auth --config-dir tmp/neonctl-config --no-analytics --color false` with `stdin=DEVNULL`, 6s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
[empty]
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...
```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-06-06
**CLI version:** 2.22.2
**Check command:** `neonctl init --api-key <fake> --config-dir tmp/neonctl-config` with `stdin=DEVNULL`, 6s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
Adding Neon MCP server, extension (for VS Code and Cursor) and agent skills
Which editor(s) would you like to configure? (Space to toggle each option, Enter to confirm your selection)
```

**stderr** (first 20 lines):
```
[empty]
```

## §24 — Authentication & Secret Handling
**Date:** 2026-06-06
**CLI version:** 2.22.2
**Check command:** `neonctl projects list --output json --api-key <fake> --config-dir tmp/neonctl-config --no-analytics --color false`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
[empty]
```

**stderr** (first 20 lines):
```
INFO: Authentication failed, deleting credentials...
INFO: Authentication failed, deleting credentials...
```

## §2 — Output Format & Parseability
**Date:** 2026-06-06
**CLI version:** 2.22.2
**Check command:** `neonctl link --agent --project-id proj_bad --org-id org_bad --api-key <fake> --config-dir tmp/neonctl-config --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
{
  "status": "error",
  "code": "AUTH_ERROR",
  "message": "supplied credentials do not pass authentication"
}
```

**stderr** (first 20 lines):
```
[empty]
```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-06-06
**CLI version:** 2.22.2
**Check command:** `neonctl init --agent cursor --api-key <fake> --config-dir tmp/neonctl-config` with 8s timeout
**Exit code:** 124
**Score:** 1/3

**stdout** (first 20 lines):
```
Adding Neon extension (includes MCP server) and agent skills for Cursor
Authenticating
Authenticating.
Authenticating..
Authenticating...
[spinner/control sequences omitted]
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...
INFO: Auth complete
```
