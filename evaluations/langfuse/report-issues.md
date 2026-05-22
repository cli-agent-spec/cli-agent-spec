# Langfuse CLI — Issues and Gaps

**Generated:** 2026-05-22  
**Scope:** Critical failure modes

## Observed Bugs

### `--json` does not cover parser errors

Trigger: `./node_modules/.bin/langfuse api traces get --json`  
Result: prose usage output and exit 1.  
Impact: agents cannot rely on JSON for common invalid-invocation paths.

### Top-level `--json`, `--schema`, and `--manifest` behave like help

Trigger: `./node_modules/.bin/langfuse --json` and schema/manifest probes.  
Result: help text exits 0 instead of returning JSON or rejecting unknown flags.  
Impact: agents may falsely treat a schema probe as successful.

### Auth failure lacks semantic structure

Trigger: `./node_modules/.bin/langfuse api healths list --json`  
Result: `{"ok":false,"error":"Missing --username for basic auth"}`.  
Impact: agents do not receive auth method, setup command, or semantic auth code.

### Destructive command help lacks safety controls

Trigger: `./node_modules/.bin/langfuse api traces delete-public --help`  
Result: no `--dry-run`, confirmation flag, or danger metadata.  
Impact: agents cannot preview destructive scope without custom safeguards.

## Gap Table

| § | Gap | Workaround |
|---|---|---|
| §1 | Generic exit code 1 for many failures. | Parse output text and maintain local error classification. |
| §2 | JSON output is inconsistent across error paths. | Attempt JSON parse, then fall back to pattern matching. |
| §12 | No idempotency key/effect contract. | Query state before retries. |
| §23 | No dry-run for delete operations. | Use `--curl` preview and require explicit user approval. |
| §43 | No truncation metadata. | Use endpoint limits/fields and external output caps. |
| §74 | No required-scope declaration. | Use minimally scoped project keys and avoid broad credentials. |
