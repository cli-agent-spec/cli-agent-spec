# REQ-O-046: AGENTS.md CI Validation

**Tier:** Opt-In | **Priority:** P2

**Source:** [§73 Documentation Accuracy Drift](../challenges/01-critical-ecosystem-runtime-agent-specific/73-high-documentation-accuracy-drift.md) · [§44 Agent Knowledge Packaging Absence](../challenges/01-critical-ecosystem-runtime-agent-specific/44-medium-knowledge-packaging.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: High

---

## Description

The CLI's CI pipeline MUST include a validation step that checks AGENTS.md accuracy against the live binary. The validation MUST: (1) compare the `<!-- cli-version: -->` field in AGENTS.md against `<binary> --version` and fail if they differ; (2) extract every flag name, command name, and env var name documented in AGENTS.md and confirm each appears in `<binary> --help` output; (3) fail the CI build if any discrepancy is found. The validation step MUST run on every commit that touches either AGENTS.md or any source file that affects CLI commands or flags.

## Acceptance Criteria

- CI includes a step that runs AGENTS.md validation on every relevant commit
- Version mismatch between `<!-- cli-version: -->` and `<binary> --version` fails CI
- Any flag, command, or env var in AGENTS.md not found in `--help` output fails CI
- CI step produces a diff-style report listing exactly which items are mismatched
- The validation step is documented in AGENTS.md under `## CI Validation` so agents know it exists

---

## Schema

**Types:** none — CI validation produces a human-readable diff report; no JSON schema

---

## Wire Format

```bash
# ci/validate-agents-md.sh — run in CI on every commit touching AGENTS.md or CLI source

BINARY_VERSION=$(my-cli --version | tr -d '[:space:]')
DOC_VERSION=$(grep -oP '(?<=cli-version: )\S+' AGENTS.md | tr -d '[:space:]')

if [ "$BINARY_VERSION" != "$DOC_VERSION" ]; then
  echo "FAIL: AGENTS.md cli-version ($DOC_VERSION) != binary version ($BINARY_VERSION)"
  exit 1
fi

MISMATCHES=0
while IFS= read -r flag; do
  if ! my-cli --help 2>&1 | grep -qF "$flag"; then
    echo "FAIL: flag '$flag' in AGENTS.md not found in --help"
    MISMATCHES=$((MISMATCHES + 1))
  fi
done < <(grep -oP '\-\-[\w-]+' AGENTS.md | sort -u)

[ $MISMATCHES -eq 0 ] || exit 1
echo "PASS: AGENTS.md matches binary $BINARY_VERSION"
```

---

## Example

```
# CI output on a PR that renames --replicas to --count:

FAIL: AGENTS.md cli-version (2.0.3) != binary version (2.1.0)
FAIL: flag '--replicas' in AGENTS.md not found in --help

→ CI blocks merge until AGENTS.md is updated to cli-version: 2.1.0
  and --replicas is replaced with --count
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-043](o-043-agents-md-content-spec.md) | O | Enforces: validates the content required by REQ-O-043 |
| [REQ-O-045](o-045-integration-artifact-version-declaration.md) | O | Composes: version field check is part of this validation |
| [REQ-O-034](o-034-tool-generate-skills-built-in-command.md) | O | Composes: generate-skills can regenerate AGENTS.md, making this validation trivially pass |
