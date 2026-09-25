# Conformance Levels

> A CLI claims a level, not a percentage. Each level is a fixed set of requirements, and each higher level contains every lower one.

159 requirements are written for framework authors. A team retrofitting an existing Cobra, Click, or Clap tool needs a smaller first target that removes the failures agents hit on every call. Levels give that target and a way to state progress that other people can verify.

---

## The three levels

| Level | Name | Contains | Size |
|-------|------|----------|------|
| 1 | Agent-safe basics | The twelve requirements listed below | 12 |
| 2 | Agent-reliable | Level 1 plus every other `P0` requirement | 51 |
| 3 | Full spec | Every requirement | 159 |

Every requirement in `requirements/index.md` carries a `Level` column with the lowest level that includes it. `scripts/validate_links.py` recomputes the column from this file and the priorities, so the two cannot drift.

---

## Level 1 — Agent-safe basics

A Level 1 CLI never hangs an agent, always answers in one parseable shape, and signals failure through codes rather than prose. These twelve requirements address the Critical failure modes an agent meets on almost every invocation: hangs (§10, §50), unparseable output (§2, §3, §8), ambiguous exit codes (§1), and destructive calls without a preview (§23).

<!-- level-1 -->
| Requirement | Why it is in Level 1 |
|-------------|----------------------|
| [REQ-F-001](f-001-standard-exit-code-table.md) | Retry decisions start from a fixed exit code table |
| [REQ-F-002](f-002-exit-code-2-reserved-for-validation-failures.md) | Exit `2` guarantees nothing was written, so fixing input and reissuing is safe |
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | JSON activates in a non-TTY without the agent knowing a flag |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | One envelope shape for every command and outcome |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | stdout carries only the envelope |
| [REQ-F-007](f-007-ansi-color-code-suppression.md) | No escape codes corrupt the JSON |
| [REQ-F-008](f-008-no-color-and-ci-environment-detection.md) | `NO_COLOR` and `CI` are honored |
| [REQ-F-009](f-009-non-interactive-mode-auto-detection.md) | No prompt waits for input that never comes |
| [REQ-F-010](f-010-pager-suppression.md) | No pager swallows output |
| [REQ-F-048](f-048-help-output-routing-to-stderr-in-non-tty-mode.md) | Help text never lands in parsed stdout |
| [REQ-C-004](c-004-destructive-commands-must-support-dry-run.md) | Destructive commands can be previewed |
| [REQ-C-013](c-013-error-responses-include-code-and-message.md) | Every error has a stable code |
<!-- /level-1 -->

---

## Claiming a level

1. Implement every requirement in the level and verify its acceptance criteria
2. Run the [conformance kit](../conformance/README.md) with a profile that includes `read`, `invalid`, and `destructive` probes and, for Level 3, a `manifest` command
3. Publish the kit's `ConformanceResult` next to the claim

The kit verifies the mechanically checkable part of each level. A `pass` verdict is necessary, not sufficient: requirements such as locale-invariant serialization or secret redaction still need their acceptance criteria reviewed. A level verdict of `incomplete` means the profile lacked a probe kind, and the claim cannot be made until the missing checks run.

---

## Related

| Document | Relationship |
|----------|--------------|
| [`requirements/index.md`](index.md) | Aggregates: the `Level` column for every requirement |
| [`conformance/README.md`](../conformance/README.md) | Enforces: deterministic checks tagged with the level they verify |
| [`IMPLEMENTING.md`](../IMPLEMENTING.md) | Composes: goal-based paths and the wave plan order work within and across levels |
| [§10](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) · [§1](../challenges/04-critical-output-and-parsing/01-critical-exit-codes.md) · [§2](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) | Consumes: the failure modes Level 1 eliminates first |
