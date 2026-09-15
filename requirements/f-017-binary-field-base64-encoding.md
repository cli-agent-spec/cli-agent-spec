# REQ-F-017: Binary Field Base64 Encoding

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§9 Binary & Encoding Safety](../challenges/04-critical-output-and-parsing/09-high-binary-encoding.md)

**Addresses:** Severity: High / Token Spend: Low / Time: Medium / Context: Low

---

## Description

When a command returns a value that cannot be represented as valid UTF-8 text, the framework MUST automatically encode it as a structured object: `{"type": "binary", "encoding": "base64", "value": "<base64 string>", "size_bytes": <integer>}`. Command authors MUST be able to declare a field as potentially binary; the framework handles encoding transparently. The framework MUST also accept a `content_type` annotation that is passed through as `"content_type"` in the wrapper object.

## Acceptance Criteria

- A command that returns raw PNG bytes produces valid JSON with a `base64`-encoded value wrapper
- The `size_bytes` field in the wrapper matches the original byte length
- A consuming caller can recover the original bytes by base64-decoding `value`

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Binary fields are encoded as a structured wrapper object inside `data`. The wrapper schema:

```json
{
  "type": "binary",
  "encoding": "base64",
  "value": "<base64 string>",
  "size_bytes": 1234,
  "content_type": "image/png"
}
```

`content_type` is optional and is present only when the command author declares it.

---

## Wire Format

Response containing a base64-encoded binary field:

```json
{
  "ok": true,
  "data": {
    "name": "logo.png",
    "bytes": {
      "type": "binary",
      "encoding": "base64",
      "value": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk",
      "size_bytes": 1024,
      "content_type": "image/png"
    }
  },
  "error": null,
  "warnings": [],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id": "req_03CD",
    "command": "get-image",
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed beyond declaring a field as potentially binary. The framework detects non-UTF-8 byte values and wraps them automatically.

```
# Command declares field 'bytes' as binary
register command "get-image":
  output_schema:
    bytes: { type: binary, content_type: "image/png" }

# Framework serializes raw PNG bytes as:
{
  "type": "binary",
  "encoding": "base64",
  "value": "iVBOR...",
  "size_bytes": 1024,
  "content_type": "image/png"
}
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-016](f-016-utf-8-sanitization-before-serialization.md) | F | Composes: binary encoding runs before UTF-8 sanitization to prevent mangling |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries the binary wrapper in `data` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Provides: output schema declaration mechanism used to annotate binary fields |
