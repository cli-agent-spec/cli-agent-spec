> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §34

## 34. Shell Injection via Agent-Constructed Commands

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** High | **Context:** Medium

### The Problem

When an AI agent constructs CLI invocations — either as shell strings or by assembling argument arrays from LLM-generated values — it can inadvertently (or maliciously, via a compromised tool result) inject shell metacharacters that alter command semantics. This is distinct from prompt injection (challenge #25), which concerns LLM context corruption. Shell injection corrupts the subprocess being executed and can trigger unintended commands.

The attack surface is widest when agents:
1. Build command strings by interpolating variables: `f"git commit -m '{message}'"` where `message` comes from LLM output or user input
2. Pass agent-constructed values to `subprocess.run(..., shell=True)`
3. Call external subcommands (Commander.js git-style subcommand delegation) that the agent cannot inspect

```python
# Dangerous: agent fills in commit_message from LLM output
message = "fix bug'; rm -rf /tmp/work; echo '"
subprocess.run(f"git commit -m '{message}'", shell=True)
# Executes: git commit -m 'fix bug'; rm -rf /tmp/work; echo ''
```

The jpoehnelt rubric (Axis 5 level 2–3) explicitly names this as an agent-specific hardening concern, noting that CLIs must reject path traversals (`../`), percent-encoded segments (`%2e`), and embedded query params (`?`, `#` in resource IDs) — all hallucination patterns that agents produce that humans rarely do. A CLI that accepts these naively amplifies agent errors into security events.

The MCP-wrapped CLI pattern specifically calls out that the wrapper layer is the correct place to implement shell-quoting using `shlex` (Python) or `shell-escape` (Node), receiving typed arguments from JSON and constructing commands safely — but most wrappers do not implement this.

### Impact

- An agent with write access to a system can accidentally or intentionally execute unintended shell commands, including file deletion, network exfiltration, or privilege escalation
- Path traversal arguments (`../../etc/passwd`) passed to file-operating commands can escape intended working directories
- Hallucinated arguments containing `?`, `#`, `;`, `&&`, `||` can be silently interpreted as shell operators or URL fragments
- The failure is typically silent: the command exits non-zero or produces unexpected output with no indication that injection occurred
- Hard to detect because the injected commands may succeed (exit 0) with outputs that appear plausible

### Solutions

**For CLI consumers (agents):**
```python
import shlex

# Safe: never interpolate into shell strings
subprocess.run(["git", "commit", "-m", message])  # ✓ list form

# Validate before passing: reject traversal and metacharacter patterns
import re
SAFE_VALUE_RE = re.compile(r'^[^;&|<>`$\\\n\r]+$')
if not SAFE_VALUE_RE.match(message):
    raise ValueError(f"Unsafe value for --message: {message!r}")
```

**For CLI authors / MCP wrapper authors:**
```typescript
import shellEscape from 'shell-escape';

// In MCP tool handler: receive typed args from JSON, construct safely
const args = ["git", "commit", "-m", request.params.arguments.message];
const result = await execFile(args[0], args.slice(1));  // ✓ never shell=True
```

**For framework design:**
- Reject arguments containing `../`, `./`, percent-encoded characters (`%[0-9a-fA-F]{2}`), embedded query string markers (`?`, `#`), and shell metacharacters (`;`, `&&`, `||`, backtick, `$()`) by default
- Provide a whitelist-based argument sanitizer as a framework primitive: `@arg(pattern=r'^[\w\-\.]+$')`
- Default to `subprocess.run(args_list)` (never `shell=True`) in all generated subprocess calls
- Apply jpoehnelt Axis 5 level 2 checks at argument parsing time, before any execution
- MCP wrappers: always receive arguments as typed JSON objects, never concatenate into shell strings

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Framework uses `shell=True` in generated subprocess calls; no metacharacter validation; path traversal accepted silently |
| 1 | `shell=True` avoided in most cases; no rejection of `../`, `%XX`, or embedded `?`/`#`; validation is type-only |
| 2 | Exec-array used throughout; framework rejects path traversal; structured error with `suggestion` on rejection |
| 3 | Axis 5 level 2 full check set: rejects `../`, `%XX`, `?`, `#`, null bytes, string literals `"null"/"undefined"`; `agent_hardening=True` flag on argument declarations |

**Check:** Pass `--name "acme%2Fwidgets"` and `--output "../../etc/test"` to any command — verify both are rejected with a structured `VALIDATION_ERROR` and a `suggestion` showing the corrected form.

---

### Agent Workaround

**Signature:** command whose values contain `;`, `&&`, `$()`, or `../` produces unexpected output or side effects; may still exit `0` with plausible-looking result

**Tier:** A (one safe command, no branching)

**Always use exec-array (list form) for subprocess calls; validate LLM-generated values before passing them:**

```python
import subprocess, re, urllib.parse

# Patterns that indicate agent hallucination
PATH_TRAVERSAL_RE = re.compile(r'(^|/)\.\.(/|$)')
PERCENT_ENCODED_RE = re.compile(r'%[0-9a-fA-F]{2}')
URL_METACHAR_RE = re.compile(r'[?#]')
SHELL_METACHAR_RE = re.compile(r'[;&|<>`$()\n\r\x00]')
LITERAL_NULL_RE = re.compile(r'^(null|undefined|None|NaN|Infinity)$')

def validate_cli_value(name: str, value: str) -> str:
    if PATH_TRAVERSAL_RE.search(value):
        raise ValueError(f"Path traversal in --{name}: {value!r}")
    if PERCENT_ENCODED_RE.search(value):
        decoded = urllib.parse.unquote(value)
        raise ValueError(f"Percent-encoded in --{name}: {value!r} (decoded: {decoded!r})")
    if URL_METACHAR_RE.search(value):
        raise ValueError(f"URL metacharacter in --{name}: {value!r}")
    if LITERAL_NULL_RE.match(value):
        raise ValueError(f"Literal null-like value in --{name}: {value!r}")
    return value

# Always use list form — never shell=True
result = subprocess.run(
    ["tool", "create", "--name", validate_cli_value("name", name)],
    capture_output=True, text=True,
    # never: shell=True
)
```

**Limitation:** Validation catches common hallucination patterns but cannot enumerate all possible injection sequences — the definitive fix is exec-array subprocess calls (list form), which makes shell injection structurally impossible regardless of argument content
