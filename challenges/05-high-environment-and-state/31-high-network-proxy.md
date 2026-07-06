> **Part V: Environment & State** | Challenge §31

## 31. Network Proxy Unawareness

**Severity:** High | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Medium | **Time:** High | **Context:** Low

### The Problem

Agent execution environments frequently route traffic through proxies (corporate networks, CI systems, VPNs, transparent proxies). Tools that don't respect standard proxy environment variables fail with misleading network errors that look identical to the target service being down.

**Tool ignores proxy env vars:**
```bash
$ export HTTPS_PROXY=http://proxy.corp.example.com:8080
$ tool fetch-data --url https://api.example.com
# Tool uses requests.get() without proxies= argument
# Directly connects: connection refused (blocked by firewall)
# Agent sees: "Error: connection refused to api.example.com"
# Agent thinks: API is down. Retries 3 times. Reports failure.
# Reality: proxy not used
```

**Proxy auth not supported:**
```bash
$ export HTTPS_PROXY=http://user:pass@proxy.corp.example.com:8080
$ tool sync
# Tool reads HTTPS_PROXY but doesn't support auth
# Proxy returns 407 Proxy Auth Required
# Tool: "Error: unexpected 407 response"
# Agent: doesn't know what 407 means in this context
```

**SSL certificate interception:**
```bash
# Corporate proxy does SSL inspection, presents its own cert
$ tool fetch-schema --url https://api.example.com
# Tool doesn't use system cert store → SSL verification fails
# Error: "certificate verify failed: unable to get local issuer certificate"
# Looks like a server cert error, actually a proxy issue
```

**No-proxy list ignored:**
```bash
$ export NO_PROXY=localhost,internal.corp.example.com
$ tool call-internal --url http://internal.corp.example.com/api
# Tool sends request through proxy anyway
# Internal service not reachable via proxy → connection refused
```

### Impact

- Network errors indistinguishable from service outages
- Agent retries against service that is actually up but unreachable
- SSL errors misdiagnosed as server certificate problems
- No actionable error message: "connection refused" tells agent nothing about proxy

### Solutions

**Respect all standard proxy env vars:**
```python
import urllib.request
# Python requests library — auto-reads env vars:
import requests
session = requests.Session()
# requests automatically reads: HTTP_PROXY, HTTPS_PROXY, NO_PROXY
# This is the default — don't override it with proxies={}

# For lower-level: urllib respects env vars by default
# Never do: urllib.request.urlopen(url, context=ssl_context_that_ignores_env)
```

**Use system certificate store:**
```python
import ssl, certifi
# Use certifi for cross-platform cert bundle
ctx = ssl.create_default_context(cafile=certifi.where())
# Or respect REQUESTS_CA_BUNDLE env var
```

**Include proxy info in network error output:**
```json
{
  "ok": false,
  "error": {
    "code": "NETWORK_CONNECTION_FAILED",
    "message": "Cannot reach api.example.com",
    "network_context": {
      "proxy_used": "http://proxy.corp.example.com:8080",
      "proxy_source": "HTTPS_PROXY env var",
      "no_proxy": "localhost,internal.corp",
      "ssl_verify": true
    },
    "suggestion": "Check proxy connectivity: curl -x $HTTPS_PROXY https://api.example.com"
  }
}
```

**`--proxy` explicit override:**
```bash
tool fetch-data --proxy http://proxy.corp.example.com:8080
tool fetch-data --no-proxy   # bypass proxy for this call
```

**For framework design:**
- Framework HTTP client reads `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` automatically
- Network errors include `network_context` block showing proxy settings used
- `tool doctor` checks: can reach key endpoints with current proxy config
- `--proxy` and `--no-proxy` are framework-level flags on all network commands

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Tool ignores `HTTPS_PROXY` / `HTTP_PROXY`; network errors give no proxy context; `NO_PROXY` not respected |
| 1 | Tool reads proxy env vars but network errors don't indicate which proxy was used; `NO_PROXY` may be ignored |
| 2 | Proxy env vars respected including `NO_PROXY`; network errors include `network_context.proxy_used`; system cert store used |
| 3 | `--proxy` and `--no-proxy` flags available; `network_context` in all network errors; `tool doctor` verifies connectivity through current proxy config |

**Check:** Set `HTTPS_PROXY` to a non-existent proxy and run a network command — verify the error output includes `network_context.proxy_used` identifying the proxy that was attempted.

---

### Agent Workaround

**Signature:** network command fails with `connection refused`, `407`, or `certificate verify failed` while `HTTPS_PROXY` is set and the target service is up

**Tier:** B (one observable check, then one command)

**Propagate proxy env vars explicitly to subprocesses; diagnose network errors using `network_context`:**

```python
import subprocess, json, os

# Ensure proxy vars are forwarded (they usually are, but be explicit)
proxy_env = {
    k: v for k, v in os.environ.items()
    if k.upper() in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY")
}

result = subprocess.run(
    ["tool", "fetch-data", "--url", url, "--output", "json"],
    capture_output=True, text=True,
    env={**os.environ, **proxy_env},
)
parsed = json.loads(result.stdout)

if not parsed.get("ok"):
    error = parsed.get("error", {})
    net = error.get("network_context", {})
    if net:
        proxy_used = net.get("proxy_used")
        if proxy_used:
            # Network error went through a proxy — check proxy connectivity
            print(f"Connection failed via proxy {proxy_used}: {error['message']}")
        else:
            # Direct connection failed
            print(f"Direct connection failed: {error['message']}")
```

**Use `tool doctor` to verify proxy connectivity before network-dependent operations:**
```python
def check_network(tool: str) -> bool:
    result = subprocess.run(
        [tool, "doctor", "--output", "json"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
        checks = {c["name"]: c for c in data.get("checks", [])}
        return checks.get("network_connectivity", {}).get("ok", True)
    except (json.JSONDecodeError, KeyError):
        return True  # assume ok if doctor not supported
```

**Limitation:** If the tool's network errors say only "connection refused" with no `network_context`, the agent cannot distinguish a proxy misconfiguration from the target service being down — check `HTTPS_PROXY` value manually and test with `curl -x $HTTPS_PROXY <url>` before assuming service failure
