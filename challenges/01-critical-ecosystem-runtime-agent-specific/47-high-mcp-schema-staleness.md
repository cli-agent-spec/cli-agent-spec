> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §47

## 47. MCP Wrapper Schema Staleness

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Low

### The Problem

The MCP-wrapped CLI pattern is the most effective approach for making legacy CLIs agent-compatible: wrap an existing CLI in an MCP server that provides structured JSON responses, schema discoverability, and protocol-level error signaling. However, the wrapper author must write tool definitions by hand — the CLI's `--help` text is not automatically parseable into JSON Schema.

Once written, the wrapper schema drifts from the underlying CLI as the CLI evolves:
- CLI adds new flags that the wrapper does not expose
- CLI deprecates flags that the wrapper still documents as current
- CLI changes the semantics of an existing flag without changing its name
- CLI changes output format but the wrapper schema still declares the old format

There is no protocol-level mechanism in MCP to detect or communicate this staleness. An agent using a stale wrapper will:
1. Attempt invocations with arguments that the wrapper's schema says are valid but the CLI rejects
2. Miss new functionality that the CLI supports but the wrapper does not expose
3. Receive outputs that don't match the wrapper's declared `outputSchema`

```typescript
// MCP wrapper written for CLI version 1.x
server.tool("deploy", {
    environment: z.enum(["staging", "production"]),
    // Note: CLI 2.x added --region and --replica-count; wrapper doesn't know
});

// CLI 2.x reality:
// deploy --environment production  // works but missing new required --region in some org configs
// Agent gets "missing required parameter: region" from the CLI
// But the MCP schema doesn't list --region, so agent doesn't know to provide it
```

This is distinct from challenge #22 (Schema Versioning & Output Stability), which concerns first-party frameworks versioning their own output schema. This challenge concerns the emergent staleness of *hand-authored intermediate wrappers* — a two-layer versioning problem that is unique to the wrapper pattern and not addressed by either the framework or the protocol.

### Impact

- Agent constructs valid (per-wrapper-schema) invocations that fail at the CLI layer with opaque errors
- New CLI functionality is silently inaccessible through the wrapper
- If the wrapper's `outputSchema` is stale, agent parsing of structured output fails for commands that changed response format
- No automated mechanism to detect or alert on schema divergence
- Maintenance burden grows linearly with the number of wrapped subcommands and the CLI's development velocity

### Solutions

**Wrapper health-check command:**
```typescript
// Add a schema validation tool to the MCP wrapper
server.tool("_wrapper_health", {}, async () => {
    const cliVersion = await execAndCapture("my-cli --version");
    const knownVersion = "2.3.1";  // version wrapper was written against
    return {
        content: [{type: "text", text: JSON.stringify({
            wrapper_schema_version: knownVersion,
            cli_actual_version: cliVersion.trim(),
            schema_may_be_stale: cliVersion.trim() !== knownVersion,
        })}]
    };
});
```

**Schema auto-generation from --help:**
```python
# Parse --help output to detect new flags not in wrapper schema
def detect_schema_drift(tool_name: str, wrapper_schema: dict) -> list[str]:
    help_output = subprocess.run([tool_name, "--help"], capture_output=True).stdout.decode()
    # Extract flags from help text using regex
    help_flags = set(re.findall(r'--(\w[\w-]*)', help_output))
    wrapper_flags = set(wrapper_schema["properties"].keys())
    new_flags = help_flags - wrapper_flags
    return list(new_flags)
```

**For framework design:**
- MCP wrapper generators should pin the `cli_version` in tool annotations and emit a `schema_stale` warning when the CLI version changes
- Auto-generate MCP wrapper schemas from CLI `--help` or `--schema` JSON output (where available) rather than requiring manual authoring
- Include a `_meta.schema_cli_version` field in tool results so agents can detect version mismatches
- When an MCP tool call produces a non-zero exit code with "unknown option" or "unrecognized argument" in the error, the wrapper should emit `{"code": "SCHEMA_STALE", "hint": "The underlying CLI may have changed; wrapper schema may be outdated"}`
- MCP protocol: add optional `toolSchemaVersion` annotation to tool definitions, allowing version-to-version compatibility tracking

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No version pinning in wrapper; schema drift undetectable; "unknown option" errors from CLI appear as opaque failures |
| 1 | `cli_version` pinned in wrapper metadata; no health-check tool; no `SCHEMA_STALE` detection |
| 2 | `_meta.schema_cli_version` in every tool result; "unknown option" errors mapped to `SCHEMA_STALE` code |
| 3 | `_wrapper_health` tool available; auto-generated schema from `--schema` output; drift detection compares wrapper vs. CLI flag list |

**Check:** Call `_wrapper_health` (if available) and verify it returns `wrapper_schema_version` and `cli_actual_version`; then trigger an "unknown option" error and verify it surfaces as `SCHEMA_STALE`.

---

### Agent Workaround

**Signature:** `unknown option` or `unrecognized argument` for a flag the tool schema declares valid; missing-required error for a parameter absent from the schema

**Tier:** B (one observable check, then one command)

**Call `_wrapper_health` before first use; treat "unknown option" errors as schema staleness:**

```python
import subprocess, json

def check_wrapper_health(tool_cmd: list[str]) -> dict | None:
    """Call the wrapper's health-check tool if available."""
    result = subprocess.run(
        [*tool_cmd, "_wrapper_health"],
        capture_output=True, text=True,
        timeout=10,
    )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None

health = check_wrapper_health(["my-mcp-wrapper"])
if health and health.get("schema_may_be_stale"):
    print(
        f"WARNING: MCP wrapper schema may be stale. "
        f"Wrapper built for CLI v{health['wrapper_schema_version']}, "
        f"current CLI is v{health['cli_actual_version']}. "
        "Some arguments may be missing or invalid."
    )

# Detect schema staleness from "unknown option" errors
result = subprocess.run(cmd, capture_output=True, text=True)
parsed = json.loads(result.stdout)
if not parsed.get("ok"):
    error = parsed.get("error", {})
    msg = error.get("message", "")
    if "unknown option" in msg.lower() or "unrecognized argument" in msg.lower():
        raise RuntimeError(
            f"MCP wrapper schema may be stale: {msg}. "
            "The underlying CLI may have changed flags since the wrapper was last updated."
        )
```

**Limitation:** If the wrapper has no `_wrapper_health` tool and does not map "unknown option" errors to `SCHEMA_STALE`, the agent cannot detect staleness — fall back to comparing `meta.tool_version` across calls; any change signals potential schema drift
