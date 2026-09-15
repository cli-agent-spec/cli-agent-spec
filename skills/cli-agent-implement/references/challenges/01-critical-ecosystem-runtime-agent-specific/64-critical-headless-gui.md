> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §64

## 64. Headless Display and GUI Launch Blocking

**Source:** Gemini `07_system_physics.md`, Antigravity `05_environment_and_execution.md` (RA)

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Distinct from §45 (OAuth browser flow), many CLI tools launch GUI applications for operations unrelated to authentication: opening a browser to show documentation, launching a file picker, showing a notification dialog, rendering a chart, or using X11 for visualization. In headless environments (containers, CI, SSH sessions without X11 forwarding), these launches either crash immediately (`cannot connect to X server`), hang indefinitely (waiting for a window to close), or silently do nothing while the tool waits for user interaction that never comes.

```bash
# Tool opens browser to show deployment result
$ tool deploy --env prod --open-browser
# In headless container: xdg-open hangs or crashes with:
# "Failed to open URI: No application is registered as handling this file"
# Tool is waiting for the browser to close — hangs forever

# Tool uses X11 for progress visualization
$ tool analyze --chart
# In SSH session without -X: "Error: cannot open display :0"
# Tool crashes with non-zero exit; agent doesn't know if the analyze completed

# macOS `open` command in Linux container:
$ open https://docs.example.com
# "open: command not found" → exit 127 → agent thinks deploy failed
```

### Impact

- Agent blocked indefinitely waiting for a GUI window to close
- Critical operation may have completed successfully but tool crashes during the GUI step
- Exit code reflects GUI failure, not operation result — agent can't determine if work was done
- No way for agent to know in advance which commands will attempt GUI launches

### Solutions

**Detect headless environment and skip GUI operations:**
```python
import os, sys
def is_headless():
    return (
        not sys.stdout.isatty() or
        os.environ.get('CI') or
        not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY')
    )

if is_headless():
    # Skip browser launch; emit URL in JSON instead
    return {"ok": True, "data": {"url": url, "opened": False, "open_hint": f"open {url}"}}
```

**Schema declares GUI operations:**
```json
{
  "name": "deploy",
  "gui_operations": ["browser_open"],
  "headless_behavior": "emit_url_in_output"
}
```

**Wrap graphical commands in headless fallback:**
```bash
# Tool wraps GUI launch:
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo '{"url": "'"$URL"'", "note": "open this URL in your browser"}'
else
    xdg-open "$URL"
fi
```

**For framework design:**
- Framework MUST detect headless environment on startup and set `framework.headless = true`
- Commands that declare `gui_operations` MUST implement headless fallbacks; framework raises a registration error if `headless_behavior` is not declared
- In headless mode, browser/GUI launch attempts MUST be replaced with URL/path emission in the JSON response rather than blocking

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Commands launch GUI/browser in non-TTY mode; deadlock or crash in headless environments; no fallback |
| 1 | Headless detected; GUI not launched; operation fails silently or with a prose error; no URL/path emitted |
| 2 | `headless_behavior: emit_url_in_output` in schema; URL returned in JSON response instead of opening browser |
| 3 | `gui_operations` declared in schema; framework-level headless detection on startup; registration error if no `headless_behavior` declared |

**Check:** Run any command with `--open-browser` (or equivalent) in a headless environment (`DISPLAY=` unset) — verify it exits cleanly with the URL in the JSON response and does not hang.

---

### Agent Workaround

**Signature:** stderr shows `cannot open display`, `Failed to open URI`, or `open: command not found` with `exit 127`; or process hangs after the operation completes

**Tier:** C (stateful logic; weak models apply the fallback below)
**Fallback:** `CI=true NO_BROWSER=1 BROWSER=true DISPLAY= timeout 60 tool <args> </dev/null` (never pass `--open-browser`); if that fails, escalate with the command, exit code, stdout, and stderr

**Set headless environment variables; detect and avoid GUI-launching flags; handle URLs from headless fallback:**

```python
import subprocess, json, os

env = {
    **os.environ,
    "CI": "true",                   # many tools skip GUI in CI mode
    "DISPLAY": "",                  # unset display server — forces headless detection
    "BROWSER": "true",              # no-op browser command
    "NO_BROWSER": "1",              # some tools check this
}

# Check schema for GUI operations before calling
schema = load_schema("tool")  # from §52 workaround
cmd_schema = find_command(schema, "deploy")
if cmd_schema and "browser_open" in cmd_schema.get("gui_operations", []):
    headless_behavior = cmd_schema.get("headless_behavior")
    if headless_behavior == "emit_url_in_output":
        pass  # safe: URL will be in JSON
    elif not headless_behavior:
        print("WARNING: Command may launch browser in headless env — proceed with caution")

result = subprocess.run(
    ["tool", "deploy", "--env", "prod", "--output", "json"],
    # Note: never pass --open-browser in agent context
    capture_output=True, text=True,
    stdin=subprocess.DEVNULL,
    env=env,
    timeout=60,
)
parsed = json.loads(result.stdout)

# Handle headless URL fallback
data = parsed.get("data", {})
if "url" in data and not data.get("opened", True):
    url = data["url"]
    print(f"Browser action deferred (headless): {url}")
    # Agent can surface this URL to a human or use it for API calls
```

**Limitation:** If the tool does not detect headless mode and launches a browser or GUI without a fallback, kill the process after a short timeout (5–10 seconds) and check whether the operation itself completed by calling a status command — the GUI launch may be post-operation and non-blocking for some tools
