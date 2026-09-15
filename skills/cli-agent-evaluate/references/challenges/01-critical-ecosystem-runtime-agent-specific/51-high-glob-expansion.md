> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §51

## 51. Shell Word Splitting and Glob Expansion Interference

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

When agents construct CLI invocations as shell strings and pass them to a shell executor, the shell performs word splitting and glob expansion before the tool receives the arguments. A filename with a space (`report 2024.txt`) becomes two separate arguments; a pattern like `*.json` expands to all matching files in the current directory, or fails with "no matches found" in strict mode. The agent's logically correct command is silently distorted by the shell before the tool ever sees it.

```bash
# Agent intends: delete the file named "report 2024.txt"
$ rm report 2024.txt
# Shell word-splits: rm receives TWO args: "report" and "2024.txt"
# "report" doesn't exist → exit 1
# Agent gets error but doesn't know why

# Agent intends: process all JSON files matching a pattern
$ my-tool process *.json
# If no .json files exist in CWD:
#   bash (without nullglob): passes literal "*.json" — tool gets a string, not a list
#   zsh (with nomatch): "no matches found" — error before tool even runs
#   bash (with nullglob): passes nothing — tool gets zero arguments, different behavior

# Agent intends: a literal value containing special chars
$ my-tool --filter "status=active&region=us"
# Shell may interpret & as background operator in some contexts
```

The behavior is shell-dependent (bash vs zsh vs sh all differ), environment-dependent (shell options like `nullglob`, `globstar`), and completely invisible to the tool.

### Impact

- Silent argument mutation before tool receives any input
- Tool operates on wrong or zero targets, exits successfully
- Shell-variant behavior: same command produces different results on different systems
- The tool cannot detect or report the distortion — it only sees the post-expansion args

### Solutions

**Tools must validate received arguments against declared constraints:**
```bash
# If --file expects a single file path, tool validates it exists before acting
$ my-tool process report
Error: file 'report' not found. Did you mean 'report 2024.txt'?
# This surfaces the word-split mistake
```

**Schema declares which args expect file paths or glob patterns:**
```json
{
  "name": "files",
  "type": "glob_pattern",
  "glob_expanded_by": "caller",
  "or": "filepath"
}
```

**Framework-provided invocation helpers use exec-array:**
```python
# Framework's subprocess API (exec-array, no shell):
result = framework.run(["my-tool", "process", filename])
# filename is passed as a single argument regardless of spaces or special chars
```

**For framework design:**
- The framework's subprocess API MUST use exec-array (not shell string) — this fully prevents the problem for tool-to-tool invocations
- Document prominently in the agent guide: "never construct shell strings; always use exec-array invocation."
- Tools that accept file paths MUST validate existence and emit a distinct `FILE_NOT_FOUND` error to surface word-split mistakes

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Framework uses shell string invocation; glob expansion and word splitting occur silently before tool receives args |
| 1 | Exec-array used in framework; tool does not validate received paths; word-split mistakes produce ambiguous errors |
| 2 | Exec-array enforced; file-path args validated for existence before operation; `FILE_NOT_FOUND` error on missing path |
| 3 | Schema declares which args expect `glob_pattern` vs `filepath`; `FILE_NOT_FOUND` error includes "did you mean?" suggestion for common word-split patterns |

**Check:** Pass a filename containing a space as a single argument via exec-array — verify the tool receives it as one argument and either processes it or emits a clear `FILE_NOT_FOUND` error with the full path.

---

### Agent Workaround

**Signature:** error names only the first word of a space-containing path; shell prints `no matches found`; tool receives literal `*.json` or zero args yet may exit `0`

**Tier:** B (one observable check, then one command)

**Always use exec-array (list form) for subprocess calls; pre-validate file paths before passing them:**

```python
import subprocess, json, os, shlex

# ALWAYS use list form — never construct a shell string
# BAD:  subprocess.run(f"tool process {filename}", shell=True)
# GOOD: subprocess.run(["tool", "process", filename])

def validate_file_path(path: str) -> str:
    """Validate a file path before passing to a tool."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File not found: {path!r}. "
            "If the path has spaces, ensure it is a single argument (not word-split)."
        )
    # Resolve to absolute path to avoid CWD sensitivity
    return os.path.abspath(path)

# Validate each path argument before the call
files = [validate_file_path(f) for f in file_list]

result = subprocess.run(
    ["tool", "process", "--output", "json"] + files,  # exec-array, not shell=True
    capture_output=True, text=True,
    stdin=subprocess.DEVNULL,
)
parsed = json.loads(result.stdout)
```

**Handle glob patterns by expanding them in Python, not in shell:**
```python
import glob

# Expand globs in Python before passing to tool
pattern = "*.json"
matched = glob.glob(pattern)
if not matched:
    raise RuntimeError(f"No files matched glob pattern: {pattern!r}")

result = subprocess.run(
    ["tool", "process"] + matched,   # pass actual files, not the glob pattern
    capture_output=True, text=True,
)
```

**Limitation:** Exec-array prevents shell expansion but does not prevent the tool from receiving the wrong number of arguments if the agent itself accidentally splits a path — always treat each file path as a single string element in the args list
