> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §45

## 45. Headless Authentication / OAuth Browser Flow Blocking

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Critical | **Context:** Low

### The Problem

Many modern CLI tools implement authentication via OAuth flows that require a browser — typically an OAuth authorization code flow where the CLI opens a browser tab, the user logs in, and the browser redirects back to a localhost callback server. In agent environments, there is no browser, no desktop, and often no display server. The tool hangs waiting for a browser interaction that will never occur.

This is distinct from challenge #24 (Authentication & Secret Handling), which covers secret storage and env var loading. This challenge covers the *authentication flow initiation* — the step before secrets exist — which blocks agent use entirely.

```bash
# Agent tries to use a CLI tool for the first time
$ gh auth login
# CLI: "Press Enter to open github.com in your browser..."
# Agent sends Enter
# CLI: "Opening browser... Waiting for authentication..."
# No browser available in agent environment → hangs forever
```

Common failure patterns:
1. **OAuth authorization code flow**: CLI opens browser, waits for redirect to localhost
2. **Device code flow** (better but still problematic): CLI prints a URL and a code, waits for the user to visit the URL and enter the code — agent cannot do this autonomously
3. **Interactive token entry**: CLI prompts "Enter your API token:" — blocks on stdin (challenge #10) but specifically in an auth context where the token isn't pre-provided
4. **Credential file expiry**: CLI has stored credentials but they have expired; re-auth requires the browser flow; agent gets auth errors with no clear fix

The MCP HTTP transport requires OAuth 2.1 with PKCE, which is correct for security but adds significant complexity for agent environments that need pre-authorized service accounts or pre-issued tokens.

### Impact

- Complete authentication failure in headless agent environments
- No structured error output: many tools just hang waiting for the browser (challenge #10 compound)
- Even if the agent detects the hang and kills the process, it has no machine-readable information about what authentication mechanism to use
- Expired credentials produce auth errors that are indistinguishable from permission errors without a structured error code
- Single-sign-on and enterprise SSO flows are particularly problematic: they may require multi-factor authentication that is inherently interactive

### Solutions

**For CLI authors:**
```python
# Check for non-interactive auth options before attempting browser flow
if not sys.stdin.isatty():
    # Non-interactive mode: check for token in env vars
    token = os.environ.get("MY_TOOL_TOKEN") or os.environ.get("MY_TOOL_API_KEY")
    if not token:
        print(json.dumps({"ok": False, "error": {
            "code": "AUTH_REQUIRED",
            "message": "No credentials found. Set MY_TOOL_TOKEN environment variable.",
            "auth_methods": [
                {"type": "env_var", "name": "MY_TOOL_TOKEN", "description": "API token"},
                {"type": "env_var", "name": "MY_TOOL_API_KEY", "description": "Legacy API key"}
            ]
        }}))
        sys.exit(8)  # PERMISSION_DENIED exit code
    authenticate_with_token(token)
else:
    # Interactive: offer browser flow
    launch_browser_auth_flow()
```

**For framework design:**
- Any command that triggers authentication must check `isatty()` and return a structured `AUTH_REQUIRED` error in non-interactive mode, never hang
- The `AUTH_REQUIRED` error must include `auth_methods` — an array of structured objects describing how to authenticate non-interactively (env var name, config file format, token endpoint)
- Schema output should include `"requires_auth": true` and `"auth_methods": [...]` so agents can determine how to authenticate before first invocation
- Support `--token` / `--api-key` as universal authentication flags that bypass stored credentials for headless use
- Credential expiry should produce `{"code": "AUTH_EXPIRED"}` distinct from `AUTH_REQUIRED`, with instructions for renewal that work in headless mode

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Browser OAuth flow launched in non-TTY mode; hangs waiting for browser redirect; no structured error emitted |
| 1 | Non-TTY detected; process exits but error message is prose only; `auth_methods` field absent |
| 2 | `AUTH_REQUIRED` structured error with `auth_methods` array; exits immediately in non-TTY mode (no hang) |
| 3 | `--schema` includes `requires_auth` and `auth_methods`; `AUTH_EXPIRED` distinct from `AUTH_REQUIRED`; `--token` flag bypasses stored credentials |

**Check:** Run any authenticated command without credentials set and with `stdin=subprocess.DEVNULL` — verify it exits within 2 seconds with `{"code": "AUTH_REQUIRED", "auth_methods": [...]}`.

---

### Agent Workaround

**Signature:** process hangs after printing `Opening browser...` or a device-code URL; or blocks on an `Enter your API token:` prompt; ends only when killed by timeout

**Tier:** B (one observable check, then one command)

**Pre-check authentication before any command; act on `auth_methods` from `AUTH_REQUIRED` errors:**

```python
import subprocess, json, os

def ensure_authenticated(tool: str) -> bool:
    """Run a lightweight read command to check auth state."""
    env = {**os.environ}
    result = subprocess.run(
        [tool, "status", "--output", "json"],
        capture_output=True, text=True,
        stdin=subprocess.DEVNULL,
        timeout=10,
        env=env,
    )
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False

    if parsed.get("ok"):
        return True

    error = parsed.get("error", {})
    code = error.get("code", "")

    if code in ("AUTH_REQUIRED", "AUTH_EXPIRED"):
        auth_methods = error.get("auth_methods", [])
        for method in auth_methods:
            if method.get("type") == "env_var":
                env_var = method["name"]
                if os.environ.get(env_var):
                    # Env var is already set — likely an expired credential
                    print(f"Credential expired. Re-set {env_var} or run: {error.get('reauth_command', 'tool auth refresh')}")
                else:
                    print(f"Missing credential: set {env_var} to authenticate")
        return False

    return True

if not ensure_authenticated("tool"):
    raise RuntimeError("Authentication required — cannot proceed headlessly")
```

**Limitation:** If the tool hangs on auth in non-TTY mode with no timeout, kill the process after a short period (e.g., 5 seconds) and treat the timeout as an `AUTH_REQUIRED` signal — browser auth flows always require a browser and cannot be completed by an agent
