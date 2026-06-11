# Execution And Reliability

> Execution flow, blocking behavior, atomicity, and reliability under agent orchestration.

**Failure modes:** 9 active &nbsp;|&nbsp; 🔴 4 critical · 🟠 4 high · 🟡 1 medium

---

| File | Severity | Summary |
|------|----------|---------|
| [10-critical-interactivity.md](10-critical-interactivity.md) | 🔴 Critical | Agents run in non-interactive environments |
| [11-critical-timeouts.md](11-critical-timeouts.md) | 🔴 Critical | Agents have finite time budgets per tool call |
| [12-critical-idempotency.md](12-critical-idempotency.md) | 🔴 Critical | Agents retry on failure |
| [13-critical-partial-failure.md](13-critical-partial-failure.md) | 🔴 Critical | Multi-step commands can fail mid-execution, leaving the system in an unknown intermediate state |
| [14-high-arg-validation.md](14-high-arg-validation.md) | 🟠 High | Many CLI tools begin executing — creating files, sending requests, modifying state — before validating all their argu... |
| [15-high-race-conditions.md](15-high-race-conditions.md) | 🟠 High | Agents may invoke multiple tool calls in parallel |
| [16-high-signal-handling.md](16-high-signal-handling.md) | 🟠 High | Agents enforce time budgets by killing processes (SIGTERM, then SIGKILL) |
| [17-medium-child-process-leakage.md](17-medium-child-process-leakage.md) | 🟡 Medium | CLI tools frequently spawn background processes — log forwarders, file watchers, health monitors, connection pools |
| [77-high-no-batch-dispatch.md](77-high-no-batch-dispatch.md) | 🟠 High | No batch dispatch command forces agents to shell out once per operation, exhausting the tool-call budget |

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§10](10-critical-interactivity.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§11](11-critical-timeouts.md) | 🔴 Critical | Common | Hard | High | Critical | Low |
| [§12](12-critical-idempotency.md) | 🔴 Critical | Common | Hard | High | High | Medium |
| [§13](13-critical-partial-failure.md) | 🔴 Critical | Common | Hard | High | High | Medium |
| [§14](14-high-arg-validation.md) | 🟠 High | Common | Medium | Medium | Medium | Low |
| [§15](15-high-race-conditions.md) | 🟠 High | Situational | Hard | Medium | Medium | Low |
| [§16](16-high-signal-handling.md) | 🟠 High | Situational | Hard | Medium | Medium | Low |
| [§17](17-medium-child-process-leakage.md) | 🟡 Medium | Situational | Hard | Low | Low | Low |
| [§77](77-high-no-batch-dispatch.md) | 🟠 High | Common | Easy | High | High | Medium |
