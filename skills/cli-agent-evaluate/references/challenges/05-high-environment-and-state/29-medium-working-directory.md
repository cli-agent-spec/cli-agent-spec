> **Part V: Environment & State** | Challenge §29

## 29. Working Directory Sensitivity

**Severity:** Medium | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** Medium | **Time:** Low | **Context:** Low

### The Problem

Many CLI tools resolve paths, find config files, or change behavior based on the current working directory. Agents set CWD at session start and may not realize that CWD matters for a given command — or that the correct CWD differs per command.

**Implicit project root discovery:**
```bash
$ cd /project/src/components && tool build
# Tool walks up to find package.json → /project/package.json
# Builds from /project, not /project/src/components
# Output paths are relative to /project
# Agent expected paths relative to /project/src/components
```

**Config file discovered from CWD:**
```bash
$ tool validate
# Looks for .toolrc in CWD, then parent dirs
# Agent's CWD=/tmp → no .toolrc found → uses global defaults
# Behavior differs from running in /project where .toolrc exists
```

**Relative paths in output:**
```bash
$ cd /project && tool list-files
{"files": ["src/index.ts", "src/utils.ts"]}
# Paths are relative to CWD at time of call
# Agent stores these, later calls tool from different CWD
# Paths are now wrong
```

**`cd` side effects across tool calls:**
```bash
# Agent calls: tool set-context --dir /project
# Tool internally does os.chdir("/project")
# Next tool call: CWD has changed, agent doesn't know
```

### Impact

- Different CWD → different config loaded → different behavior
- Relative paths in output become stale or wrong
- Tool finds wrong project root, operates on wrong codebase
- Silent failures: command succeeds but affects wrong files

### Solutions

**Always output absolute paths:**
```json
{
  "files": [
    "/project/src/index.ts",
    "/project/src/utils.ts"
  ]
}
```

**Include CWD used in `meta`:**
```json
{
  "meta": {
    "cwd": "/project",
    "project_root": "/project"
  }
}
```

**Explicit `--cwd` / `--root` flag:**
```bash
tool build --cwd /project
tool validate --root /project
# CWD-independent: agent always passes explicit path
```

**Never mutate CWD of the calling process:**
```python
# Bad: os.chdir(target_dir)
# Good: use absolute paths internally; never change process CWD
import os
old_cwd = os.getcwd()
# operate with absolute paths throughout
```

**For framework design:**
- All path outputs are absolute by default
- `meta.cwd` included in every response
- `--cwd` flag available on all commands as a framework standard
- Framework never calls `os.chdir()` / `process.chdir()`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Path outputs are relative; no `meta.cwd`; tool behavior changes silently based on CWD |
| 1 | Some paths are absolute; `meta.cwd` absent; `--cwd` flag on some commands only |
| 2 | All path outputs are absolute; `meta.cwd` present in response; `--cwd` flag available |
| 3 | `--cwd` is a framework-level flag on all commands; framework never mutates process CWD; all paths absolute by default |

**Check:** Run a command from two different directories and compare the path values in the output — any relative path that differs is a failure.

---

### Agent Workaround

**Signature:** same command run from different directories returns different results or relative paths; stored paths later fail with `No such file or directory`

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** Run the command with `--cwd <absolute-project-root>` from that same directory; if that fails, escalate with the command, exit code, stdout, and stderr

**Always pass `--cwd` explicitly; verify `meta.cwd` in response matches intent:**

```python
import subprocess, json, os

project_root = "/absolute/path/to/project"

result = subprocess.run(
    ["tool", "build", "--cwd", project_root, "--output", "json"],
    capture_output=True, text=True,
    cwd=project_root,  # also set subprocess CWD as a belt-and-suspenders measure
)
parsed = json.loads(result.stdout)

# Verify the tool used the CWD we intended
meta_cwd = parsed.get("meta", {}).get("cwd")
if meta_cwd and os.path.realpath(meta_cwd) != os.path.realpath(project_root):
    raise RuntimeError(f"Tool ran from unexpected CWD: {meta_cwd}")
```

**Convert relative paths in output to absolute before storing:**
```python
def resolve_paths(obj, base_dir: str):
    """Recursively resolve relative paths in output using meta.cwd as base."""
    if isinstance(obj, str) and (obj.startswith("./") or obj.startswith("../")):
        return os.path.normpath(os.path.join(base_dir, obj))
    if isinstance(obj, list):
        return [resolve_paths(i, base_dir) for i in obj]
    if isinstance(obj, dict):
        return {k: resolve_paths(v, base_dir) for k, v in obj.items()}
    return obj

cwd = parsed.get("meta", {}).get("cwd", os.getcwd())
data = resolve_paths(parsed.get("data", {}), cwd)
```

**Limitation:** If the tool outputs relative paths and provides no `meta.cwd`, the agent cannot safely resolve them — store the subprocess `cwd` at call time and use it as the base for all path resolution
