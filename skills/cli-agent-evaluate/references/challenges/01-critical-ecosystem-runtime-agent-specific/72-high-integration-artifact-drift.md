> **Part I: Ecosystem, Runtime & Agent-Specific** | Challenge §72

## 72. Integration Artifact Version Drift

**Severity:** High | **Frequency:** Common | **Detectability:** Medium | **Token Spend:** High | **Time:** Medium | **Context:** Low

### The Problem

Agent-facing integration artifacts — OpenAPI specs, AGENTS.md workflow docs, skill files, companion packages, and LangChain/LlamaIndex tool definitions — are typically maintained in a separate repository, package, or file from the CLI binary. As the CLI evolves, these artifacts drift: they document commands that were removed, omit new flags, and describe old behavior. Agents loading these artifacts have no signal that the content is stale.

This is distinct from §47 (MCP Wrapper Schema Staleness), which covers the MCP-specific drift pattern. This challenge covers all non-MCP integration artifacts that share the same root cause: separation of the artifact from the binary release cycle.

```bash
# Agent loads OpenAPI spec to plan a deployment
$ cat openapi.yaml | grep 'deploy'
# OpenAPI spec describes: deploy --env staging|production --replicas N
# Agent constructs: my-cli deploy --env staging --replicas 3

$ my-cli deploy --env staging --replicas 3
Error: unknown flag --replicas   # flag was renamed to --count in v2.0
# OpenAPI spec is pinned to v1.x; CLI is v2.1
```

Common drift patterns:
1. **Flag rename** — `--replicas` → `--count`; artifact still documents old name
2. **Command removal** — a subcommand is deleted in a major version; artifact still lists it
3. **New required flag** — CLI adds a required `--region` flag; artifact does not mention it
4. **Output schema change** — JSON response structure changes; artifact declares old shape
5. **Env var rename** — `MY_TOOL_API_KEY` → `MY_TOOL_TOKEN`; AGENTS.md still documents old name

The agent cannot distinguish "this artifact is stale" from "I am constructing the invocation incorrectly" — both produce the same error.

### Impact

- Agent constructs invocations that match the artifact but fail against the binary — produces `ARG_ERROR` (exit 2) with no indication that the artifact is the problem
- High token spend: agent retries with variations on the same stale information, all failing
- Correctness inversion: having an integration artifact is *worse* than having none if the artifact is stale — the agent trusts it and stops trying alternatives
- Impossible to detect automatically without comparing artifact content against live `--help` output

### Solutions

**For CLI authors:**

Include a version field in every integration artifact, matching the binary version exactly:

```yaml
# openapi.yaml
info:
  title: My CLI API
  version: "2.1.0"   # must match `my-cli --version` output exactly
```

```markdown
<!-- AGENTS.md -->
<!-- cli-version: 2.1.0 -->
```

Co-version artifacts with the binary — release them in the same CI pipeline, with the same version tag:

```yaml
# .github/workflows/release.yml
- name: Release binary and artifacts together
  run: |
    VERSION=$(my-cli --version)
    sed -i "s/version: .*/version: \"$VERSION\"/" openapi.yaml
    git commit -am "Release $VERSION"
    git tag $VERSION
```

If artifacts live in a separate package, version-lock it to the binary with an explicit compatibility field:

```yaml
# companion-package/package.json
{
  "name": "my-cli-openapi",
  "version": "2.1.0",
  "peerDependencies": {
    "my-cli": "2.1.0"
  }
}
```

**For framework designers:**

Generate integration artifacts automatically from the registered command schema at release time. Generated artifacts cannot drift because they are produced from the same source of truth as the binary.

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Integration artifacts exist with no version field — drift is undetectable; or confirmed drift (artifact documents commands/flags not present in `--help`) |
| 1 | Artifacts have a version field but it does not match `<binary> --version`, or version format differs (e.g. `2.1` vs `2.1.0`) |
| 2 | Artifacts are versioned and currently match binary version, but no automated co-versioning mechanism — future drift is not prevented |
| 3 | Artifacts are co-versioned: same package, same CI release pipeline, or version-locked companion; zero confirmed drift instances |

**Check:** For each integration artifact found (OpenAPI, AGENTS.md, skill files): look for a version field. Compare against `<binary> --version`. Scan artifact for command names and flag names not present in `<binary> --help`. Each mismatch is a confirmed drift instance.

### Agent Workaround

Before using any integration artifact, extract its declared version and compare against `<binary> --version`. If they differ or no version is declared, treat the artifact as potentially stale.

Cross-check critical details against live `--help` before constructing any invocation based on artifact content:

```
1. Load artifact, extract version → compare to binary version
2. If versions differ: flag artifact as STALE; do not trust flag names or output schema
3. For any flag from the artifact: verify it appears in `<binary> <subcommand> --help`
4. For any env var from the artifact: verify it appears in `<binary> --help` or AGENTS.md date matches release notes
```

If drift is confirmed, fall back to `--help` as the authoritative source and ignore the artifact.

**Limitation:** Cross-checking every artifact claim against `--help` is O(N) in the number of flags and commands — expensive for large CLIs. The agent must decide whether to spot-check (fast, risky) or fully validate (slow, safe) based on task criticality.
