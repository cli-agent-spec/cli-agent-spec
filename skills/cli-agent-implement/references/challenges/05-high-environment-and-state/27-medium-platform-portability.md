> **Part V: Environment & State** | Challenge §27

## 27. Platform & Shell Portability

**Severity:** Medium | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Agent environments vary: macOS, Linux, Docker containers, CI runners. Shell assumptions and platform-specific behavior cause silent failures on non-target platforms.

**macOS vs Linux differences:**
```bash
$ sed -i 's/foo/bar/' file.txt
# Linux: works
# macOS: Error: invalid command code 's'
# macOS requires: sed -i '' 's/foo/bar/' file.txt
```

**Shell-specific syntax:**
```bash
$ tool --args "key=value key2=value2"
# Works in bash
# Fails in sh (no word splitting override)
# Behaves differently in zsh
```

**Path assumptions:**
```bash
#!/usr/bin/env python3
# Assumes python3 in PATH — not true in all containers
```

**GNU vs BSD tool flags:**
```bash
date --iso-8601   # GNU date
date -u +%Y-%m-%dT%H:%M:%SZ  # portable
```

### Impact

- Commands that work on the agent developer's machine fail silently in CI or container environments
- Shell syntax differences cause arg parsing to break without clear error
- Platform-specific path or tool assumptions prevent the tool from running at all
- Agent receives an exit 127 or shell error, not a structured JSON failure

### Solutions

**Portable shebang and runtime detection:**
```bash
#!/usr/bin/env -S python3 -u
# -S: allows arguments after env command (GNU env >=8.30 / macOS 12+)
```

**Explicit shell and version requirements:**
```json
{
  "requires": {
    "shell": "bash>=4.0",
    "platform": ["linux", "darwin"],
    "tools": ["curl>=7.0", "jq>=1.6"]
  }
}
```

**For framework design:**
- `tool doctor` checks platform compatibility
- Framework abstracts platform differences (dates, paths, colors)
- All paths use forward slashes, never backslash (for cross-platform scripts)

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Tool uses platform-specific flags or assumptions; fails on macOS/Linux without explanation |
| 1 | Tool works on target platform; fails on others with a raw shell or OS error, not a structured JSON error |
| 2 | `tool doctor` checks runtime and OS compatibility; failure emits a structured JSON error with `platform` context |
| 3 | Explicit platform/shell requirements declared in `--show-requirements`; framework abstracts all platform differences; `tool doctor` checks all dependencies |

**Check:** Run `tool doctor --output json` — verify it emits structured pass/fail checks for OS, shell, and required tools.

---

### Agent Workaround

**Signature:** command works on one OS but fails on another with `exit 127`, `invalid option`, or `command not found`; no structured JSON error

**Tier:** B (one observable check, then one command)

**Always run `tool doctor` before the first command; inspect platform context in errors:**

```python
import subprocess, json, sys

def check_platform(tool: str) -> list[dict]:
    result = subprocess.run(
        [tool, "doctor", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
        return [c for c in data.get("checks", []) if not c.get("ok")]
    except json.JSONDecodeError:
        return []  # tool doesn't support --doctor

failing = check_platform("tool")
if failing:
    for check in failing:
        print(f"Prereq failed: {check['name']} — {check.get('fix', 'no fix provided')}")
    sys.exit(1)
```

**Pass `--output json` and use explicit paths to avoid shell expansion differences:**
```python
# Avoid shell=True — shell syntax differs across platforms
result = subprocess.run(
    ["tool", "build", "--cwd", "/absolute/path/to/project", "--output", "json"],
    capture_output=True, text=True,  # not shell=True
)
```

**Limitation:** If the tool uses platform-specific binaries or shell syntax internally and provides no `tool doctor` command, the only signal is a non-zero exit code with stderr text — parse stderr for version or command-not-found patterns to identify the missing dependency
