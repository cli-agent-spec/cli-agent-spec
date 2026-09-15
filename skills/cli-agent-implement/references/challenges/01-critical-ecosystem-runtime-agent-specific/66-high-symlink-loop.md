> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §66

## 66. Symlink Loop and Recursive Traversal Exhaustion

**Source:** Antigravity `05_environment_and_execution.md` (RA)

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Critical | **Context:** Low

### The Problem

When a CLI tool performs recursive directory traversal (copy, delete, archive, search) and encounters a circular symlink (`A → B → A`), it loops indefinitely consuming all available memory and CPU until it crashes or the system OOM-kills it. The tool emits no warning before running out of resources. Agents operating on user-provided paths cannot know in advance whether circular symlinks exist, and the tool provides no defense.

```bash
# Setup: circular symlink
$ mkdir /tmp/a && mkdir /tmp/b
$ ln -s /tmp/b /tmp/a/link_to_b
$ ln -s /tmp/a /tmp/b/link_to_a

# Agent runs a recursive delete:
$ my-tool delete --recursive /tmp/a
# Tool traverses: a/ → a/link_to_b/ → a/link_to_b/link_to_a/ → ...
# Memory grows unbounded; process hangs; eventually OOM-killed
# Agent sees: timeout, then exit (non-zero from OOM kill signal)
# No structured error; agent doesn't know if any files were deleted

# Also affects: archive commands (infinite zip), find-and-replace, hash computation
$ tool archive /tmp/a --output archive.tar.gz
# Creates a theoretically infinite archive; fills disk; crashes
```

### Impact

- Process consumes all available memory and CPU before dying
- Agent timeout fires; no information about what happened or what was deleted
- Disk may be filled by infinite archive or temp file creation
- Partial operations: some files may have been deleted/modified before the crash

### Solutions

**Track visited inodes; fail on revisit:**
```python
visited_inodes = set()
def safe_walk(path):
    inode = os.stat(path).st_ino
    if inode in visited_inodes:
        raise SymlinkLoopError(f"Circular symlink detected at {path}")
    visited_inodes.add(inode)
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=True):
            safe_walk(entry.path)
```

**Structured error on loop detection:**
```json
{
  "ok": false,
  "error": {
    "code": "SYMLINK_LOOP",
    "message": "Circular symlink detected at /tmp/a/link_to_b/link_to_a.",
    "path": "/tmp/a/link_to_b/link_to_a",
    "loop_target": "/tmp/a",
    "completed_count": 42,
    "hint": "Use --no-follow-symlinks to skip symlinks during traversal."
  }
}
```

**For framework design:**
- Framework's filesystem traversal utilities MUST track visited inodes and exit with a structured `SYMLINK_LOOP` error (exit 4) immediately upon detection
- `--no-follow-symlinks` flag MUST be auto-provided for all recursive traversal commands
- Maximum traversal depth (`--max-depth`, default: 50) MUST be enforced as a second defense layer

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Circular symlinks cause the tool to run indefinitely, consuming all memory; no detection; OOM kill |
| 1 | Process eventually fails but with a non-structured error; no `SYMLINK_LOOP` code; no `completed_count` |
| 2 | `SYMLINK_LOOP` structured error on detection; `completed_count` indicates partial work done; exits promptly |
| 3 | `--no-follow-symlinks` flag on all recursive commands; `--max-depth` default enforced; inode tracking in framework traversal utilities |

**Check:** Create a circular symlink (`ln -s . /tmp/loop/self`) and pass it to any recursive command — verify it exits within 1 second with `{"code": "SYMLINK_LOOP", "completed_count": N}`.

---

### Agent Workaround

**Signature:** recursive command (delete, archive, search) hangs with growing memory or disk use; killed by timeout or OOM with a signal exit code and no structured error

**Tier:** B (one observable check, then one command)

**Pass `--no-follow-symlinks` and `--max-depth` on all recursive commands; handle `SYMLINK_LOOP` errors as partial success:**

```python
import subprocess, json

def run_recursive(
    cmd: list[str],
    path: str,
    max_depth: int = 50,
) -> dict:
    full_cmd = [
        *cmd,
        path,
        "--no-follow-symlinks",     # prevent symlink loop traversal
        f"--max-depth={max_depth}", # second defense layer
        "--output", "json",
    ]

    result = subprocess.run(
        full_cmd,
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=120,  # hard timeout as final safety net
    )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"No JSON output: {result.stdout[:200]}")

    if not parsed.get("ok"):
        error = parsed.get("error", {})
        if error.get("code") == "SYMLINK_LOOP":
            # Partial success — some items were processed before the loop
            completed = error.get("completed_count", 0)
            loop_path = error.get("path", "unknown")
            loop_target = error.get("loop_target", "unknown")
            print(
                f"WARNING: Circular symlink at {loop_path} → {loop_target}. "
                f"{completed} items processed before detection. "
                f"Use {error.get('hint', '--no-follow-symlinks')} to skip symlinks."
            )
            return {"ok": False, "partial": True, "completed_count": completed, "error": error}
        raise RuntimeError(f"Recursive command failed: {parsed}")

    return parsed
```

**Limitation:** If the tool has no `--no-follow-symlinks` flag and no loop detection, it will exhaust resources on circular symlinks — use a short `timeout` (30–60 seconds) on all recursive commands and treat `TimeoutExpired` on such commands as a potential symlink loop indicator
