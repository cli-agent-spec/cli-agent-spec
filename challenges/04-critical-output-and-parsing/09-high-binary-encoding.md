> **Part I: Output & Parsing** | Challenge §9

## 9. Binary & Encoding Safety

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Low | **Time:** Medium | **Context:** Low

### The Problem

CLI tools that read files, databases, or APIs may encounter binary data, null bytes, or non-UTF-8 strings. When this data is embedded in JSON output, serialization silently corrupts or crashes the tool, and the agent receives either invalid JSON or a crash with no result.

**Null bytes break JSON:**
```bash
$ tool read-file binary.bin --output json
# File contains \x00 bytes
# json.dumps() in Python: works but produces \u0000
# json.loads() in some parsers: terminates string at \x00
# Result: agent gets truncated or invalid data silently
```

**Non-UTF-8 crashes serialization:**
```bash
$ tool read-file latin1-encoded.txt --output json
# File is Latin-1, not UTF-8
# Python json.dumps(): UnicodeDecodeError → unhandled → crash
# Agent receives: empty stdout, exit 1, no JSON error
```

**Binary in API response:**
```bash
$ tool fetch-record --id 42 --output json
# Record's "avatar" field contains raw PNG bytes
# JSON serialization: fails or produces garbage
# Agent: receives malformed JSON
```

**Log files with mixed encoding:**
```bash
$ tool get-logs --output json
# Log file has 99% UTF-8, one line with a Latin-1 char
# Tool crashes on that line, returns partial output
# Agent: partial JSON, parse error
```

### Impact

- Tool crashes with no JSON error output (agent gets empty stdout)
- JSON is malformed — agent's JSON parser throws
- Binary data silently truncated — agent gets wrong data, no warning
- Non-deterministic behavior depending on data content

### Solutions

**Detect and handle encoding explicitly:**
```python
def safe_read(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # Return base64 for binary, with metadata
        return None  # signal: use binary path

def safe_field(value: bytes | str) -> dict:
    if isinstance(value, bytes):
        try:
            text = value.decode("utf-8")
            return {"type": "text", "value": text}
        except UnicodeDecodeError:
            import base64
            return {"type": "binary", "encoding": "base64",
                    "value": base64.b64encode(value).decode()}
    return {"type": "text", "value": value}
```

**Binary fields use base64 in JSON output:**
```json
{
  "ok": true,
  "data": {
    "name": "photo.png",
    "content": {
      "type": "binary",
      "encoding": "base64",
      "value": "iVBORw0KGgo...",
      "size_bytes": 45231
    }
  }
}
```

**Null byte sanitization:**
```python
def sanitize_string(s: str) -> str:
    return s.replace("\x00", "\ufffd")  # replacement character
```

**Declare content type in output:**
```json
{
  "data": {
    "content": "...",
    "content_encoding": "utf-8",    // or "base64", "latin-1"
    "content_type": "text/plain"    // or "application/octet-stream"
  }
}
```

**For framework design:**
- All string fields pass through a UTF-8 sanitizer before JSON serialization
- Binary fields automatically base64-encoded with `{type, encoding, value}` wrapper
- Framework catches UnicodeDecodeError and emits structured error, never crashes raw
- `--binary-mode base64|hex|skip` flag for commands that may return binary

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Non-UTF-8 input crashes the tool with an unhandled exception and no JSON error on stdout |
| 1 | Encoding errors caught but output is invalid, truncated, or the error is text-only on stderr |
| 2 | Encoding errors produce a structured JSON error; binary fields base64-encoded |
| 3 | Framework auto-detects encoding; null bytes sanitized to `\ufffd`; all binary fields use `{type, encoding, value}` wrapper; `--binary-mode` flag available |

**Check:** Pass a file containing non-UTF-8 bytes to any command that reads file content — verify it emits a structured JSON error (not a crash) and exits with a defined error code.

---

### Agent Workaround

**Signature:** empty stdout with nonzero exit and `UnicodeDecodeError` or `Traceback` in stderr; or JSON truncated or containing `\u0000` / `\ufffd` characters

**Tier:** B (one observable check, then one command)

**Use `errors="replace"` when decoding tool output; handle JSON parse failures as encoding issues:**

```python
result = subprocess.run(cmd, capture_output=True)  # capture as bytes

# Decode with replacement — never crash on bad bytes
stdout = result.stdout.decode("utf-8", errors="replace")
stderr = result.stderr.decode("utf-8", errors="replace")

try:
    parsed = json.loads(stdout)
except json.JSONDecodeError:
    # Could be encoding corruption — check if output contains replacement chars
    if "\ufffd" in stdout:
        raise RuntimeError("Tool output contains encoding errors — binary data in JSON field?")
    raise
```

**Decode base64 binary fields when present:**
```python
import base64

def decode_field(field: dict | str) -> bytes | str:
    if isinstance(field, dict) and field.get("encoding") == "base64":
        return base64.b64decode(field["value"])
    return field
```

**Limitation:** If the tool crashes with an unhandled `UnicodeDecodeError` and produces no stdout, the agent receives empty output with a non-zero exit code and no way to distinguish this from a network failure or permission error — use `--binary-mode skip` if available to exclude binary fields from output
