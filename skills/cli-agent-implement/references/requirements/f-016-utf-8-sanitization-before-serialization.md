# REQ-F-016: UTF-8 Sanitization Before Serialization

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§9 Binary & Encoding Safety](../challenges/04-critical-output-and-parsing/09-high-binary-encoding.md)

**Addresses:** Severity: High / Token Spend: Low / Time: Medium / Context: Low

---

## Description

The framework's JSON serializer MUST pass every string value through a UTF-8 sanitizer before serialization. The sanitizer MUST handle: non-UTF-8 byte sequences (replace with U+FFFD), null bytes (replace with U+FFFD), and lone surrogate code points. The sanitizer MUST never raise an exception or crash; it MUST always produce valid UTF-8 output.

## Acceptance Criteria

- A command that returns a Latin-1 encoded string does not crash; the output is valid UTF-8 JSON
- A command that returns a string containing `\x00` produces valid JSON (no embedded null bytes in output)
- The framework never emits a `UnicodeDecodeError` or equivalent to stderr

---

## Schema

**Types:** [`response-envelope.md`](../schemas/response-envelope.md)

Behavioral requirement — the sanitizer runs inside the framework's JSON serializer. No new fields are added to the envelope; the guarantee is that all string values in the output are valid UTF-8.

---

## Wire Format

Clean JSON output after sanitization (invalid bytes replaced with U+FFFD `\ufffd`):

```json
{
  "ok": true,
  "data": {
    "filename": "caf\ufffd.txt",
    "content":  "line one\ufffdline two"
  },
  "error": null,
  "warnings": [
    { "code": "INVALID_UTF8_REPLACED", "message": "1 invalid UTF-8 sequence replaced with U+FFFD", "context": { "field": "data.filename", "count": 1 } },
    { "code": "NULL_BYTE_REPLACED", "message": "1 null byte replaced with U+FFFD", "context": { "field": "data.content", "count": 1 } }
  ],
  "meta": {
    "exit_code": 0,
    "duration_ms": 12,
    "request_id": "req_02AB",
    "command": "read-file",
    "timestamp": "2024-06-01T12:00:00Z"
  }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework's serializer intercepts every string value before encoding it as JSON, passes it through the sanitizer, and optionally appends a warning entry for each replacement.

```
# Command returns Latin-1 bytes b"caf\xe9.txt"
→ serializer sanitizes → "caf\ufffd.txt"
→ valid UTF-8 JSON emitted to stdout

# Command returns string with null byte "hello\x00world"
→ serializer sanitizes → "hello\ufffdworld"
→ valid UTF-8 JSON emitted to stdout

# No UnicodeDecodeError on stderr in either case
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-017](f-017-binary-field-base64-encoding.md) | F | Composes: binary fields are base64-encoded before sanitization runs |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope that carries sanitized string values |
| [REQ-F-005](f-005-locale-invariant-serialization.md) | F | Composes: locale-invariant serialization works in tandem with UTF-8 sanitization |
