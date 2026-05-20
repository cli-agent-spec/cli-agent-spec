# {{CLI}} — Fix Report

**Generated:** {{DATE}}
**CLI version:** {{VERSION}}
**Scope:** {{SCOPE}}
**In findings:** {{N_FINDINGS}} failure modes evaluated

## Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Indeterminate (?) |
|---|---|---|---|---|
| Critical | {{CRIT_PASS}} | {{CRIT_PARTIAL}} | {{CRIT_FAIL}} | {{CRIT_INDET}} |
| High | {{HIGH_PASS}} | {{HIGH_PARTIAL}} | {{HIGH_FAIL}} | {{HIGH_INDET}} |
| Medium | {{MED_PASS}} | {{MED_PARTIAL}} | {{MED_FAIL}} | {{MED_INDET}} |

---

## Required Fixes  _(score < 3, sorted: severity desc, score asc)_

<!-- REPEAT for each §N where score < 3, ordered by severity desc per config/severity-order.json then score asc -->

### §{{N}} — {{TITLE}}  [{{SEVERITY}} · {{SCORE}}/3]

**Gap:** {{NOTES}}

**Solutions:**
{{SOLUTIONS_CONTENT}}

**Requirements that address this:**
<!-- INSERT output of: scripts/lookup_requirements.py §{{N}} -->
- REQ-{{TIER}}-{{NNN}} ({{PRIORITY}}) — {{REQ_TITLE}} [Tier: F = framework handles / C = you declare / O = you opt in]

---

<!-- END REPEAT -->

## Already Passing

{{PASSING_LIST}}  _(score 3/3 — no action needed)_

<!-- IF any ?/3 entries — omit section entirely if none -->
## Could Not Verify

{{INDET_LIST}}  _(check timed out — behavior unknown; treat as unverified risk)_
<!-- END IF -->
