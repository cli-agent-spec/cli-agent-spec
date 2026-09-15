> **Part III: Errors & Discoverability** | Challenge §20

## 20. Environment & Dependency Discovery

**Severity:** Medium | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

CLI tools often depend on external tools, services, or specific environment configurations. When these are missing, the failure message doesn't tell the agent what's missing or how to get it.

**Unhelpful missing dependency errors:**
```bash
$ tool build
/bin/sh: docker: command not found
exit 127
# Agent knows docker is missing but not: which version, how to install,
# whether there's an alternative
```

**Silent wrong version usage:**
```bash
$ tool deploy
Deploying...
Error: unsupported field 'replicas' in deployment spec
exit 1
# Actually: kubectl version is too old, but error doesn't say that
```

**Environment check scattered across execution:**
```bash
$ tool run
Connecting to DB... ok
Loading config... ok
Checking Redis... FAILED: connection refused
# Fails at step 3; agent has to retry to discover more prereqs
```

### Impact

- Agent cannot distinguish a missing dependency from a code bug or network error
- Each unmet prerequisite discovered only at the step that needs it — no early-fail
- No `fix` field means the agent must guess how to resolve the missing dependency
- Wrong tool version causes semantic errors (unsupported field, wrong behavior) with no version context

### Solutions

**Preflight check command:**
```bash
$ tool doctor --output json
{
  "ok": false,
  "checks": [
    {"name": "docker",   "ok": true,  "version": "24.0.5", "required": ">=20.0"},
    {"name": "kubectl",  "ok": false, "found": "1.18.0", "required": ">=1.24",
     "fix": "brew upgrade kubectl"},
    {"name": "db_conn",  "ok": true},
    {"name": "redis",    "ok": false, "error": "connection refused at localhost:6379",
     "fix": "docker run -d redis"}
  ]
}
```

**Dependency declaration in help:**
```bash
$ tool build --show-requirements --output json
{
  "required": [
    {"name": "docker", "version": ">=20.0", "install": "https://docs.docker.com/..."},
    {"name": "DOCKER_BUILDX_BUILDER", "type": "env_var", "optional": true}
  ]
}
```

**For framework design:**
- Framework provides a `preflight()` hook for each command
- `tool doctor` runs all preflight checks without executing any commands
- Each failed check includes a `fix` field with the exact command to run

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No preflight check; missing dependencies discovered mid-execution with unstructured errors; no `fix` hint |
| 1 | Some dependency errors include the missing tool name; no version info; no structured JSON format |
| 2 | `tool doctor --output json` runs all checks with `ok`, `version`, `required`, and `fix` fields |
| 3 | `tool <command> --show-requirements --output json` lists per-command dependencies; `tool doctor` is a framework-level command |

**Check:** Remove or alias a required dependency to a wrong version and run `tool doctor --output json` — verify it returns a failing check with a `fix` field containing the exact install command.

---

### Agent Workaround

**Signature:** `exit 127` or `command not found` in stderr mid-execution; each re-run surfaces one more missing prerequisite; no `fix` hint in the error

**Tier:** B (one observable check, then one command)

**Run `tool doctor --output json` before first use; act on `fix` fields from failing checks:**

```python
import subprocess, json, sys

def preflight(tool: str) -> bool:
    result = subprocess.run(
        [tool, "doctor", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return True  # doctor not supported, assume ok

    failing = [c for c in data.get("checks", []) if not c.get("ok")]
    for check in failing:
        name = check["name"]
        fix = check.get("fix", "no fix provided")
        found = check.get("found", "not found")
        required = check.get("required", "unknown version")
        print(f"Prereq failed: {name} (found: {found}, required: {required})")
        print(f"  Fix: {fix}")

    return len(failing) == 0

if not preflight("tool"):
    sys.exit(1)
```

**Detect exit 127 (command not found) and map it to a missing dependency:**
```python
if result.returncode == 127:
    # Shell: command not found — extract missing binary from stderr
    missing = result.stderr.strip().split(":")[-1].strip()
    raise RuntimeError(f"Missing dependency: {missing} — install it and retry")
```

**Limitation:** If the tool has no `tool doctor` command and exposes dependencies only through runtime failure messages, run a no-op invocation (e.g., `tool --version`) first and inspect stderr for missing dependency errors before running real commands
