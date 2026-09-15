# REQ-O-019: --proxy and --no-proxy Flags

**Tier:** Opt-In | **Priority:** P2

**Source:** [§31 Network Proxy Unawareness](../challenges/05-high-environment-and-state/31-high-network-proxy.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework MUST provide `--proxy <url>` (override proxy for this invocation) and `--no-proxy` (bypass proxy for this invocation) as standard flags on all commands that perform network I/O. `--proxy` MUST override `HTTPS_PROXY` and `HTTP_PROXY` environment variables. `--no-proxy` MUST bypass all proxy settings (direct connection). These flags MUST be automatically available on commands that declare `has_network_io: true`.

## Acceptance Criteria

- `--proxy http://proxy.example.com:8080` routes all HTTP requests through that proxy
- `--no-proxy` results in direct connections regardless of `HTTPS_PROXY` env var
- The proxy URL used is reflected in `network_context` in error responses
- The flags are absent on commands that declare no network I/O

---

## Schema

No dedicated schema type — proxy routing is behavioral. The proxy URL in use is surfaced in `error.context.network` on network failures (via REQ-F-037).

---

## Wire Format

No wire-format fields — proxy configuration is not injected into success responses. On network failure, `error.context.network.proxy_used` shows the proxy that was in effect.

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "UNAVAILABLE",
    "message": "Connection refused",
    "context": {
      "network": { "url": "https://api.example.com/v1/deploy", "proxy_used": "http://proxy.corp.example.com:8080" }
    }
  },
  "warnings": [],
  "meta": { "exit_code": 12, "duration_ms": 12 }
}
```

---

## Example

Opt-in: automatically available on commands that declare `has_network_io: true`.

```
register command "deploy":
  has_network_io: true
  # --proxy and --no-proxy are auto-registered by the framework

# Override proxy for this invocation:
$ tool deploy --proxy http://proxy.example.com:8080

# Bypass all proxy settings:
$ tool deploy --no-proxy
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-036](f-036-http-client-proxy-environment-variable-compliance.md) | F | Provides: env-var proxy compliance that `--proxy` and `--no-proxy` override |
| [REQ-F-037](f-037-network-error-context-block.md) | F | Composes: network errors include `proxy_used` from this flag's effective value |
| [REQ-C-012](c-012-commands-with-network-i-o-support-timeout.md) | C | Composes: commands with network I/O declare both timeout and proxy support |
