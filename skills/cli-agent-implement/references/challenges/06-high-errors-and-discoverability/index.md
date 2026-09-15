# Errors And Discoverability

> Error quality, retry guidance, schema discovery, and versioning.

**Failure modes:** 5 active &nbsp;|&nbsp; 🟠 3 high · 🟡 2 medium

---

| File | Severity | Summary |
|------|----------|---------|
| [18-high-error-quality.md](18-high-error-quality.md) | 🟠 High | When a command fails, the agent needs to understand: what failed, why, and what to do next |
| [19-high-retry-hints.md](19-high-retry-hints.md) | 🟠 High | When a command fails, the agent decides: retry immediately, retry after delay, retry with different args, or give up |
| [22-high-schema-versioning.md](22-high-schema-versioning.md) | 🟠 High | Agents built against a tool's output schema break silently when that schema changes |
| [20-medium-dependency-discovery.md](20-medium-dependency-discovery.md) | 🟡 Medium | CLI tools often depend on external tools, services, or specific environment configurations |
| [21-medium-schema-discoverability.md](21-medium-schema-discoverability.md) | 🟡 Medium | Agents need to know what commands exist, what parameters they accept, and what they return — without running commands... |

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§18](18-high-error-quality.md) | 🟠 High | Very Common | Easy | High | Medium | High |
| [§19](19-high-retry-hints.md) | 🟠 High | Very Common | Medium | High | High | Medium |
| [§22](22-high-schema-versioning.md) | 🟠 High | Common | Hard | High | High | Medium |
| [§20](20-medium-dependency-discovery.md) | 🟡 Medium | Common | Easy | Medium | Medium | Low |
| [§21](21-medium-schema-discoverability.md) | 🟡 Medium | Very Common | Easy | High | Medium | Medium |
