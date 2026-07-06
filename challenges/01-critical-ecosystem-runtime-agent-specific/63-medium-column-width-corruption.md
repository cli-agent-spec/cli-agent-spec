> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §63

## 63. Terminal Column Width Output Corruption

**Source:** Antigravity `01_io_and_formatting.md` (RA)

**Severity:** Medium | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** Low | **Context:** Medium

### The Problem

Tools that format output based on terminal width (`$COLUMNS`, `shutil.get_terminal_size()`, `process.stdout.columns`) produce line-wrapped output that breaks agent parsing. A 100-character URL split across two 50-character lines becomes two invalid strings. A JSON field value containing a newline is structurally corrupt. When stdout is not a TTY, `$COLUMNS` is often unset (defaulting to 80) or inherited from a terminal with an unexpected width.

```bash
# Tool wraps long values at terminal width (80 columns by default in non-TTY):
$ tool describe resource-with-very-long-name --output json
{
  "endpoint": "https://api.very-long-subdomain.example.com/v2/resources/very-long-
path/detail",    # ← broken across two lines — invalid URL
  "description": "A resource with a long description that wraps at the terminal
width boundary"   # ← newline in string value — invalid JSON
}

# Agent tries to use the URL — fails because it's been split
# JSON parser fails on the multi-line string values
```

The problem is worse in table-formatted output (not JSON) — column alignment based on terminal width produces garbage when the terminal width assumption is wrong.

### Impact

- URLs, paths, and identifiers split across lines become invalid
- Multi-line string values corrupt JSON structure
- Table output with dynamic column widths produces unparseable garbage in non-TTY mode
- Agents receive structurally broken data with no indication of corruption

### Solutions

**Disable hard-wrapping in non-TTY mode:**
```python
# Python: don't wrap when stdout is not a TTY
import shutil, sys
columns = shutil.get_terminal_size().columns if sys.stdout.isatty() else 0
# columns=0 means "no wrap"
```

**`--width=0` flag disables all hard-wrapping:**
```bash
$ tool describe resource --width=0 --output json
# All strings output as single lines regardless of length
```

**JSON output mode MUST never hard-wrap string values:**
- In JSON output mode, the framework serializes all strings without newline injection
- Table/human output mode may wrap; JSON output mode MUST NOT

**For framework design:**
- Framework MUST disable all terminal-width-based formatting when JSON output mode is active
- Framework MUST NOT inject newlines into string field values during serialization regardless of `$COLUMNS` value
- The `--width` flag (default: `0` in non-TTY, terminal width in TTY) MUST be respected by all formatting functions

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | JSON output wraps long string values at terminal width; URLs and identifiers split across lines; invalid JSON produced |
| 1 | Hard-wrapping disabled when `--output json`; prose output still wraps; `--width` flag absent |
| 2 | JSON mode never injects newlines into string values regardless of `$COLUMNS`; `--width=0` available |
| 3 | Framework disables all terminal-width-based formatting in JSON mode at the framework level; `$COLUMNS` ignored in JSON mode |

**Check:** Set `COLUMNS=40` and run any command with a long string field (URL, path) in `--output json` mode — verify the JSON is valid and the string is not line-wrapped.

---

### Agent Workaround

**Signature:** JSON parse fails on output where long strings (URLs, paths) are split across lines at a fixed column (often 80); break point shifts with `COLUMNS`

**Tier:** B (one observable check, then one command)

**Set `COLUMNS=0` and `--width=0` to suppress terminal-width wrapping; strip any injected newlines from string values:**

```python
import subprocess, json, re, os

env = {
    **os.environ,
    "COLUMNS": "0",      # suppress width-based wrapping in many tools
    "TERM": "dumb",      # many tools disable formatting for dumb terminal
}

result = subprocess.run(
    ["tool", "describe", resource_id, "--output", "json", "--width=0"],
    capture_output=True, text=True,
    env=env,
)

stdout = result.stdout

# If JSON parsing fails, attempt to repair newlines injected into string values
try:
    parsed = json.loads(stdout)
except json.JSONDecodeError:
    # Heuristic: remove newlines that appear inside JSON strings (line-wrapped values)
    # This is fragile — only use as a last resort
    repaired = re.sub(
        r'(?<=[^\\])\n(?=\s*[^"\{\[\]\}])',  # newlines not after a quote or bracket
        "",
        stdout,
    )
    parsed = json.loads(repaired)
```

**Limitation:** Repairing injected newlines in JSON strings is fragile and may produce incorrect results for multi-line string fields that are legitimately multi-line — the correct fix is `--output json` mode combined with `COLUMNS=0`; if the tool still wraps, it is a bug that requires the tool author to fix
