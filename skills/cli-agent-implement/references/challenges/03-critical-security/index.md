# Security

> Destructive operations, authentication, secret handling, and prompt injection.

**Failure modes:** 5 active &nbsp;|&nbsp; 🔴 5 critical

---

| File | Severity | Summary |
|------|----------|---------|
| [23-critical-destructive-ops.md](23-critical-destructive-ops.md) | 🔴 Critical | Agents may execute destructive commands without fully understanding consequences, especially when operating autonomou... |
| [24-critical-auth-secrets.md](24-critical-auth-secrets.md) | 🔴 Critical | CLI tools often need credentials |
| [25-critical-prompt-injection.md](25-critical-prompt-injection.md) | 🔴 Critical | CLI tool output is fed directly into the agent's context |
| [74-critical-credential-scope-declaration.md](74-critical-credential-scope-declaration.md) | 🔴 Critical | CLI tools accept any credential without declaring what permissions each command requires, giving agents full account blast radius |
| [75-critical-safe-default-execution.md](75-critical-safe-default-execution.md) | 🔴 Critical | High-stakes commands execute immediately with real side effects; agents have no way to preview impact without explicitly remembering --dry-run at every callsite |

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§23](23-critical-destructive-ops.md) | 🔴 Critical | Common | Medium | Medium | High | Medium |
| [§24](24-critical-auth-secrets.md) | 🔴 Critical | Common | Hard | Medium | Medium | Low |
| [§25](25-critical-prompt-injection.md) | 🔴 Critical | Situational | Hard | High | High | High |
| [§74](74-critical-credential-scope-declaration.md) | 🔴 Critical | Common | Hard | Low | Medium | Low |
| [§75](75-critical-safe-default-execution.md) | 🔴 Critical | Situational | Hard | Low | Critical | Low |
