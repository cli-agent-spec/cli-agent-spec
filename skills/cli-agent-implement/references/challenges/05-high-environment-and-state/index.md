# Environment And State

> Session state, configuration, working directory, filesystem, network, and runtime environment.

**Failure modes:** 7 active &nbsp;|&nbsp; 🟠 4 high · 🟡 3 medium

---

| File | Severity | Summary |
|------|----------|---------|
| [26-high-session-management.md](26-high-session-management.md) | 🟠 High | Some CLIs maintain state between invocations (login sessions, active contexts, selected environments) |
| [28-high-config-shadowing.md](28-high-config-shadowing.md) | 🟠 High | Most CLI tools load config from multiple locations in a priority order |
| [31-high-network-proxy.md](31-high-network-proxy.md) | 🟠 High | Agent execution environments frequently route traffic through proxies (corporate networks, CI systems, VPNs, transpar... |
| [32-high-self-update.md](32-high-self-update.md) | 🟠 High | Some CLI tools automatically check for updates, download new versions, or silently upgrade themselves |
| [27-medium-platform-portability.md](27-medium-platform-portability.md) | 🟡 Medium | Agent environments vary: macOS, Linux, Docker containers, CI runners |
| [29-medium-working-directory.md](29-medium-working-directory.md) | 🟡 Medium | Many CLI tools resolve paths, find config files, or change behavior based on the current working directory |
| [30-medium-filesystem-side-effects.md](30-medium-filesystem-side-effects.md) | 🟡 Medium | Tools write to locations the agent doesn't know about: caches, logs, lock files, temp dirs, credential stores |

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§26](26-high-session-management.md) | 🟠 High | Common | Hard | Medium | Medium | Low |
| [§28](28-high-config-shadowing.md) | 🟠 High | Common | Hard | High | High | Medium |
| [§31](31-high-network-proxy.md) | 🟠 High | Situational | Hard | Medium | High | Low |
| [§32](32-high-self-update.md) | 🟠 High | Situational | Hard | Medium | High | Low |
| [§27](27-medium-platform-portability.md) | 🟡 Medium | Common | Easy | Medium | Medium | Low |
| [§29](29-medium-working-directory.md) | 🟡 Medium | Common | Medium | Medium | Low | Low |
| [§30](30-medium-filesystem-side-effects.md) | 🟡 Medium | Common | Hard | Low | Low | Low |
