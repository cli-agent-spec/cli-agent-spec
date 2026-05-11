# Guides

> Design guidance for CLI authors. Unlike failure modes (what goes wrong) and requirements (what to enforce), guides capture what to do — positive design principles that cannot be mechanically verified but materially improve agent compatibility.

---

| Guide | Topic | Summary |
|-------|-------|---------|
| [Unix Naming Conventions](unix-naming-conventions.md) | Naming, vocabulary, corpus alignment | How to exploit LLM Unix training as a design asset |
| [Streaming vs Envelope Output](streaming-vs-envelope.md) | Output mode selection | When to stream by default vs return a buffered envelope |
| [Designing AI-Native CLI Commands That Read from stdin](stdin-native-cli.md) | stdin handling, pipe safety | Three failure modes that silently break stdin-reading commands — and the patterns to fix them |
