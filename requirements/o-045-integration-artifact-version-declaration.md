# REQ-O-045: Integration Artifact Version Declaration

**Tier:** Opt-In | **Priority:** P1

**Source:** [§72 Integration Artifact Version Drift](../challenges/01-critical-ecosystem-runtime-agent-specific/72-high-integration-artifact-drift.md) · [§47 MCP Wrapper Schema Staleness](../challenges/01-critical-ecosystem-runtime-agent-specific/47-high-mcp-schema-staleness.md)

**Addresses:** Severity: High / Token Spend: High / Time: Medium / Context: Low

---

## Description

Every agent-facing integration artifact (OpenAPI spec, AGENTS.md, skill files, companion packages, LangChain/LlamaIndex tool definitions) MUST declare the CLI binary version it was written against, using a format-appropriate version field. The declared version MUST match the output of `<binary> --version` exactly. Artifacts MUST be released in the same CI pipeline as the binary they describe, or version-locked via a `peerDependencies` / `requires` constraint that prevents mismatched installs.

## Acceptance Criteria

- Every integration artifact contains a version declaration (format-appropriate: YAML `version:`, Markdown `<!-- cli-version: -->`, JSON `"cli_version":`)
- The declared version matches `<binary> --version` output exactly (same string, same format)
- Artifacts are either: (a) in the same package as the binary, (b) released by the same CI pipeline as the binary with the same version tag, or (c) a companion package with a `peerDependencies` / `requires` constraint pinning to the matching binary version
- No command name or flag name in any integration artifact is absent from `<binary> --help` output

---

## Schema

**Types:** none — version field format is artifact-specific

---

## Wire Format

OpenAPI spec:
```yaml
openapi: "3.1.0"
info:
  title: My CLI
  version: "2.1.0"    # must match `my-cli --version` exactly
```

AGENTS.md:
```markdown
<!-- cli-version: 2.1.0 -->
```

Companion package:
```json
{
  "name": "my-cli-openapi",
  "version": "2.1.0",
  "peerDependencies": { "my-cli": "2.1.0" }
}
```

---

## Example

```bash
$ my-cli --version
2.1.0

$ grep 'version:' openapi.yaml
  version: "2.1.0"   # matches → artifact is current

$ grep 'version:' openapi.yaml
  version: "2.0.1"   # mismatch → artifact is STALE, agent must not trust flag names
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-O-043](o-043-agents-md-content-spec.md) | O | Extends: version declaration is required in AGENTS.md |
| [REQ-O-046](o-046-agents-md-ci-validation.md) | O | Composes: CI validation checks declared version matches binary |
| [REQ-F-022](f-022-schema-version-in-every-response.md) | F | Specializes: runtime schema versioning; this requirement covers static artifact versioning |
