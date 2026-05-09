# Output And Parsing

> How CLI tools format, stream, and structure their output for agent consumption.

**Failure modes:** 10 active &nbsp;|&nbsp; 🔴 2 critical · 🟠 5 high · 🟡 3 medium

---

| File | Severity | Summary |
|------|----------|---------|
| [01-critical-exit-codes.md](01-critical-exit-codes.md) | 🔴 Critical | The most fundamental contract between a CLI tool and its caller is the exit code |
| [02-critical-output-format.md](02-critical-output-format.md) | 🔴 Critical | Agents parse command output to determine what happened and extract values for subsequent steps |
| [03-high-stderr-stdout.md](03-high-stderr-stdout.md) | 🟠 High | Unix convention: stdout = data, stderr = diagnostics |
| [05-high-pagination.md](05-high-pagination.md) | 🟠 High | Commands that return large datasets in a single response create multiple problems: the output may be too large to par... |
| [08-high-ansi-leakage.md](08-high-ansi-leakage.md) | 🟠 High | ANSI escape sequences (colors, bold, cursor movement) are designed for TTY display |
| [09-high-binary-encoding.md](09-high-binary-encoding.md) | 🟠 High | CLI tools that read files, databases, or APIs may encounter binary data, null bytes, or non-UTF-8 strings |
| [76-high-streaming-default-incompatibility.md](76-high-streaming-default-incompatibility.md) | 🟠 High | Commands that emit JSONL by default break agents that parse stdout with `json.loads()` |
| [04-medium-verbosity.md](04-medium-verbosity.md) | 🟡 Medium | Every byte of CLI output that reaches the agent consumes tokens from its context window |
| [06-medium-command-composition.md](06-medium-command-composition.md) | 🟡 Medium | Agents often need to chain commands: get an ID from one command, pass it to another |
| [07-medium-output-nondeterminism.md](07-medium-output-nondeterminism.md) | 🟡 Medium | Agents compare outputs, cache results, detect changes, and build logic on top of command results |

## Detailed Metrics

| Challenge | Severity | Frequency | Detectability | Token Spend | Time | Context |
|-----------|----------|-----------|---------------|-------------|------|---------|
| [§1](01-critical-exit-codes.md) | 🔴 Critical | Very Common | Hard | High | High | Low |
| [§2](02-critical-output-format.md) | 🔴 Critical | Very Common | Easy | High | Medium | High |
| [§3](03-high-stderr-stdout.md) | 🟠 High | Very Common | Hard | Medium | Low | High |
| [§5](05-high-pagination.md) | 🟠 High | Common | Hard | High | High | Critical |
| [§8](08-high-ansi-leakage.md) | 🟠 High | Common | Hard | Medium | Low | Medium |
| [§9](09-high-binary-encoding.md) | 🟠 High | Situational | Hard | Low | Medium | Low |
| [§76](76-high-streaming-default-incompatibility.md) | 🟠 High | Situational | Medium | Medium | Low | Medium |
| [§4](04-medium-verbosity.md) | 🟡 Medium | Very Common | Easy | High | Low | High |
| [§6](06-medium-command-composition.md) | 🟡 Medium | Common | Easy | Medium | Low | Low |
| [§7](07-medium-output-nondeterminism.md) | 🟡 Medium | Common | Hard | Medium | Medium | Low |
