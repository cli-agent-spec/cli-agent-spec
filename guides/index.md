# Guides

> Design guidance for CLI authors. Unlike failure modes (what goes wrong) and requirements (what to enforce), guides capture what to do — positive design principles that cannot be mechanically verified but materially improve agent compatibility.

---

| Guide | Topic | Summary |
|-------|-------|---------|
| [Unix Naming Conventions](unix-naming-conventions.md) | Naming, vocabulary, corpus alignment | How to exploit LLM Unix training as a design asset |
| [Streaming vs Envelope Output](streaming-vs-envelope.md) | Output mode selection | When to stream by default vs return a buffered envelope |
| [Designing AI-Native CLI Commands That Read from stdin](stdin-native-cli.md) | stdin handling, pipe safety | Three failure modes that silently break stdin-reading commands — and the patterns to fix them |
| [The No-Args Entry Point](no-args-entry-point.md) | First-contact discoverability, argparse anti-pattern | Why bare invocation must exit 0 and how the argparse `required=True` default silently breaks agent discovery |
| [Designing CLIs for Skill Optimization](skill-optimizable-design.md) | Skill transferability, optimization prerequisites | How to make CLI behavior learnable and portable across agent runtimes — and which failure modes abort skill training entirely |
| [LLM-Optimized Output Formats](llm-optimized-output-formats.md) | Output format design, token efficiency | When to offer a compact LLM-native format alongside JSON, what it requires, and where it expands the prompt injection surface |
| [Designing a Built-In Batch Dispatch Command](batch-dispatch.md) | Batch execution, JSONL dispatch protocol | When to provide `exec`, how to design the `_cmd`/`_opts` protocol, and safe invocation patterns for agent builders |
| [Designing Errors for Autonomous Recovery](recoverable-errors.md) | Error design, recovery ladder, executable remediation | The four questions every error must answer in machine-readable fields, the three recovery classes, and how to author a safe `fix_command` |
