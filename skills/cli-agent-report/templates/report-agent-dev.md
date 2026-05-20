# {{CLI}} — Integration Guide

**Generated:** {{DATE}}
**CLI version:** {{VERSION}}
**Scope:** {{SCOPE}}

## Invocation Invariants

These constraints must hold on every call to {{CLI}}, regardless of language or framework:

```
binary:  {{BINARY}}
stdin:   closed (DEVNULL / equivalent)
timeout: {{TIMEOUT}}s
env:     {{ENV_LINE_1}}  # {{ENV_SECTIONS_1}} — {{ENV_WHY_1}}
         {{ENV_LINE_N}}  # {{ENV_SECTIONS_N}} — {{ENV_WHY_N}}
flags:   {{FLAG_1}}      # {{FLAG_SECTIONS_1}} — {{FLAG_WHY_1}}
         {{FLAG_N}}      # {{FLAG_SECTIONS_N}} — {{FLAG_WHY_N}}
```

<!-- INSERT output of: scripts/build_invariants.py — deduplicates env/flags across all failing §N workarounds -->
<!-- If environment.md not found: use descriptive placeholders and note "Load evaluations/{{CLI}}/environment.md for actual values." -->
<!-- Omit env: or flags: block entirely if no entries exist for that category -->

---

## Per-Failure-Mode Workarounds  _(score < 3, sorted: severity desc, score asc)_

<!-- REPEAT for each §N where score < 3, ordered by severity desc per config/severity-order.json then score asc -->

### §{{N}} — {{TITLE}}  [{{SEVERITY}} · {{SCORE}}/3]

**Gap:** {{NOTES}}

**Workaround:**
{{AGENT_WORKAROUND_CONTENT}}

---

<!-- END REPEAT -->

## No Action Needed

{{PASSING_LIST}}  _(score 3/3)_

<!-- IF any ?/3 entries — omit section entirely if none -->
## Could Not Verify

{{INDET_LIST}}  _(check timed out — treat as unverified risk; consider adding retry logic or manual observation)_
<!-- END IF -->
