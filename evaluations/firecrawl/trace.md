# firecrawl - Trace


## §1 - Exit Codes & Status Signaling
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `missing required, network, and auth failure probes`
**Exit code:** search -> 1; search local API -> 1; scrape without auth -> 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
error: missing required argument query; Error: connect ECONNREFUSED 127.0.0.1:1; auth prompt printed to stdout
```

**stderr** (first 20 lines):
```text
Failures collapse to exit 1, auth-required scrape exits 0 after printing a prompt, and no JSON error body carries exit_code.
```


## §2 - Output Format & Parseability
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl search firecrawl --json` without credentials`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```text
stdout was a human login prompt, not JSON
```

**stderr** (first 20 lines):
```text
Several commands expose --json, but auth and error paths emit prose/prompts or stderr text without ok/data/error envelope.
```


## §10 - Interactivity & TTY Requirements
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl config` and `firecrawl login --browser` with stdin closed`
**Exit code:** 0 / 124 external timeout
**Score:** 0/3

**stdout** (first 20 lines):
```text
config printed prompt; browser login waited for authentication
```

**stderr** (first 20 lines):
```text
config/scrape print an interactive auth prompt under stdin=/dev/null; login --browser waits for browser auth until external timeout.
```


## §11 - Timeouts & Hanging Processes
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl search "agent cli audit" --api-url http://127.0.0.1:1 --timeout 2000 --json``
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
Error: connect ECONNREFUSED 127.0.0.1:1
```

**stderr** (first 20 lines):
```text
search/crawl expose timeout flags, but connection failure returns prose stderr and exit 1, not structured TIMEOUT metadata.
```


## §12 - Idempotency & Safe Retries
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `help scan for --idempotency-key/effect/dry-run on mutating commands`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
No idempotency key or effect contract found
```

**stderr** (first 20 lines):
```text
No --idempotency-key support or effect field found on mutating/setup commands.
```


## §13 - Partial Failure & Atomicity
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl init -y --skip-install --skip-auth --skip-skills``
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
Reported Skills installed despite --skip-skills; no completed_steps/failed_step/resume token
```

**stderr** (first 20 lines):
```text
Multi-step init has no structured completed_steps, failed_step, resume token, or rollback support; --skip-skills run still reported skills installed.
```


## §23 - Side Effects & Destructive Operations
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl logout --dry-run``
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```text
error: unknown option --dry-run
```

**stderr** (first 20 lines):
```text
logout rejects --dry-run; setup/init/logout expose side effects without dry-run, machine-readable danger_level, or effect fields.
```


## §24 - Authentication & Secret Handling
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl scrape https://example.com --api-key fc-SECRET-12345 --json``
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
Error: Unauthorized: Invalid token; tested token was not echoed
```

**stderr** (first 20 lines):
```text
FIRECRAWL_API_KEY is supported and invalid-key errors did not echo the tested value, but --api-key accepts secrets on the command line and auth prompts are prose.
```


## §25 - Prompt Injection via Output
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `help/docs scan plus unauthenticated --json probe`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
No trusted/untrusted external content envelope found
```

**stderr** (first 20 lines):
```text
External scrape/search content is not wrapped in a trusted/untrusted envelope; single-format outputs are raw content and no trusted:false metadata is advertised.
```


## §34 - Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl scrape --name acme%2Fwidgets --output ../../etc/test --api-url http://127.0.0.1:1``
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
error: unknown option --name; no structured VALIDATION_ERROR/suggestion
```

**stderr** (first 20 lines):
```text
Unknown --name was rejected, but rejection is prose only; --output accepts arbitrary paths and no structured VALIDATION_ERROR/suggestion exists.
```


## §37 - REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `REPL/shell subcommand discovery`
**Exit code:** not run
**Score:** ?/3

**stdout** (first 20 lines):
```text
No REPL or shell subcommand found
```

**stderr** (first 20 lines):
```text
No REPL or shell subcommand was found to run the specified check; no schema exists to declare requires_interactive.
```


## §42 - Debug / Trace Mode Secret Leakage
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl scrape https://example.com --token fc-SECRET-12345 --debug``
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```text
error: unknown option --token; tested token was not echoed
```

**stderr** (first 20 lines):
```text
--token/--debug are rejected without echoing the tested token, but --api-key secrets are accepted as CLI args and no trace-safe/schema sensitivity metadata exists.
```


## §43 - Tool Output Result Size Unboundedness
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `help/docs scan for output limits`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
No --max-output/--max-length or truncation metadata found
```

