# dokploy — Trace

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: src/generated/commands.ts option handling; attempted validation path before API call`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
Generated commands pass Commander option values directly into opts and then apiGet/apiPost.
No validation rejects ../, %XX, ?, #, null bytes, or string literals before network calls.
```

**stderr** (first 20 lines):
```
```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
Top-level help lists API command groups only; no REPL, shell, console, or interactive command is present.
```

**stderr** (first 20 lines):
```
```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy auth -u http://127.0.0.1:9 -t secret-test-token`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Validating credentials...
Authentication failed: connect EPERM 127.0.0.1:9 - Local (0.0.0.0:0)
```

**stderr** (first 20 lines):
```
```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy project all --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Options expose --json only. No --max-output, --max-length, truncation metadata, or total byte metadata is documented.
```

**stderr** (first 20 lines):
```
```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy project all --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
No configuration found. Please run 'dokploy auth' first or set DOKPLOY_URL and DOKPLOY_AUTH_TOKEN environment variables.
```

**stderr** (first 20 lines):
```
```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: rg 'process.stdin|readline|prompt' src`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
No stdin-reading command paths found. Commands use flags and environment variables.
```

**stderr** (first 20 lines):
```
```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: src/client.ts and generated command catch behavior`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No CREDENTIALS_EXPIRED code, expired_at field, reauth_command, or distinct expiry exit code exists.
Axios errors are surfaced through the top-level catch as prose with process.exit(1).
```

**stderr** (first 20 lines):
```
```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: apiGet/apiPost and generated actions`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Commands await complete Axios responses and then print once.
No streaming, line-buffered JSON heartbeat, or heartbeat interval exists.
```

**stderr** (first 20 lines):
```
```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: rg 'process.stdin|stdin|input-file' src`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
No stdin payload command paths found.
```

**stderr** (first 20 lines):
```
```

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: rg 'EDITOR|VISUAL|spawn|exec' src`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
No editor-launching command paths found.
```

**stderr** (first 20 lines):
```
```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No browser/GUI launch commands or --open-browser style flags are listed.
```

**stderr** (first 20 lines):
```
```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `npm install -g @dokploy/cli --no-fund --no-audit`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
added 30 packages in 3s
Second install also exited 0.
dokploy --version => 0.3.0
```

**stderr** (first 20 lines):
```
```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy project all --json < /dev/null`
**Exit code:** 1
**Score:** 3/3

**stdout** (first 20 lines):
```
Command exits promptly with missing-config error; no prompt, pager, editor, or browser flow is triggered.
```

**stderr** (first 20 lines):
```
```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `DOKPLOY_URL=http://127.0.0.1:9 DOKPLOY_API_KEY=secret-test-token dokploy project all --json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
connect EPERM 127.0.0.1:9 - Local (0.0.0.0:0)
```

**stderr** (first 20 lines):
```
```

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy application create --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Options include resource fields and --json only; no --idempotency-key, effect field, or --dry-run is documented.
```

**stderr** (first 20 lines):
```
```

## §13 — Partial Failure & Atomicity
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: generated command output/error handling`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No partial:true, completed_steps, failed_step, resume token, per-item result, or rollback flag exists.
```

**stderr** (first 20 lines):
```
```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy application delete --help`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
Usage: dokploy application delete [options]
Options:
  --applicationId <value>  applicationId
  --json                   Output raw JSON
```

**stderr** (first 20 lines):
```
```

## §24 — Authentication & Secret Handling
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy auth --help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
Options:
  -u, --url <url>      Server URL (e.g., https://panel.dokploy.com)
  -t, --token <token>  API key from your Dokploy dashboard
```

**stderr** (first 20 lines):
```
```

## §25 — Prompt Injection via Output
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `source inspection: generated --json output branch`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
For --json, generated commands call console.log(JSON.stringify(data, null, 2)).
No ok/data/error envelope or trusted:false markers are added.
```

**stderr** (first 20 lines):
```
```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy --schema`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
error: unknown option '--schema'
```

**stderr** (first 20 lines):
```
```

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy project all --json; dokploy project one --projectId missing --json`
**Exit code:** 1
**Score:** 0/3

**stdout** (first 20 lines):
```
Both missing-config checks exit 1 with prose. Source contains process.exit(1) for top-level catch and auth/config failures.
No exit code table is documented.
```

**stderr** (first 20 lines):
```
```

## §2 — Output Format & Parseability
**Date:** 2026-05-26
**CLI version:** 0.3.0
**Check command:** `dokploy project all --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
error: unknown option '--output'
Generated API commands support --json, but errors are prose and successful raw JSON has no ok/data/error envelope.
```

**stderr** (first 20 lines):
```
```
