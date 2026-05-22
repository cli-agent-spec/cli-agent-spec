# Langfuse CLI Agent Audit — Report Index

**Generated:** 2026-05-22  
**CLI:** `langfuse` (`langfuse-cli` 0.0.10)  
**Scope:** Critical failure modes only

## Scores

| Area | Score |
|---|---:|
| Failure mode average | 1.4/3 |
| Passing critical modes | 6/22 |
| Partial critical modes | 7/22 |
| Failing critical modes | 6/22 |
| Indeterminate critical modes | 3/22 |
| Readiness | 9/15 [C] |

## Reports

| File | Audience | Purpose |
|---|---|---|
| `report-dev.md` | Langfuse CLI maintainers | Fix list ordered by agent impact. |
| `report-agent-dev.md` | Developers integrating the CLI into agents | Invocation guidance and workarounds. |
| `report-runtime.md` | Runtime agents | Short operational brief before calling the CLI. |
| `report-issues.md` | Agent users and maintainers | Concrete bugs and gaps observed during checks. |

## Key Findings

- Parser and validation failures do not honor `--json`; agents receive prose usage text for common errors.
- Exit status collapses validation, auth, command, and network failures into generic exit code 1.
- Destructive and mutating commands lack dry-run, idempotency, and machine-readable effect metadata.
- Missing-auth output does not provide `AUTH_REQUIRED`, `auth_methods`, or setup guidance in structured form.
- Large-output protection is not declared; agents must manage `--limit` and `--fields` themselves.

## Source Artifacts

- `environment.md`
- `readiness.md`
- `findings.md`
- `trace.md`
- `issues.md`
