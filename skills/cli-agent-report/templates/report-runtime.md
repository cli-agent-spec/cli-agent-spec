# {{CLI}} — Runtime Brief

Generated: {{DATE}} | CLI version: {{VERSION}} | Findings: {{N_FINDINGS}} failure modes | Scope: {{SCOPE}}

## Invoke As

`{{BINARY}}`

## Always Include

<!-- Collect every flag and env var from Agent Workaround sections of failing §N that must apply on every invocation. One row per distinct flag/var. -->

| Flag / Env var | Reason | §N |
|---|---|---|
| {{FLAG_OR_ENV}} | {{WHY}} | {{SECTIONS}} |

<!-- Omit rows that apply only in specific scenarios, not every call -->

## Never Do

<!-- Extract Limitation lines and explicit "do not / never / avoid" statements from workaround sections. -->

| Action | Risk | §N |
|---|---|---|
| {{FORBIDDEN_ACTION}} | {{CONSEQUENCE}} | {{SECTIONS}} |

## Watch in Output

<!-- Extract pattern-matching guidance (regex, string literals, stderr patterns) from workaround sections. -->

| Pattern | Meaning | Action |
|---|---|---|
| {{PATTERN}} | {{SIGNAL}} | {{RESPONSE}} |

<!-- Omit table if no patterns found -->

## Score Summary

<!-- All §N in scope, sorted Critical → High → Medium, within group §N ascending -->

| §N | Title | Severity | Score |
|---|---|---|---|
| §{{N}} | {{TITLE}} | {{SEVERITY}} | {{SCORE}}/3 |

**Worst gaps (score 0):** {{SCORE_0_LIST}}
**Partial (score 1–2):** {{SCORE_1_2_LIST}}
**Indeterminate (?/3 — timed out):** {{INDET_LIST}}
**Passing:** {{PASSING_LIST}}

<!-- Omit any **label:** line if the list is empty -->
<!-- Target: 80 lines total. Omit prose headers, bullet explanations, and implementation context. -->
