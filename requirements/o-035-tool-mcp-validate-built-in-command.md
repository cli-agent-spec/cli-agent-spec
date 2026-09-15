# REQ-O-035: tool mcp-validate Built-In Command

**Tier:** Opt-In | **Priority:** P2

**Source:** [§47 MCP Wrapper Schema Staleness](../challenges/01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Medium

---

## Description

When the tool is wrapped as an MCP server, the framework MUST provide a built-in `tool mcp-validate` command that compares the MCP tool schemas with the current CLI command schemas and reports any drift. Schema drift is defined as: a field present in the CLI schema but absent from the MCP schema; a field present in the MCP schema but absent from the CLI schema; a field type that differs between the two schemas; a new command added to the CLI but not exposed in the MCP wrapper. The command MUST accept `--mcp-schema-file <path>` or `--mcp-server-url <url>` as the source of truth for the MCP schema.

## Acceptance Criteria

- `tool mcp-validate --mcp-schema-file mcp.json` exits 0 if schemas match, non-zero if drift is detected
- Drift is reported as a structured JSON diff with `added`, `removed`, and `changed` fields
- A new CLI command not present in the MCP schema is reported as a `missing_from_mcp` drift entry
- The command can be run in CI to detect schema staleness before deployment

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

`data` contains `drift` with `added`, `removed`, `changed`, and `missing_from_mcp` arrays.

---

## Wire Format

```bash
$ tool mcp-validate --mcp-schema-file mcp.json --output json
```

```json
{
  "ok": false,
  "data": {
    "drift": {
      "added": [],
      "removed": [],
      "changed": [{ "command": "deploy", "field": "data.url", "cli_type": "string", "mcp_type": "null" }],
      "missing_from_mcp": ["delete"]
    }
  },
  "error": {
    "code": "SCHEMA_DRIFT_DETECTED",
    "message": "CLI schema and MCP schema differ for 2 commands",
    "retryable": false,
    "fix_required": "Regenerate the MCP schema from tool manifest"
  },
  "warnings": [],
  "meta": { "exit_code": 1, "duration_ms": 31 }
}
```

No drift:

```json
{ "ok": true, "data": { "drift": { "added": [], "removed": [], "changed": [], "missing_from_mcp": [] } }, "error": null, "warnings": [], "meta": { "exit_code": 0, "duration_ms": 12 } }
```

---

## Example

Opt-in at the framework level.

```
app = Framework("tool")
app.enable_mcp_validate()

# Run in CI to catch schema staleness before deployment:
$ tool mcp-validate --mcp-schema-file ./mcp-server/schema.json
→ exit 0 if no drift, exit 1 if drift detected
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: CLI schemas compared against MCP schemas |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Provides: manifest used as the canonical CLI schema source for comparison |
