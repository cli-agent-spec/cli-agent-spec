> **Part I: Ecosystem, Runtime & Agent-Specific** | Challenge §73

## 73. Documentation Accuracy Drift

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** High | **Time:** Medium | **Context:** Low

### The Problem

AGENTS.md and other agent-facing documentation become inaccurate as the CLI evolves. Unlike §44 (Agent Knowledge Packaging Absence), which covers the case where no documentation exists, this challenge covers documentation that *exists but is wrong*: flag names that changed, commands that were removed, env vars that were renamed, invocation patterns that no longer work, prerequisite sequences that have changed.

An agent that finds AGENTS.md treats it as authoritative — it was written explicitly for agents, so the agent has every reason to trust it. When AGENTS.md is inaccurate, the agent fails confidently, repeatedly, and without understanding why.

```bash
# AGENTS.md documents: use `my-cli auth --token $MY_TOOL_TOKEN`
# CLI v3.0 changed to: `my-cli login --api-key $MY_TOOL_API_KEY`

$ my-cli auth --token $MY_TOOL_TOKEN
Error: unknown command 'auth'   # command renamed in v3.0

# Agent retries with AGENTS.md variations — all fail
# Agent does not fall back to --help because it trusts AGENTS.md
# Result: task failure after many retries, no diagnosis
```

AGENTS.md drift is more dangerous than having no AGENTS.md:
- **Without AGENTS.md:** agent falls back to `--help`, discovers actual interface, succeeds slowly
- **With stale AGENTS.md:** agent trusts wrong information, fails consistently, does not self-correct

Documentation accuracy typically degrades at CLI version boundaries: major versions change flag names, minor versions deprecate flags, patch versions may change env var names. AGENTS.md is rarely updated in the same PR as the CLI change.

### Impact

- Agent fails on every invocation derived from stale documentation — no partial success
- Hard to detect: the agent has no mechanism to know AGENTS.md is wrong without cross-checking against `--help`
- High token spend: agent retries confidently with variations on the stale invocation pattern
- Negative signal: the agent may conclude its understanding of the task is wrong, rather than that the docs are wrong — leading to hallucinated alternative approaches
- Worse than §44: a missing doc causes one-time discovery cost; a stale doc causes ongoing failure with no convergence

### Solutions

**For CLI authors:**

Include a version field in AGENTS.md that agents can compare against `<binary> --version`:

```markdown
<!-- cli-version: 3.1.2 -->
<!-- last-validated: 2026-04-01 -->
# AGENTS.md — My CLI
```

Add AGENTS.md validation to CI — run a script that checks each documented flag and command against `--help` output:

```bash
# ci/validate-agents-md.sh
BINARY_VERSION=$(my-cli --version)
DOC_VERSION=$(grep 'cli-version:' AGENTS.md | sed 's/.*cli-version: //')
if [ "$BINARY_VERSION" != "$DOC_VERSION" ]; then
  echo "AGENTS.md version $DOC_VERSION does not match binary $BINARY_VERSION"
  exit 1
fi
# Spot-check documented flags
for flag in $(grep -oP '\-\-[\w-]+' AGENTS.md); do
  if ! my-cli --help | grep -q "$flag"; then
    echo "Flag $flag in AGENTS.md not found in --help"
    exit 1
  fi
done
```

Update AGENTS.md in the same PR as any flag, command, or env var change — enforce this via PR template or CI gate.

**For framework designers:**

Generate AGENTS.md automatically from registered command schemas. If AGENTS.md cannot drift from the schema, it cannot drift from the binary.

Provide a `--validate-agents-md` command or make `generate-skills` verify existing AGENTS.md against live schema on each run.

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | AGENTS.md exists and contains confirmed inaccuracies — documented commands, flags, or env vars that do not exist or have changed |
| 1 | AGENTS.md is largely accurate but has gaps: undocumented flags, missing env vars, or omitted commands added since last update |
| 2 | AGENTS.md is accurate at time of evaluation but has no version field — freshness unverifiable; no CI gate |
| 3 | AGENTS.md accurate, carries a version field matching `<binary> --version`, and is validated against `--help` in CI |

**Check:** Read AGENTS.md. Extract all flag names, command names, and env var names. Run `<binary> --help` (and subcommand `--help` for documented subcommands). For each documented item, check it appears in `--help` output. Count mismatches. Check for a version field and compare against `<binary> --version`.

### Agent Workaround

Before using AGENTS.md as a planning source, spot-check its accuracy against `--help`:

```
1. Extract the canonical invocation from AGENTS.md
2. Run `<binary> --help` and confirm the top-level command exists
3. For each flag documented in AGENTS.md: confirm it appears in relevant `--help` output
4. If any mismatch found: treat entire AGENTS.md as STALE; fall back to --help as authoritative
5. If AGENTS.md has a version field: compare to `<binary> --version`; mismatch → STALE
```

If AGENTS.md is stale, use `--help` output as the primary planning source and report the specific discrepancies found (expected flag, actual error) in task notes for the human operator.

**Limitation:** Spot-checking covers only the flags the agent happens to verify. A stale AGENTS.md may be accurate for common flags but wrong for edge-case flags the agent only encounters mid-task.
