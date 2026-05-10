> **Part I: Output & Parsing** | Challenge §2

## 2. Output Format & Parseability

**Severity:** Critical | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** High

### The Problem

Agents parse command output to determine what happened and extract values for subsequent steps. Unparseable, inconsistent, or human-only output forces the agent to do fragile regex parsing or hallucinate results.

**Human-formatted output agents cannot reliably parse:**
```
$ tool list-users
┌────────────────┬─────┬──────────────┐
│ Name           │ ID  │ Status       │
├────────────────┼─────┼──────────────┤
│ Alice Johnson  │ 42  │ active       │
│ Bob Smith      │ 43  │ suspended    │
└────────────────┴─────┴──────────────┘
Total: 2 users
```

```
# Agent tries: grep for numbers, split on │, strip whitespace...
# Breaks on: names with special chars, different terminal widths,
#             localized output, color codes embedded in text
```

**Output that changes format based on result count:**
```bash
$ tool get-item --id 1
name: foo, value: bar   # single item: flat format

$ tool get-items
name: foo               # multiple items: different structure
  value: bar
name: baz
  value: qux
```

**Mixed content in stdout:**
```
Initializing... done
Connecting to database... done
{"result": "ok", "id": 42}   # ← the actual data is buried in prose
Operation completed in 1.2s
```

**Locale-dependent output:**
```bash
# On en_US system:
$ tool show-size
File size: 1,234,567 bytes

# On de_DE system:
$ tool show-size
Dateigröße: 1.234.567 Bytes
# agent's number parsing breaks
```

### Impact

- Agent extracts wrong values, propagates errors downstream
- Token waste: agent must reason about format before extracting data
- Non-deterministic behavior across environments

### Solutions

**Machine-readable output flag:**
```bash
# Always provide a structured output mode
tool list-users --output json
tool list-users --output jsonl   # one JSON object per line for streaming
tool list-users --output tsv     # tab-separated, good for piping
tool list-users --output plain   # minimal, no decoration (for humans too)

# Some CLIs use --json as a shorthand (gh, az, etc.)
tool list-users --json           # equivalent to --output json

# Some CLIs use -o as a short flag (kubectl, helm, etc.)
tool list-users -o json
```

**JSON output schema:**
```json
{
  "ok": true,
  "data": [...],      // always present, even if empty array/null
  "error": null,      // always present
  "meta": {
    "count": 2,
    "duration_ms": 45
  }
}
```

**On failure:**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "User with id=999 does not exist",
    "details": {}
  }
}
```

**Rules for agent-compatible output:**
1. Same schema whether 0, 1, or N results
2. No prose mixed into data output (prose goes to stderr)
3. No color codes in `--output json` mode (detect `NO_COLOR` env var)
4. Numbers always in invariant locale (`.` decimal, no thousands separator)
5. Dates always in ISO 8601 (`2024-03-11T14:30:00Z`)
6. Boolean as `true`/`false`, never `yes`/`no`/`1`/`0` in JSON mode

**For framework design:**
- Auto-detect output format based on `--output` flag or `CI=true` env
- Provide output formatters as first-class framework primitives
- Emit a JSON schema for every command's output via `--output-schema`

---

> **Merged from §48:** The following content was originally a separate challenge.
> It is consolidated here because it describes a specific case of the same root problem.

### Subsection: Structured Output Envelope Absence

**Severity:** High | **Frequency:** Very Common | **Detectability:** Easy | **Token Spend:** High | **Time:** Medium | **Context:** High

### The Problem

Even when a CLI tool supports `--format json` or `--output json`, the JSON output is typically ad-hoc per command — each command invents its own top-level structure, its own error format, its own success/failure indicator, and its own metadata placement. Agents consuming a suite of tools must learn a different JSON schema for each command's success case, each command's error case, and have no reliable way to extract common metadata (timing, version, request ID) across tools.

This is distinct from challenge #2 (Output Format & Parseability), which covers whether JSON output exists at all. This challenge concerns the *envelope* — the consistent wrapper structure around any JSON response — which challenge #2 does not require.

```json
// Tool A success:
{"status": "ok", "result": {...}, "timestamp": "..."}

// Tool B success:
{"data": [...], "count": 42}

// Tool C success:
[{"id": 1, ...}, {"id": 2, ...}]   // bare array, no envelope

// Tool D error:
{"error": "not found"}

// Tool E error:
{"message": "Resource not found", "code": 404}