**stderr** (first 20 lines):
```text
No --max-output/--max-length limit or meta.truncated/meta.total_bytes contract is documented or exposed in help.
```


## §45 - Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl scrape https://example.com` without credentials`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
Exited 0 with auth prompt rather than AUTH_REQUIRED JSON
```

**stderr** (first 20 lines):
```text
Unauthenticated commands print a login prompt to stdout and exit 0; browser login waits for auth instead of returning structured AUTH_REQUIRED/auth_methods.
```


## §50 - Stdin Consumption Deadlock
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl config` with stdin closed`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```text
Prompt text emitted; no STDIN_REQUIRED JSON or hint
```

**stderr** (first 20 lines):
```text
Non-TTY auth prompts return promptly, but no STDIN_REQUIRED structured error or hint is emitted.
```


## §53 - Credential Expiry Mid-Session
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `invalid credential probe`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```text
Unauthorized prose only; no expiry/permission distinction
```

**stderr** (first 20 lines):
```text
Invalid credentials return prose Unauthorized text only; no CREDENTIALS_EXPIRED/PERMISSION_DENIED distinction or reauth_command field was found.
```


## §60 - OS Output Buffer Deadlock
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl login --browser` long-running auth wait`
**Exit code:** 124 external timeout
**Score:** 1/3

**stdout** (first 20 lines):
```text
Progress text emitted, no JSON heartbeat
```

**stderr** (first 20 lines):
```text
Long-running browser auth emits progress text but no JSON heartbeat, elapsed_ms, or step metadata.
```


## §61 - Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `70KB stdin piped to `firecrawl view-config``
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```text
Command ignored stdin and exited; no STDIN_TOO_LARGE enforcement
```

**stderr** (first 20 lines):
```text
A 70KB stdin payload to view-config exited, but no stdin size limit, STDIN_TOO_LARGE error, --input-file alternative, or schema declaration exists.
```


## §62 - $EDITOR and $VISUAL Trap
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `editor-requiring command discovery`
**Exit code:** not run
**Score:** ?/3

**stdout** (first 20 lines):
```text
No editor-requiring Firecrawl subcommand found
```

**stderr** (first 20 lines):
```text
No editor-requiring Firecrawl subcommand was found to run the specified check; no schema exists to declare requires_editor or alternatives.
```


## §64 - Headless Display and GUI Launch Blocking
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl login --browser` with DISPLAY unset`
**Exit code:** 124 external timeout
**Score:** 0/3

**stdout** (first 20 lines):
```text
Auth URL printed, then waited for browser auth
```

**stderr** (first 20 lines):
```text
login --browser emits a URL but then waits for browser authentication and timed out in headless/non-TTY execution.
```


## §71 - Non-Interactive Installation Absence
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `local `npm install firecrawl-cli --no-fund --no-audit` rerun and `firecrawl --version``
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```text
Install was idempotent; version output 1.18.1
```

**stderr** (first 20 lines):
```text
README/docs document non-interactive npm/npx install and local npm install was idempotent; no AGENTS.md verify command makes this a 3/3.
```


## §74 - Credential Scope Declaration Absence
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** ``firecrawl --schema`, `firecrawl manifest``
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```text
--schema shows help/error; manifest is unknown command
```

**stderr** (first 20 lines):
```text
No --schema/manifest/check-permissions command and no per-command required_scopes declaration were found.
```


## §75 - Safe-Default Execution Mode Absent
**Date:** 2026-05-27
**CLI version:** 1.18.1
**Check command:** `help scan for safe_default/dry-run/live/effect`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```text
No safe-default execution contract found
```

**stderr** (first 20 lines):
```text
No safe_default manifest, --live contract, dry-run default, or meta.dry_run/effect output exists for side-effecting commands.
```
