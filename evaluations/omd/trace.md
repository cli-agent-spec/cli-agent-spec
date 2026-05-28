# omd — Trace

## §34 — Shell Injection via Agent-Constructed Commands
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd get table acme%2Fwidgets --output json`; `./target/debug/omd patch table 123e4567-e89b-12d3-a456-426614174000 --json-file ../../etc/passwd --dry-run --output json`
**Exit code:** 3
**Score:** 2/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"ARG_ERROR","message":"Invalid input for 'fqn': percent_encoded_separator (value: \"acme%2Fwidgets\")","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
{"data":null,"error":{"code":"ARG_ERROR","message":"Invalid input for 'json_file': file not found or not accessible (value: \"../../etc/passwd\")","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §37 — REPL / Interactive Mode Accidental Triggering
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd --help`; `./target/debug/omd --schema`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
Commands listed: auth, search, get, lineage, config, spec, mcp, services, glossary, tag, domain, quality, patch, csv, shortcuts, completions, help.
No REPL or shell subcommand found.
```

**stderr** (first 20 lines):
```
```

## §42 — Debug / Trace Mode Secret Leakage
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd --token audit-secret-123 -vv auth status --output json`
**Exit code:** 8
**Score:** 2/3

**stdout** (first 20 lines):
```json
{"data":{"error":"HTTP client error: error sending request for url (http://localhost:8585/api/v1/system/version)","host":"http://localhost:8585","logged_in":true,"profile":"default","server":null,"token":"valid"},"error":null,"meta":{"cli_version":"0.1.1","duration_ms":4,"envelope_version":"1.0","timeout_ms":30000},"ok":true,"warnings":[]}
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Token verification failed","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd --skills --skills-content | wc -c`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
14401 bytes emitted; output envelope did not include meta.truncated, meta.total_bytes, or max output metadata.
```

**stderr** (first 20 lines):
```
```

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `HOME=<temp> ./target/debug/omd auth login --sso --host http://localhost:8585 --output json < /dev/null`
**Exit code:** 8
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Headless mode cannot use --sso. Use --token, --token-env-var, or --email/--password.","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd csv import --input - --entity-type table --dry-run --output json < /dev/null`
**Exit code:** 3
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"ARG_ERROR","message":"Config error: CSV must have an 'id' column with the entity UUID","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd auth status --output json`
**Exit code:** 8
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":{"error":"Auth error: Token has expired. Run `omd auth login` to re-authenticate.","host":"http://localhost:8585","logged_in":true,"profile":"default","server":null,"token":"expired"},"error":null,"meta":{"cli_version":"0.1.1","duration_ms":29,"envelope_version":"1.0","timeout_ms":30000},"ok":true,"warnings":[]}
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Token verification failed","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `rg -n "heartbeat|heartbeat-interval|elapsed_ms" src docs README.md AGENTS.md`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```
No heartbeat contract or heartbeat interval found. Streaming/page support exists, but no long-running heartbeat behavior is declared.
```

**stderr** (first 20 lines):
```
```

