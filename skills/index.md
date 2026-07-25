# CLI Agent Spec — Skills

Installable agent skills for evaluating CLIs and guiding implementation of the [CLI Agent Spec](../README.md).

Compatible with any [Agent Skills](https://agentskills.io)-enabled agent: Claude Code, Cursor, Gemini CLI, Copilot, and others.

## Skills

| Skill | Purpose |
|-------|---------|
| [`cli-agent-onboard`](cli-agent-onboard/SKILL.md) | Profile a CLI tool once — detects runtime, binary, flags, timeout method |
| [`cli-agent-evaluate`](cli-agent-evaluate/SKILL.md) | Score a CLI against a single failure mode (0–3), with applicable agent workaround |
| [`cli-agent-evaluate-batch`](cli-agent-evaluate-batch/SKILL.md) | Evaluate a CLI across multiple failure modes in one run |
| [`cli-agent-implement`](cli-agent-implement/SKILL.md) | Guide implementing the spec in a CLI framework, tier by tier |
| [`cli-agent-audit`](cli-agent-audit/SKILL.md) | Full autonomous audit — install, onboard, evaluate, and report |
| [`cli-agent-readiness`](cli-agent-readiness/SKILL.md) | Score proactive agent readiness across 5 dimensions |
| [`cli-agent-report`](cli-agent-report/SKILL.md) | Generate perspective-specific reports from evaluation findings |
| [`cli-agent-diagnose`](cli-agent-diagnose/SKILL.md) | Classify a failed agent CLI call against §N failure modes |
| [`validate-links`](validate-links/SKILL.md) | Validate cross-links and schema↔requirement symmetry in the spec |

## Installation

```bash
npx skills install cli-agent-spec/cli-agent-spec/skills/cli-agent-onboard
npx skills install cli-agent-spec/cli-agent-spec/skills/cli-agent-evaluate
npx skills install cli-agent-spec/cli-agent-spec/skills/cli-agent-implement
```
