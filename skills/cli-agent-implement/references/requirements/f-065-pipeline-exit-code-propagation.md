# REQ-F-065: Pipeline Exit Code Propagation

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§56 Exit Code Masking in Shell Pipelines](../challenges/01-critical-ecosystem-runtime-agent-specific/56-high-pipeline-exit-masking.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Low

---

## Description

When the framework invokes multi-stage shell pipelines internally, it MUST use `set -o pipefail` (or language-level equivalent) so that a failure in any stage of the pipeline propagates as the pipeline's exit code. The framework MUST NOT use the pattern `cmd | other_cmd` without capturing intermediate exit codes. For language runtimes that do not support `pipefail` natively, the framework MUST use explicit pipe handling that checks each stage's exit code. The framework MUST document this behavior in its subprocess API and warn (at framework startup) if the calling shell does not have `pipefail` set.

## Acceptance Criteria

- A pipeline where the first stage fails exits with the first stage's non-zero code, not 0
- The framework's subprocess API raises an error for any pipeline stage failure, not just the last
- A pipeline `cmd1 | cmd2` where `cmd1` exits 1 and `cmd2` exits 0 results in overall exit 1
- Framework startup emits a warning when `pipefail` is not set in the parent shell environment

---

## Schema

No dedicated schema type — this requirement governs pipeline exit code propagation behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework always flushes and closes stdout before exiting, and uses `pipefail`-equivalent handling in all internal pipelines.

```
# Internal pipeline: cmd1 | cmd2 — cmd1 exits 1
framework.pipe(["cmd1"], ["cmd2"])
→ framework detects cmd1 exit 1; raises PipelineError(stage=0, code=1)
→ overall process exits 1, not 0

# External shell without pipefail — framework warns at startup
$ mytool deploy
→ [WARN] Parent shell does not have pipefail set; pipeline failures may be masked
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-062](f-062-glob-expansion-and-word-splitting-prevention.md) | F | Composes: array-form subprocess API is prerequisite for reliable exit code capture |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: child process tracking ensures all pipeline stages are monitored |
| [REQ-F-013](f-013-sigterm-handler-installation.md) | F | Composes: SIGTERM handler ensures stdout is flushed before the process exits in a pipeline |
| [REQ-F-014](f-014-sigpipe-handler-installation.md) | F | Composes: SIGPIPE handler governs behavior when the downstream consumer closes the pipe |
