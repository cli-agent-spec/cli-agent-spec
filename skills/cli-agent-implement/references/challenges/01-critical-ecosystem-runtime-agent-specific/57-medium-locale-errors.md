> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §57

## 57. Locale-Dependent Error Messages

**Severity:** Medium | **Frequency:** Situational | **Detectability:** Easy | **Token Spend:** High | **Time:** Low | **Context:** Medium

### The Problem

Distinct from §2 (locale-invariant serialization of numbers/dates), many CLI tools embed raw OS or runtime error messages directly in `error.message`. These come from `errno`, OS exceptions, database drivers — and they are locale-translated. On a French server, "Permission denied" becomes "Permission refusée". Agents that pattern-match on error message text fail silently in non-English environments.

```python
try:
    os.rename(src, dst)
except OSError as e:
    return {"ok": False, "error": {"message": str(e)}}
# en_US: "Permission denied: '/etc/hosts'"
# fr_FR: "Permission refusée: '/etc/hosts'"
# Agent checking for "Permission denied" fails on French systems
```

### Impact

- Error-handling logic that pattern-matches on message text fails on non-English systems
- Agents may retry indefinitely when error classification fails

### Solutions

**Separate machine-readable code from locale message:**
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Permission denied: '/etc/hosts'",
    "locale_message": "Permission refusée: '/etc/hosts'",
    "locale": "fr_FR"
  }
}
```

**Framework normalizes OS errors to English (`LC_MESSAGES=C`) before serialization.**

**For framework design:**
- The framework's exception handler MUST normalize all OS/runtime error messages to English before placing them in `error.message`
- `error.code` is the ONLY field agents should use for error classification; `error.message` is human-readable context only

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Error messages contain locale-translated OS errors; agent pattern-matching on text fails on non-English systems |
| 1 | Most errors use structured codes; some OS errors passed through as raw locale strings in `message` |
| 2 | Framework sets `LC_MESSAGES=C` for OS calls; `error.code` present for all errors; `message` may still be locale text |
| 3 | `error.code` is the only field used for classification; `error.message` normalized to English; `error.locale_message` available for humans |

**Check:** Run the tool on a non-English locale (`LANG=fr_FR.UTF-8 tool <cmd>`) and trigger an OS error — verify `error.code` is present and `error.message` is English regardless of locale.

---

### Agent Workaround

**Signature:** error text in stderr or `error.message` appears in a non-English language; text pattern matching that works on other hosts fails on this one

**Tier:** A (one safe command, no branching)

**Always classify errors by `error.code`, never by `error.message` text; set `LC_MESSAGES=C` in the subprocess environment:**

```python
import subprocess, json, os

env = {
    **os.environ,
    "LC_ALL": "C",           # normalize all locale output to English
    "LC_MESSAGES": "C",      # especially error messages
    "LANG": "C.UTF-8",       # UTF-8 safe but English messages
}

result = subprocess.run(
    cmd, capture_output=True, text=True, env=env
)
parsed = json.loads(result.stdout)

if not parsed.get("ok"):
    error = parsed.get("error", {})

    # ALWAYS use code for classification — never message text
    code = error.get("code", "UNKNOWN")

    # These code checks work on any locale
    if code == "PERMISSION_DENIED":
        raise PermissionError(error.get("message"))
    elif code == "FILE_NOT_FOUND":
        raise FileNotFoundError(error.get("message"))
    else:
        raise RuntimeError(f"[{code}] {error.get('message')}")
```

**Limitation:** `LC_MESSAGES=C` in the subprocess environment normalizes shell and Python runtime messages but does not affect messages from tools that have already translated errors internally — if the tool wraps OS errors without normalization, `error.message` may still be locale-translated; use only `error.code` for branching logic
