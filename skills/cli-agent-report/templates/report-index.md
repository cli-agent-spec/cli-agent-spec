# {{CLI}} — Evaluation Index

**Generated:** {{DATE}}
**CLI version:** {{VERSION}}
**Scope:** {{SCOPE}}
**Failure modes evaluated:** {{N_FINDINGS}} of 71 _(scope: {{SCOPE}})_

## Score Summary

| Severity | Pass (3/3) | Partial (1–2) | Fail (0) | Total |
|---|---|---|---|---|
| Critical | {{CRIT_PASS}} | {{CRIT_PARTIAL}} | {{CRIT_FAIL}} | {{CRIT_TOTAL}} |
| High | {{HIGH_PASS}} | {{HIGH_PARTIAL}} | {{HIGH_FAIL}} | {{HIGH_TOTAL}} |
| Medium | {{MED_PASS}} | {{MED_PARTIAL}} | {{MED_FAIL}} | {{MED_TOTAL}} |
| **All** | **{{TOTAL_PASS}}** | **{{TOTAL_PARTIAL}}** | **{{TOTAL_FAIL}}** | **{{TOTAL}}** |

**Average score:** {{AVG_SCORE}} / 3

## Readiness Score

<!-- IF evaluations/{{CLI}}/readiness.md exists: render the table below.
     IF /6 depth (quick): render only Dimensions 1–2 rows with total /6.
     IF /15 depth (full): render all five rows.
     IF readiness.md does not exist: replace entire section with:
     "_Readiness not evaluated. Run `/cli-agent-readiness` to populate this section._" -->

| Dimension | Score |
|---|---|
| Documentation Quality | {{DIM1}}/3 |
| Self-Description | {{DIM2}}/3 |
| Pre-built Integrations | {{DIM3}}/3 |
| Setup Reproducibility | {{DIM4}}/3 |
| Workflow Coverage | {{DIM5}}/3 |
| **Total** | **{{READINESS_TOTAL}} [{{READINESS_GRADE}}]** |

## Reports

| Report | Audience | File |
|---|---|---|
| Issues & Problems | AI agents and their builders | [report-issues.md](report-issues.md) |
| Runtime Brief | AI agents at invocation time | [report-runtime.md](report-runtime.md) |
| Integration Guide | Agent developers | [report-agent-dev.md](report-agent-dev.md) |
| Fix List | CLI authors | [report-dev.md](report-dev.md) |

## Top Issues

<!-- 3–5 bullets: highest-impact bugs from issues.md first, then score-0 findings. One clause each. -->

- {{TOP_ISSUE_1}}
- {{TOP_ISSUE_2}}
- {{TOP_ISSUE_3}}

## Observed Bugs

{{BUG_COUNT}} bugs recorded during evaluation — see [report-issues.md](report-issues.md) for details.
