# REQ-F-042: Log Rotation in Framework Logger

**Tier:** Framework-Automatic | **Priority:** P3

**Source:** [§30 Undeclared Filesystem Side Effects](../challenges/05-high-environment-and-state/30-medium-filesystem-side-effects.md)

**Addresses:** Severity: Medium / Token Spend: Low / Time: Low / Context: Low

---

## Description

The framework's internal logger MUST automatically rotate log files when they exceed a configurable maximum size (default: 100 MB) and MUST retain a configurable maximum number of rotated files (default: 5). The framework MUST prune log files older than a configurable maximum age (default: 30 days). These defaults MUST be configurable via framework-level configuration, not requiring per-command implementation.

## Acceptance Criteria

- A log file that exceeds the size limit is rotated and a new file is started
- Rotated files beyond the retention count are deleted automatically
- Log files older than the maximum age are deleted on framework startup
- Disk usage from framework logs is bounded even across unlimited invocations

---

## Schema

No dedicated schema type — this requirement governs the framework's internal log rotation behavior without adding new wire-format fields

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only

---

## Example

Framework-Automatic: no command author action needed. The framework rotates log files when they exceed the configured size threshold.

```
# Default framework configuration (no author action required)
framework.logger:
  max_size_mb: 100        # rotate when log file exceeds 100 MB
  max_rotated_files: 5    # keep at most 5 rotated files
  max_age_days: 30        # prune files older than 30 days on startup

# Log directory after rotation:
~/.mycli/logs/
  cli.log          # current log file
  cli.log.1        # most recent rotated file
  cli.log.2
  cli.log.3
  cli.log.4
  cli.log.5
  cli.log.6.gz     # → automatically deleted (exceeds max_rotated_files)
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | F | Composes: session temp directories are also cleaned up by the framework |
| [REQ-F-026](f-026-append-only-audit-log.md) | F | Composes: audit log is a separate append-only file subject to the same rotation policy |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Enforces: log entries in all verbosity modes have secrets redacted before rotation |