## §61 — Bidirectional Pipe Payload Deadlock
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `python3 -c 'print("x"*70000)' | ./target/debug/omd csv import --input - --entity-type table --dry-run --output json`
**Exit code:** 3
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"ARG_ERROR","message":"Config error: CSV must have an 'id' column with the entity UUID","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd --help`; `rg -n "EDITOR|VISUAL|editor" src`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
No editor-requiring command found in help or source search.
```

**stderr** (first 20 lines):
```
```

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `HOME=<temp> DISPLAY= ./target/debug/omd auth login --sso --host http://localhost:8585 --output json < /dev/null`
**Exit code:** 8
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Headless mode cannot use --sso. Use --token, --token-env-var, or --email/--password.","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §71 — Non-Interactive Installation Absence
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `cargo build`; `cargo build`; `./target/debug/omd --version`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
First cargo build completed successfully.
Second cargo build completed successfully.
./target/debug/omd --version => omd 0.1.1
```

**stderr** (first 20 lines):
```
```

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `HOME=<temp> ./target/debug/omd auth login --sso --host http://localhost:8585 --output json < /dev/null`
**Exit code:** 8
**Score:** 3/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Headless mode cannot use --sso. Use --token, --token-env-var, or --email/--password.","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd search orders --host http://127.0.0.1:<hanging-port> --timeout 1 --output json`
**Exit code:** 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"GENERAL_ERROR","message":"HTTP client error: error sending request for url (http://127.0.0.1:<hanging-port>/api/v1/search/query?q=orders&index=all&size=10&from=0)","retryable":false},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
Exited after about 1.09 seconds.
```

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd patch table 123e4567-e89b-12d3-a456-426614174000 --json '[{"op":"replace","path":"/description","value":"x"}]' --dry-run --idempotency-key audit-key --output json`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":{"body":[{"op":"replace","path":"/description","value":"x"}],"headers":{"X-Idempotency-Key":"audit-key"},"method":"PATCH","url":"/api/v1/tables/123e4567-e89b-12d3-a456-426614174000"},"error":null,"meta":{"cli_version":"0.1.1","dry_run":true,"duration_ms":0,"envelope_version":"1.0","timeout_ms":30000},"ok":true,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §13 — Partial Failure & Atomicity
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `rg -n "partial|completed_steps|resume|rollback" src docs README.md AGENTS.md`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
src/main.rs and src/output.rs include cancellation_envelope with partial true and completed_steps.
No resume token, rollback-on-failure flag, or step manifest found.
```

**stderr** (first 20 lines):
```
```

## §23 — Side Effects & Destructive Operations
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd patch table 123e4567-e89b-12d3-a456-426614174000 --json '[{"op":"replace","path":"/description","value":"x"}]' --dry-run --output json`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":{"body":[{"op":"replace","path":"/description","value":"x"}],"headers":{},"method":"PATCH","url":"/api/v1/tables/123e4567-e89b-12d3-a456-426614174000"},"error":null,"meta":{"cli_version":"0.1.1","dry_run":true,"duration_ms":0,"envelope_version":"1.0","timeout_ms":30000},"ok":true,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §24 — Authentication & Secret Handling
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `HOME=<temp> ./target/debug/omd auth login --token secret-canary --host http://localhost:8585 --headless --output json`
**Exit code:** 8
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"AUTH_REQUIRED","message":"Auth error: Could not reach http://localhost:8585: HTTP client error: error sending request for url (http://localhost:8585/api/v1/system/version)\nCheck the host URL and token.","retryable":true},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
```

## §25 — Prompt Injection via Output
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `rg -n "inject_external_trust_tags|sanitize_injection_patterns|no-injection-protection" src AGENTS.md docs/agent-dx-cli-scale.md`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
src/output.rs includes external trust tagging and injection pattern sanitization.
Global help exposes --no-injection-protection.
AGENTS.md documents external API responses as _source: external / _trusted: false.
```

**stderr** (first 20 lines):
```
```

## §74 — Credential Scope Declaration Absence
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd search --schema`; `./target/debug/omd check-permissions --for search`
**Exit code:** 2
**Score:** 0/3

**stdout** (first 20 lines):
```json
{"data":{"cli_name":"omd","cli_version":"0.1.1","commands":{"search":{"capabilities":{"accepts_json":false,"accepts_json_file":false,"mutating":false,"read_only":true,"supports_dry_run":false,"supports_field_selection":true,"supports_generate_params_skeleton":false,"supports_generate_skeleton":false,"supports_idempotency_key":false,"supports_include_optional":false,"supports_page_all":false,"supports_stream":false},"input":{"options":[...]}}},"schema_version":"2.0"},"ok":true}
```

**stderr** (first 20 lines):
```
No required_scopes field in schema. No check-permissions command in help.
```

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd patch --output json`; `./target/debug/omd search orders --host http://10.255.255.1:1 --timeout 2 --output json`
**Exit code:** 2; 1
**Score:** 1/3

**stdout** (first 20 lines):
```json
{"data":null,"error":{"code":"GENERAL_ERROR","message":"HTTP client error: error sending request for url (http://10.255.255.1:1/api/v1/search/query?q=orders&index=all&size=10&from=0)","retryable":false},"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":false,"warnings":[]}
```

**stderr** (first 20 lines):
```
error: the following required arguments were not provided:
  <ENTITY_TYPE>
  <ID>

Usage: omd patch --output <OUTPUT> <ENTITY_TYPE> <ID>
```

## §2 — Output Format & Parseability
**Date:** 2026-05-28
**CLI version:** `omd 0.1.1`
**Check command:** `./target/debug/omd shortcuts --output json`; `./target/debug/omd patch --output json`
**Exit code:** 0; 2
**Score:** 2/3

**stdout** (first 20 lines):
```json
{"data":[{"args":"<query>","description":"Keyword search across all metadata assets","name":"+search"}],"error":null,"meta":{"cli_version":"0.1.1","duration_ms":0,"envelope_version":"1.0"},"ok":true,"warnings":[]}
```

**stderr** (first 20 lines):
```
Normal command output is a consistent JSON envelope. Missing-argument invocation still emits clap prose to stderr and no JSON stdout.
```
