# neon - Trace

## §34 - Shell Injection via Agent-Constructed Commands
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects create --name acme%2Fwidgets --output ../../etc/test --no-color --no-analytics`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
ERROR: Invalid values:
  Argument: output, Given: "../../etc/test", Choices: "json", "yaml", "table"
```

## §37 - REPL / Interactive Mode Accidental Triggering
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon psql --output json --config-dir tmp/neon-empty-config --context-file tmp/missing-neon-context --no-color --no-analytics` with stdin closed and 3s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...response_type=code
```

## §42 - Debug / Trace Mode Secret Leakage
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects list --output json --api-key SECRET_CANARY_NEON_AUDIT_12345 --config-dir tmp/neon-empty-config --context-file tmp/missing-neon-context --no-color --no-analytics`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Authentication failed, deleting credentials...
INFO: Authentication failed, deleting credentials...
```

## §43 - Tool Output Result Size Unboundedness
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `rg -n "meta\\.truncated|total_bytes|max-output|max-length" /Users/roman/.hermes/node/lib/node_modules/neon/README.md /Users/roman/.hermes/node/lib/node_modules/neon/dist`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
```

## §45 - Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects list --output json --config-dir tmp/neon-empty-config --context-file tmp/missing-neon-context --no-color --no-analytics` with stdin closed and 3s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...response_type=code
```

## §50 - Stdin Consumption Deadlock
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon api /projects --data - --output json --api-key SECRET_CANARY_NEON_AUDIT_12345 --no-color --no-analytics`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
ERROR: Unknown command: -
```

## §53 - Credential Expiry Mid-Session
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `Could not safely mock expired Neon credentials without a real credential/session`
**Exit code:** n/a
**Score:** ?/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Indeterminate: invalid API key produced prose auth failure, but this is not equivalent to an expired credential.
```

## §60 - OS Output Buffer Deadlock
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `No safe credential-free long-running Neon command was available after login-triggering probes were stopped`
**Exit code:** n/a
**Score:** ?/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Indeterminate: exact long-running streaming behavior was not exercised.
```

## §61 - Bidirectional Pipe Payload Deadlock
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon api /projects --data - --output json --api-key SECRET_CANARY_NEON_AUDIT_12345 --no-color --no-analytics` with 70KB stdin
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
ERROR: Unknown command: -
[probe stdin error: EPIPE]
```

## §62 - $EDITOR and $VISUAL Trap
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `Static inspection found editor paths in embedded psql, but no credential-free editor-requiring command could be executed`
**Exit code:** n/a
**Score:** ?/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Indeterminate: exercising the editor path requires a live psql session.
```

## §64 - Headless Display and GUI Launch Blocking
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon auth --config-dir tmp/neon-auth-config --no-color --no-analytics` with DISPLAY empty, stdin closed, and 3s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...response_type=code
```

## §71 - Non-Interactive Installation Absence
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `npm install -g neon --no-fund --no-audit` followed by `/Users/roman/.hermes/node/bin/neon --version`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
changed 123 packages in 2s
2.30.1
```

**stderr** (first 20 lines):
```
```

## §10 - Interactivity & TTY Requirements
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon link --no-checks --org-id org-abc123 --project-id polished-snowflake-12345678 --no-env-pull --context-file tmp/neon-link-context --no-color --no-analytics` with stdin closed and 3s timeout
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Awaiting authentication in web browser.
INFO: Auth Url: https://oauth2.neon.tech/oauth2/auth?...response_type=code
```

## §11 - Timeouts & Hanging Processes
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `Static scan plus no-credential auth probes`
**Exit code:** 124
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
No user-facing --timeout flag was found. No-credential auth probes exceeded the external 3s timeout without a CLI-produced structured timeout response.
```

## §12 - Idempotency & Safe Retries
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `rg -n "idempotency|idempotency-key|effect" /Users/roman/.hermes/node/lib/node_modules/neon/README.md /Users/roman/.hermes/node/lib/node_modules/neon/dist`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
```

## §13 - Partial Failure & Atomicity
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `rg -n "partial|completed_steps|failed_step|resume|rollback" /Users/roman/.hermes/node/lib/node_modules/neon/README.md /Users/roman/.hermes/node/lib/node_modules/neon/dist`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Several incidental source references to partial parsing/results were found, but no CLI response contract for partial: true, completed_steps, failed_step, or resume token was found.
```

**stderr** (first 20 lines):
```
```

## §23 - Side Effects & Destructive Operations
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects delete --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
neon projects delete <id>
Delete a project
Global options include --output, --config-dir, --api-key, --color, --analytics, --help, --version.
Options include --context-file only.
```

**stderr** (first 20 lines):
```
```

## §24 - Authentication & Secret Handling
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects list --output json --api-key SECRET_CANARY_NEON_AUDIT_12345 --config-dir tmp/neon-empty-config --context-file tmp/missing-neon-context --no-color --no-analytics`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
INFO: Authentication failed, deleting credentials...
INFO: Authentication failed, deleting credentials...
```

## §25 - Prompt Injection via Output
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `Static inspection of output mode and api passthrough behavior`
**Exit code:** n/a
**Score:** 0/3

**stdout** (first 20 lines):
```
No `trusted: false`, external-data envelope, or prompt-injection protection marker was found. The `api` command is an authenticated passthrough for external API responses.
```

**stderr** (first 20 lines):
```
```

## §74 - Credential Scope Declaration Absence
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon --schema`, `/Users/roman/.hermes/node/bin/neon manifest`, and static scan for `required_scopes`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
--schema returned ordinary help, manifest returned ERROR: Unknown command: manifest, and no required_scopes/check-permissions contract was found.
```

**stderr** (first 20 lines):
```
```

## §1 - Exit Codes & Status Signaling
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `invalid output value, missing required arg, and invalid API key probes`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
invalid output value: exit 1
missing required arg: exit 1
invalid API key: exit 1
No JSON error body or documented semantic exit code table was observed.
```

## §2 - Output Format & Parseability
**Date:** 2026-07-05
**CLI version:** 2.30.1
**Check command:** `/Users/roman/.hermes/node/bin/neon projects get --output json --no-color --no-analytics`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
ERROR: Not enough non-option arguments: got 0, need at least 1
```
