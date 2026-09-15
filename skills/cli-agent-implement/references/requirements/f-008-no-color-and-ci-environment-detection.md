# REQ-F-008: NO_COLOR and CI Environment Detection

**Tier:** Framework-Automatic | **Priority:** P0

**Source:** [§8 ANSI & Color Code Leakage](../challenges/04-critical-output-and-parsing/08-high-ansi-leakage.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Low / Context: Medium

---

## Description

The framework MUST check for `NO_COLOR` (any value, including empty, per no-color.org), `CI`, `GITHUB_ACTIONS`, `JENKINS_URL`, and `TERM=dumb` at startup. When any of these is present, the framework MUST disable all color and formatting output globally, including for stderr. The framework MUST also set `NO_COLOR=1` in the process environment so that child processes and third-party libraries inherit the setting.

## Acceptance Criteria

- When `NO_COLOR=` (empty string), all ANSI output is disabled
- A child process spawned by the framework inherits `NO_COLOR=1`
- `TERM=dumb` alone is sufficient to disable all color output

---

## Schema

No dedicated schema type — this requirement governs environment detection behavior without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework checks these variables at startup, before any command handler runs.

```
# Any of these env vars triggers color disable + NO_COLOR propagation

$ NO_COLOR= tool deploy         # empty string is sufficient per no-color.org
$ CI=true tool deploy           # CI pipeline detection
$ GITHUB_ACTIONS=true tool deploy
$ JENKINS_URL=http://... tool deploy
$ TERM=dumb tool deploy

# In all cases:
# - No ANSI escape sequences in stdout or stderr
# - Child processes inherit NO_COLOR=1
$ NO_COLOR= tool deploy -- sh -c 'echo $NO_COLOR'
1
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | F | Extends: env detection provides an upstream signal that prevents ANSI injection |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Composes: `CI` and `NO_COLOR` also trigger JSON mode activation |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Composes: color suppression applies to both stdout and stderr streams |
