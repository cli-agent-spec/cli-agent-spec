# CLI Agent Integration Guide — gh

**Generated:** 2026-05-07
**CLI version:** 2.88.1
**Scope:** Critical failure modes

## Invocation Invariants

These constraints must hold on every call to `gh`, regardless of language or framework:

```
binary:  gh
stdin:   closed (DEVNULL / equivalent)
timeout: 30s
env:     GH_PROMPT_DISABLED=1    # §10 — disables all interactive prompts
         GH_PAGER=cat            # §10 — suppresses pager
         GH_NO_UPDATE_NOTIFIER=1 # §41 — suppresses update notices on stderr
         NO_COLOR=1              # §8  — suppresses ANSI color codes
         GH_TOKEN=<token>        # §45, §53 — pre-set auth; never rely on stored creds
flags:   --json <fields>         # §2  — force JSON output (not auto-activated)
```

**Critical:** `gh` exits 0 on HTTP errors (§1, §53). **Never branch on exit code alone.** Always inspect stderr for error patterns (see Per-Failure-Mode Workarounds below).

---

## Per-Failure-Mode Workarounds  _(score < 3, sorted: severity desc, score asc)_

### §1 — Exit Codes & Status Signaling  [Critical · 0/3]

**Gap:** HTTP 4xx and GraphQL errors exit 0. Exit code is not a reliable success signal.

**Workaround:**
```python
import subprocess, json

result = subprocess.run(
    ["gh", *your_args, "--json", fields],
    env=env, stdin=subprocess.DEVNULL,
    capture_output=True, text=True, timeout=30
)

# Never trust exit code alone — always inspect stderr
if result.returncode != 0:
    # returncode 1 = genuine gh error
    raise GhError(result.stderr)

# Check stderr for error patterns even on exit 0
stderr = result.stderr.strip()
if "HTTP 401" in stderr or "Bad credentials" in stderr:
    raise AuthError(stderr)
if "HTTP 404" in stderr or "Could not resolve" in stderr:
    raise NotFoundError(stderr)
if "HTTP" in stderr:
    raise GhError(stderr)

# Only now trust the stdout
data = json.loads(result.stdout)
```

---

### §53 — Credential Expiry Mid-Session  [Critical · 0/3]

**Gap:** Expired/invalid `GH_TOKEN` → `HTTP 401: Bad credentials` on stderr, exits 0. No structured error. Recovery suggestion (`gh auth login`) is interactive-only.

**Workaround:**
```python
AUTH_ERROR_PATTERNS = [
    "HTTP 401",
    "Bad credentials",
    "Try authenticating with:",
    "HTTP 403",
    "Must have admin rights",
]

def check_stderr_for_auth_error(stderr: str) -> None:
    for pattern in AUTH_ERROR_PATTERNS:
        if pattern in stderr:
            raise AuthExpiredError(
                f"gh auth failure detected in stderr. "
                f"Refresh GH_TOKEN and retry. Raw: {stderr[:200]}"
            )

# On AuthExpiredError: replace GH_TOKEN from secret store and retry once
```

---

### §12 — Idempotency & Safe Retries  [Critical · 1/3]

**Gap:** No idempotency key support, no `effect` field, no `--dry-run`. Retrying a failed create produces duplicates.

**Workaround — query before mutate:**
```python
def safe_create_issue(repo: str, title: str, body: str) -> dict:
    # 1. Check if issue already exists before creating
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", repo,
         "--search", f'"{title}" in:title', "--json", "number,title"],
        env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=30
    )
    existing = json.loads(result.stdout)
    for issue in existing:
        if issue["title"] == title:
            return {"effect": "noop", "number": issue["number"]}

    # 2. Only create if not found
    result = subprocess.run(
        ["gh", "issue", "create", "--repo", repo,
         "--title", title, "--body", body],
        env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=30
    )
    check_stderr_for_auth_error(result.stderr)
    url = result.stdout.strip()
    number = int(url.rstrip("/").split("/")[-1])
    return {"effect": "created", "number": number, "url": url}
```

