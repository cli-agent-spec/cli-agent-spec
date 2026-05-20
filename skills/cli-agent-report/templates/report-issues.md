# {{CLI}} — Issues Report

**Generated:** {{DATE}}
**CLI version:** {{VERSION}}
**Scope:** {{SCOPE}}
**Findings in scope:** {{N_FINDINGS}} failure modes

---

## Observed Bugs  _(from evaluation notes)_

These were witnessed directly when running checks against this CLI.

<!-- REPEAT for each entry in evaluations/{{CLI}}/issues.md within scope -->
<!-- If issues.md has no entries: replace section body with "No issues recorded during evaluation." -->

### {{BUG_SECTION_TAG}} — {{BUG_HEADLINE}}

**Discovered during:** {{BUG_SECTION}} evaluation — {{BUG_DATE}}
**Symptom:** {{BUG_SYMPTOM}}
**Impact:** {{BUG_IMPACT}}
**Trigger:** {{BUG_TRIGGER}}

<!-- Omit Trigger line if not recorded in trace.md -->

---

<!-- END REPEAT -->

---

## Failure-Mode Gaps  _(score 0–2, sorted: score asc, severity desc; ?/3 entries listed last)_

These are not confirmed bugs but verified gaps — the CLI does not meet the bar for reliable agent use. `?/3` entries (check timed out) are included at the end with **What fails:** check timed out — behavior unknown.

<!-- REPEAT for each §N where score < 3, sorted score asc then severity desc; append ?/3 last -->

### §{{N}} — {{TITLE}}  [{{SEVERITY}} · score {{SCORE}}/3]

**What fails:** {{NOTES}}
**Frequency:** {{FREQUENCY}}
**Token/time cost when it triggers:** Token Spend: {{TOKEN_SPEND}} · Time: {{TIME_COST}}
**Workaround exists:** {{WORKAROUND_EXISTS}}

<!-- WORKAROUND_EXISTS values: Yes / Partial / No
     Yes = Agent Workaround section present with no Limitation line
     Partial = Agent Workaround section present and has a Limitation line
     No = no Agent Workaround section -->

---

<!-- END REPEAT -->

---

## Passing  _(score 3/3 — safe to use without special handling)_

{{PASSING_WITH_TITLES}}

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | {{BUG_COUNT}} | {{BUG_SECTIONS}} |
| Score 0 — complete failure | {{SCORE_0_COUNT}} | {{SCORE_0_LIST}} |
| Score 1 — major gap | {{SCORE_1_COUNT}} | {{SCORE_1_LIST}} |
| Score 2 — minor gap | {{SCORE_2_COUNT}} | {{SCORE_2_LIST}} |
| Score 3 — passing | {{SCORE_3_COUNT}} | {{SCORE_3_LIST}} |
| Indeterminate (?/3 — timed out) | {{INDET_COUNT}} | {{INDET_LIST}} |

**Highest-risk combination:** {{HIGHEST_RISK_SENTENCE}}
