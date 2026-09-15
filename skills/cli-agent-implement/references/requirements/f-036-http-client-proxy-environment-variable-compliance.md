# REQ-F-036: HTTP Client Proxy Environment Variable Compliance

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§31 Network Proxy Unawareness](../challenges/05-high-environment-and-state/31-high-network-proxy.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: High / Context: Low

---

## Description

The framework's built-in HTTP client MUST automatically read and apply `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment variables. The framework MUST support proxy authentication (credentials in proxy URL). The framework MUST use the system certificate store or a configurable CA bundle path (respecting `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE` environment variables). These behaviors MUST be on by default with no additional configuration from command authors.

## Acceptance Criteria

- When `HTTPS_PROXY` is set, all outbound HTTPS requests from the framework's HTTP client use that proxy
- When `NO_PROXY=localhost`, requests to `localhost` bypass the proxy
- When `REQUESTS_CA_BUNDLE` is set, the specified CA bundle is used for SSL verification
- A command author who uses the framework's HTTP client does not need to write any proxy handling code

---

## Schema

No dedicated schema type — this requirement governs HTTP client initialization behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework initializes its HTTP client singleton by reading `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` from the environment before the first request is made.

```
$ HTTPS_PROXY=http://proxy.corp:3128 tool api call --endpoint /users
→ all HTTPS requests routed through http://proxy.corp:3128
→ no proxy configuration code required in the command

$ NO_PROXY=localhost,127.0.0.1 HTTPS_PROXY=http://proxy.corp:3128 tool api call --endpoint /users
→ requests to localhost bypass the proxy

$ REQUESTS_CA_BUNDLE=/etc/ssl/custom-ca.pem tool api call --endpoint /users
→ custom CA bundle used for SSL verification
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-037](f-037-network-error-context-block.md) | F | Extends: network errors expose which proxy env vars were active when the failure occurred |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: non-interactive mode detection used to suppress proxy auth prompts |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: response envelope used to surface any resulting network errors |
