# REQ-F-066: Subprocess Locale Normalization

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** [§57 Locale-Dependent Error Messages](../challenges/01-critical-ecosystem-runtime-agent-specific/57-medium-locale-errors.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Low / Context: Medium

---

## Description

The framework MUST set `LC_ALL=C` (or `LC_MESSAGES=C` and `LANG=C`) in the environment of all spawned subprocesses unless the command explicitly opts out via `preserve_locale: true`. This ensures that error messages from subprocesses (git, curl, system tools) are always in English and can be reliably pattern-matched. The framework MUST also normalize number formatting (decimal separators, thousands separators) by setting `LC_NUMERIC=C` in subprocess environments, preventing locale-dependent numeric output from breaking JSON parsing. The locale override applies only to spawned subprocesses; the framework itself always serializes using invariant locale (covered by REQ-F-005).

## Acceptance Criteria

- `git` error messages are in English regardless of the system locale
- A subprocess that would normally emit `1.234,56` in a German locale emits `1234.56` under framework management
- A command with `preserve_locale: true` does not have `LC_ALL=C` injected for its subprocesses
- The parent process locale is unaffected; only subprocess environments are modified

---

## Schema

No dedicated schema type — this requirement governs subprocess environment injection without adding new wire-format fields.

---

## Wire Format

No wire-format fields — this requirement governs framework behavior only.

---

## Example

Framework-Automatic: no command author action needed. The framework sets `LC_ALL=C` and `LC_NUMERIC=C` in the environment of every spawned subprocess.

```
# System locale is German (de_DE)
# Without framework: git outputs German error messages
git push → "Fehler: Zugriff verweigert"

# With framework: LC_ALL=C injected into subprocess env
framework.exec(["git", "push"])
→ "error: access denied"
→ pattern-matchable by any agent

# preserve_locale: true opt-out
register command "localize":
  preserve_locale: true
→ LC_ALL not injected; subprocess uses system locale
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-005](f-005-locale-invariant-serialization.md) | F | Composes: locale-invariant serialization ensures the framework's own output is also locale-clean |
| [REQ-F-062](f-062-glob-expansion-and-word-splitting-prevention.md) | F | Composes: locale injection is applied at the same subprocess-spawn point as array-form enforcement |
| [REQ-F-030](f-030-child-process-session-tracking.md) | F | Composes: tracked child processes receive the normalized locale environment |
| [REQ-F-016](f-016-utf-8-sanitization-before-serialization.md) | F | Composes: UTF-8 sanitization and locale normalization together ensure subprocess output is always parseable |