---

### §45 — Headless Authentication  [Critical · 1/3]

**Gap:** No structured auth error. No non-interactive re-auth path. `gh auth login` requires browser.

**Workaround — pre-flight auth check:**
```python
def verify_auth(token: str) -> bool:
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        env={**os.environ, "GH_TOKEN": token, "NO_COLOR": "1"},
        stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0 and "HTTP 401" not in result.stderr

# Run verify_auth() before any workflow that depends on gh auth
# On failure: replace GH_TOKEN from secret store; do not call gh auth login
```

---

### §2 — Output Format & Parseability  [Critical · 2/3]

**Gap:** `--json` not auto-activated; requires explicit field list per command; no response envelope.

**Workaround — always specify `--json` and normalize the response:**
```python
def gh_json(args: list[str], fields: str, env: dict) -> dict:
    result = subprocess.run(
        ["gh", *args, "--json", fields],
        env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=30
    )
    check_stderr_for_auth_error(result.stderr)
    if result.returncode != 0:
        raise GhError(result.stderr or result.stdout)
    return json.loads(result.stdout)

# Usage:
data = gh_json(
    ["issue", "list", "--repo", "owner/repo", "--limit", "50"],
    fields="number,title,state,createdAt",
    env=BASE_ENV,
)
```

---

### §10 — Interactivity & TTY Requirements  [Critical · 2/3]

**Gap:** No `--non-interactive` flag; suppression requires env vars.

**Workaround:** Always include in `BASE_ENV` (already in Invocation Invariants above). Additionally set:
```python
BASE_ENV = {
    **os.environ,
    "GH_PROMPT_DISABLED": "1",
    "GH_PAGER": "cat",
    "NO_COLOR": "1",
    "GH_NO_UPDATE_NOTIFIER": "1",
    "GH_TOKEN": os.environ["GH_TOKEN"],   # must be pre-set
}
```

---

### §11 — Timeouts & Hanging Processes  [Critical · 2/3]

**Gap:** No `--timeout` flag. Use subprocess timeout on macOS (no GNU `timeout`).

**Workaround:**
```python
try:
    result = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=30)
except subprocess.TimeoutExpired:
    raise GhTimeoutError(f"gh timed out after 30s: {cmd}")
```

---

### §43 — Output Size Unboundedness  [Critical · 2/3]

**Gap:** No pagination metadata in JSON output — agents cannot detect truncation.

**Workaround — always paginate explicitly:**
```python
def gh_list_all(resource_args: list[str], fields: str, page_size: int = 100) -> list:
    """Fetch all pages explicitly rather than relying on default limit."""
    results = []
    page = 1
    while True:
        data = gh_json(
            [*resource_args, "--limit", str(page_size)],
            fields=fields, env=BASE_ENV
        )
        if not data:
            break
        results.extend(data if isinstance(data, list) else [data])
        if len(data) < page_size:
            break   # last page
        page += 1
    return results
```

---

### §62 — $EDITOR and $VISUAL Trap  [Critical · 2/3]

**Gap:** `gh issue create` without `--body` opens `$EDITOR`. No `EDITOR_REQUIRED` error in non-TTY.

**Workaround — always supply all content flags; set EDITOR to no-op:**
```python
BASE_ENV = {
    **BASE_ENV,
    "GH_EDITOR": "/bin/true",   # no-op if editor accidentally invoked
    "EDITOR": "/bin/true",
    "VISUAL": "/bin/true",
}

# Always pass --title AND --body (or --body-file) to create commands
result = subprocess.run(
    ["gh", "issue", "create", "--repo", repo,
     "--title", title,
     "--body", body],          # never omit --body
    env=BASE_ENV, stdin=subprocess.DEVNULL,
    capture_output=True, text=True, timeout=30
)
```

---

## No Action Needed

§8 ANSI & Color Code Leakage, §50 Stdin Consumption Deadlock, §60 OS Output Buffer Deadlock, §64 Headless Display and GUI Launch Blocking  _(score 3/3)_