// Tool F error (exit code 1, stderr):
"Error: resource 'xyz' not found\n"
```

An agent consuming all six tools must handle six different response shapes for what are semantically identical outcomes. More critically, there is no standard way to:
- Distinguish success from failure without inspecting field names and values (not just exit codes)
- Extract the error message in a format-agnostic way
- Find pagination metadata (`has_more`, `next_cursor`) when it exists
- Determine whether output data is complete or truncated
- Read request timing (`duration_ms`) or correlation IDs (`request_id`)

The comparison matrix shows REQ-F-004 (Consistent JSON Response Envelope) is ✗ across all evaluated solutions — including agentyper, which provides JSON output but without a standardized envelope.

### Impact

- Agent must write per-tool parsing logic for each command's success and error formats
- No generic error handler: agents cannot uniformly check `response.ok` or `response.error.code` across tools
- Pagination metadata lives in different fields or different locations per tool, making generic pagination handling impossible
- Correlating requests across tools (for debugging) requires per-tool knowledge of where timestamps and IDs live
- LLM token spend increases when agents must reason about schema variations rather than applying a known pattern

### Solutions

**Standard envelope format:**
```json
{
  "ok": true,
  "data": { ... },
  "error": null,
  "warnings": [],
  "meta": {
    "request_id": "req_abc123",
    "duration_ms": 142,
    "schema_version": "1.0.0",
    "truncated": false,
    "has_more": false,
    "next_cursor": null
  }
}
```

**Error envelope:**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource 'xyz' does not exist",
    "field": null,
    "retryable": false,
    "retry_after_ms": null
  },
  "warnings": [],
  "meta": { "request_id": "req_abc124", "duration_ms": 23, "schema_version": "1.0.0" }
}
```

**For framework design:**
- Make the `ok`/`data`/`error`/`warnings`/`meta` envelope mandatory for all structured JSON output; prohibit raw arrays or bare objects as top-level responses
- Framework-generated output functions (`output()`, `echo()`) must serialize through the envelope automatically; direct `print()` / `console.log()` must be prohibited in command handlers
- Define a JSON Schema for the envelope itself and publish it as a standard (analogous to JSON:API or JSON-LD) so agents can validate responses against it
- The `meta` section must always include `request_id`, `duration_ms`, and `schema_version` without any author effort (framework auto-injects these)
- `error.code` must be from the standard exit code taxonomy (challenge #1) — machine-readable string constant, not a free-form message

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No structured output mode; human-formatted tables, prose, or locale-dependent text only |
| 1 | `--output json` exists on some commands but format varies; prose mixed into stdout; no consistent envelope |
| 2 | `--output json` on all commands; consistent `ok`/`data`/`error` top-level structure; no prose on stdout |
| 3 | Full envelope with `ok`, `data`, `error`, `warnings`, `meta` (including `request_id`, `duration_ms`); auto-activated when `CI=true` or stdout not a TTY |

**Check:** Run any command with `--output json` and redirect stderr to `/dev/null` — verify stdout is valid JSON with `ok` and `data` fields regardless of result count (0, 1, or N items).

---

### Agent Workaround

**Always request structured output and detect format violations before parsing:**

```python
# Discover the JSON flag from --help before invoking the real command
_help = subprocess.run([*cmd, "--help"], capture_output=True, text=True)
help_text = _help.stdout + _help.stderr

JSON_FLAG_PATTERNS = [
    (r"--output\s+\w*json", ["--output", "json"]),  # --output json / --output-format json
    (r"--json\b",            ["--json"]),             # gh, az
    (r"-o\b",                ["-o", "json"]),         # kubectl, helm
]
json_flag = next(
    (flag for pattern, flag in JSON_FLAG_PATTERNS if re.search(pattern, help_text)),
    None,
)
if json_flag is None:
    raise ValueError(f"No JSON output flag found in --help for: {cmd}")

result = subprocess.run(
    [*cmd, *json_flag],
    capture_output=True, text=True,
    env={**os.environ, "NO_COLOR": "1", "CI": "true"},
)

stdout = result.stdout.strip()

# Detect help text pollution (invocation error)
if result.returncode != 0 and any(kw in stdout for kw in ("Usage:", "Options:", "Commands:")):
    raise ValueError(f"Received help text instead of JSON — likely a usage error: {cmd}")

# Parse the last valid JSON line (guards against leading prose)
for line in reversed(stdout.splitlines()):
    try:
        parsed = json.loads(line)
        break
    except json.JSONDecodeError:
        continue
else:
    raise ValueError(f"No valid JSON in output: {stdout[:200]}")

ok = parsed.get("ok", parsed.get("status") == "ok")
data = parsed.get("data") or parsed.get("result") or parsed
```

**Limitation:** If the tool has no `--output json` flag and mixes prose with data in stdout, regex extraction is fragile and environment-dependent — there is no reliable agent-side fix; treat the tool as unstructured and require human review of any extracted values
