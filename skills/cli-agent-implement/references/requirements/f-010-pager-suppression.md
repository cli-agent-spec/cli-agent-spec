# REQ-F-010: Pager Suppression

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Critical / Context: Low

---

## Description

The framework MUST set `PAGER=cat` and `GIT_PAGER=cat` in the process environment before executing any command. The framework MUST NOT invoke any pager program for its own output. Any child process spawned by the framework inherits these environment variable overrides.

## Acceptance Criteria

- Running any command with a large output does not block on pager input
- `echo $PAGER` in a child shell spawned by a framework command returns `cat`
- `git log` executed as a sub-command from within a framework command does not open a pager

---

## Schema

No dedicated schema type — this requirement governs environment variable enforcement without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework sets `PAGER=cat` and `GIT_PAGER=cat` in the process environment before invoking any command handler.

```
# Framework sets at startup:
os.environ["PAGER"] = "cat"
os.environ["GIT_PAGER"] = "cat"

# Child process spawned by a command handler inherits the override
$ tool repo-summary
# internally runs: git log --oneline -20
# git respects GIT_PAGER=cat → output flows through without blocking

# Verify propagation
$ tool run-shell -- sh -c 'echo $PAGER'
cat
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | F | Composes: both requirements suppress blocking interactive behavior |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: pager suppression ensures output flows directly to the framework's stream routing |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | F | Composes: `PAGER=cat` is set alongside `NO_COLOR` at the same startup phase |
