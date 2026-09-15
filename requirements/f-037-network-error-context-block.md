# REQ-F-037: Network Error Context Block

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§31 Network Proxy Unawareness](../challenges/05-high-environment-and-state/31-high-network-proxy.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

When any network operation fails, the framework MUST include a `network_context` block in the error object containing: `proxy_used` (URL or null), `proxy_source` (which env var or config), `no_proxy` (value or null), `ssl_verify` (boolean), and a `suggestion` field with a concrete diagnostic command. This block MUST be populated by the framework automatically without command author effort.

## Acceptance Criteria

- A connection failure error includes `error.network_context.proxy_used`
- When no proxy is configured, `error.network_context.proxy_used` is null (not absent)
- `error.network_context.suggestion` contains an executable shell command for diagnosing the failure
- The network_context block is absent for non-network errors

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

`error.network_context` is a framework-injected sub-object within `ErrorDetail`, present only for network failures

---

## Wire Format

Network error response with `network_context` block:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "Failed to connect to api.example.com:443",
    "retryable": true,
    "network_context": {
      "url": "https://api.example.com/v1/users",
      "status_code": null,
      "proxy_used": "http://proxy.corp:3128",
      "proxy_source": "HTTPS_PROXY",
      "no_proxy": "localhost,127.0.0.1",
      "ssl_verify": true,
      "suggestion": "curl -v --proxy http://proxy.corp:3128 https://api.example.com/v1/users"
    }
  },
  "warnings": [],
  "meta": { "exit_code": 12, "duration_ms": 30012, "request_id": "req_01HZ" }
}
```

---

## Example

Framework-Automatic: no command author action needed. The framework's HTTP client catch path populates `network_context` from its own internal state (proxy config, SSL config, resolved URL) before constructing the error response.

```
$ HTTPS_PROXY=http://proxy.corp:3128 tool api call --endpoint /users
→ connection refused at proxy
→ error.network_context.proxy_used: "http://proxy.corp:3128"
→ error.network_context.proxy_source: "HTTPS_PROXY"
→ error.network_context.suggestion: "curl -v --proxy http://proxy.corp:3128 https://api.example.com/v1/users"

$ tool api call --endpoint /users   (no proxy set)
→ DNS failure
→ error.network_context.proxy_used: null
→ error.network_context.suggestion: "curl -v https://api.example.com/v1/users"
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-036](f-036-http-client-proxy-environment-variable-compliance.md) | F | Provides: proxy configuration that populates `network_context.proxy_used` and `proxy_source` |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `error` envelope field that carries the `network_context` block |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Provides: `UNAVAILABLE (12)` and `TIMEOUT (10)` exit codes used for network failures |
