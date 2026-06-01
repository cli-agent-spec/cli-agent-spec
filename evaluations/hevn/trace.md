# hevn — Trace

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn account get --name acme%2Fwidgets --output ../../etc/test --json`
**Exit code:** 2
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Usage: hevn account get [OPTIONS]
Try 'hevn account get --help' for help.
No such option: --name Did you mean --yaml?
```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn --help`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
Commands: login, logout, mcp-key, deposit, pending-deposits, rate, bills, hire, status, balance, agent-skill, contacts, account, profile, invoice, contracts, contractors, transfer, cards, banks.
No REPL or shell subcommand found.
```

**stderr** (first 20 lines):
```
```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn --token supersecret-token-value --debug`
**Exit code:** 2
**Score:** 2/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Usage: hevn [OPTIONS] COMMAND [ARGS]...
No such option: --token Did you mean --env?
```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn --help; inspect command flags`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No --max-output, --max-length, meta.truncated, or total_bytes contract found in help or installed sources.
```

**stderr** (first 20 lines):
```
```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn login --timeout 10 --no-open --json`
**Exit code:** 2
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Open this URL to authorize HEVN CLI: https://app.gethevn.com/cli-auth?port=51923&state=...
Usage: hevn login [OPTIONS]
Invalid value: Timed out waiting for callback on port 51923
```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn mcp-key --json < /dev/null`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
MCP key:
```

**stderr** (first 20 lines):
```
GetPassWarning: Can not control echo on the terminal.
Warning: Password input may be echoed.
Aborted.
```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn status --json`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
{
  "environment": "prod",
  "jwt": {"configured": false, "expiresAt": null},
  "error": "JWT is not configured. Run `hevn login` first or set HEVN_API_KEY."
}
```

**stderr** (first 20 lines):
```
```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn login --timeout 10 --no-open --json`
**Exit code:** 2
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Auth URL emitted once; no JSON heartbeat or progress events while waiting.
```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `inspect stdin-reading commands and help`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
mcp-key can read a secret from stdin/prompt; no stdin max byte contract or --input-file alternative found.
```

**stderr** (first 20 lines):
```
```

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn --help; inspect installed sources for EDITOR/VISUAL`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No editor-requiring command found.
```

**stderr** (first 20 lines):
```
```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `inspect login implementation`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
login calls webbrowser.open(auth_url) unless --no-open is passed; no schema-declared headless fallback.
```

**stderr** (first 20 lines):
```
```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `pip install hevn-cli --quiet --no-input; hevn --version`
**Exit code:** 2
**Score:** 2/3

**stdout** (first 20 lines):
```
Install from PyPI succeeded in Python 3.11 venv.
```

**stderr** (first 20 lines):
```
hevn --version: No such option: --version
```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn contacts new --json < /dev/null`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
Display name []:
```

**stderr** (first 20 lines):
```
Aborted.
```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn login --timeout 10 --no-open --json`
**Exit code:** 2
**Score:** 1/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
Invalid value: Timed out waiting for callback on port ...
```

## §12 — Idempotency & Safe Retries
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn transfer contact --contact-id abc --amount 25 --idempotency-key same --yes --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
{"ok": false, "error": "This command needs app authorization (JWT). Run `hevn login` first or set HEVN_API_KEY."}
```

**stderr** (first 20 lines):
```
```

## §13 — Partial Failure & Atomicity
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `inspect command outputs and installed sources`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
No partial/resume/rollback structured contract found.
```

**stderr** (first 20 lines):
```
```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn contracts delete --id abc --json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
{"ok": false, "error": "This command needs app authorization (JWT). Run `hevn login` first or set HEVN_API_KEY."}
```

**stderr** (first 20 lines):
```
```

## §24 — Authentication & Secret Handling
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn mcp-key --json < /dev/null`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
MCP key:
```

**stderr** (first 20 lines):
```
Warning: Password input may be echoed.
Aborted.
```

## §25 — Prompt Injection via Output
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `inspect JSON/YAML output shape`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
External fields are emitted directly; no trusted:false or external-content envelope found.
```

**stderr** (first 20 lines):
```
```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn --schema; hevn check-permissions`
**Exit code:** 2
**Score:** 0/3

**stdout** (first 20 lines):
```
```

**stderr** (first 20 lines):
```
No such option: --schema
```

## §1 — Exit Codes & Status Signaling
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn account get --name acme --json; hevn rate EUR --json`
**Exit code:** mixed
**Score:** 1/3

**stdout** (first 20 lines):
```
Validation uses exit 2; auth/network errors use exit 1; successful status/account fallbacks can exit 0 with embedded errors.
```

**stderr** (first 20 lines):
```
Exit code table is not documented and JSON bodies do not include exit_code.
```

## §2 — Output Format & Parseability
**Date:** 2026-06-01
**CLI version:** hevn-cli 0.1.0
**Check command:** `hevn account list --json; hevn --output json`
**Exit code:** mixed
**Score:** 1/3

**stdout** (first 20 lines):
```
account list --json returns valid JSON, but without a consistent ok/data/meta envelope.
```

**stderr** (first 20 lines):
```
hevn --output json: No such option: --output
```
