# Guide: Designing Errors for Autonomous Recovery

> **The principle:** Every error must answer four questions in machine-readable fields: what failed (`code`), is the identical call worth repeating (`retryable`), what must change first (`fix_required`), and what exact command makes that change (`fix_command`). Design for the least capable caller — an agent that can copy a string and compare a boolean, nothing more.

A human reads an error message, infers the cause, and improvises a fix. The weakest agent that will ever call your tool can do none of that. It can branch on a constant, compare a boolean, sleep for a number of milliseconds, and paste a string back into a shell. An error designed for autonomous recovery is one where those four operations are sufficient to reach the right next action every time.

This is not a degraded experience for capable models. A frontier model burns hundreds of tokens reasoning about `Connection failed.`; it spends near zero acting on `retryable: true, retry_after_ms: 5000`. The recovery ladder makes weak models correct and strong models cheap.

---

## The recovery ladder

Four fields, ordered by the question they answer. Each rung requires strictly less caller capability than prose:

| Question | Field | What the caller does with it |
|----------|-------|------------------------------|
| What failed? | `error.code` | Branch on a constant; never parse `message` |
| Worth repeating unchanged? | `error.retryable` (+ `retry_after_ms`) | Compare a boolean; sleep; reissue |
| What must change first? | `error.fix_required` | Know the failure is correctable, not terminal |
| What command changes it? | `error.fix_command` | Paste and run; reissue the original once |

The ladder degrades gracefully. A tool that only provides `code` and `retryable` already prevents retry loops (the §19 failure). Adding `fix_required` prevents premature abandonment of correctable failures (the §53 failure). Adding `fix_command` closes the loop: recovery without synthesis.

The corresponding contracts: [REQ-C-013](../requirements/c-013-error-responses-include-code-and-message.md) (code + message), [REQ-C-014](../requirements/c-014-error-responses-include-retryable-and-retry-after-.md) (retryable + backoff), [REQ-C-030](../requirements/c-030-error-responses-include-fix-command.md) (executable remediation).

---

## The three recovery classes

Every failure your tool can emit belongs to exactly one class, and the field combination encodes which:

| Class | Encoding | Agent behavior |
|-------|----------|----------------|
| Transient | `retryable: true` (+ `retry_after_ms`) | Wait, reissue unchanged, bounded attempts |
| Caller-correctable | `retryable: false` + `fix_required` (+ `fix_command`) | Apply the fix, reissue once |
| Terminal | `retryable: false`, neither fix field | Stop; escalate with the error verbatim |

The complete decision procedure an agent needs — and the test of your error design is that this is *all* it needs:

```
if error.retryable:            wait retry_after_ms, reissue (≤3 attempts)
elif error.fix_command:        run it; if exit 0, reissue once
elif error.fix_required:       apply the stated fix if achievable, reissue once;
                               else escalate with the condition
else:                          stop, escalate verbatim
```

If any error your tool emits requires logic outside these four lines, the error is misclassified or underspecified. The classification must hold under the spec's `retryable` semantics: `true` means the identical unchanged invocation may succeed and no side effects occurred (see [`exit-code.md`](../schemas/exit-code.md)); "the user could fix this and retry" is never `retryable: true` — it is caller-correctable.

---

## Why prose suggestions are not remediation

`suggestion: "Run tool login to refresh your credentials"` looks actionable. It is actionable for a human and for a strong model. A weak model must: extract the command from the sentence, decide whether the surrounding words are part of it, decide whether it is safe, and construct a new tool call. Each step is a failure opportunity, and the extraction step is a prompt-injection reflex waiting to be exploited by any error text that quotes untrusted input.

`fix_command: "tool login"` removes every step except copying. Keep `suggestion` for humans; it is good UX. But never make prose the only path to recovery when a command exists:

```json
{
  "code": "CREDENTIALS_EXPIRED",
  "message": "Access token expired at 2026-07-01T00:00:00Z",
  "retryable": false,
  "fix_required": "Refresh credentials, then reissue",
  "fix_command": "tool auth refresh",
  "suggestion": "Your token lifetime is 1h; consider a service account for long sessions"
}
```

Each field serves a different reader: `fix_required` tells any agent the failure is correctable, `fix_command` tells the weakest agent exactly how, `suggestion` tells the human something worth knowing that is not a recovery step.

---

## Designing `fix_command` safely

The caller will execute this string blindly; that is its purpose. Treat authoring a `fix_command` as injecting code into every consumer of your tool, because it is. The normative constraint list lives in [REQ-C-030](../requirements/c-030-error-responses-include-fix-command.md); this section carries the rationale:

- **Verbatim-executable**: no placeholders. `tool auth login --token <your-token>` forces synthesis back on the caller and teaches it to paste literal `<your-token>`. If remediation needs caller input, omit `fix_command`; state the condition in `fix_required`
- **Idempotent or read-only**: the caller may run it more than once (crashed mid-recovery, retried the whole procedure). `tool auth refresh` is safe; `tool migrate apply-next` is not
- **Never destructive**: no command declared destructive ([REQ-C-002](../requirements/c-002-command-declares-danger-level.md)) may ever appear as remediation. The framework enforces this at registration — an agent will not stop to ask whether `tool reset --hard` is proportionate
- **Static, never interpolated**: a `fix_command` template that splices in file names, server responses, or user input is an injection channel ([§25](../challenges/03-critical-security/25-critical-prompt-injection.md)). The value emitted at runtime must come from the registration-time registry, not from the failure context
- **Self-contained**: one invocation of the same tool or a declared companion; never a shell pipeline, which would smuggle arbitrary execution past the registration-time safety checks
- **Closed-loop**: after `fix_command` exits `0`, the original invocation must not fail with the same `error.code`. If it can, the remediation is wrong or the failure is misclassified

Specialized variants follow the same contract: `refresh_command` ([REQ-F-063](../requirements/f-063-credential-expiry-structured-error.md)), `reauth_command` (§53), dependency `fix_command` in `tool doctor` ([REQ-O-031](../requirements/o-031-dependency-version-matrix-declaration.md)). Emit the generic `error.fix_command` alongside any specialized field so consumers need only one code path.

---

## A worked example

The same failure at each maturity level. Score 0, the agent can only guess:

```
Error: Something went wrong
exit 1
```

Score 1, the agent can branch but not decide:

```json
{ "code": "AUTH_ERROR", "message": "Authentication failed" }
```

Retry? Re-login? Give up? Undecidable: expired credentials, wrong credentials, and missing permissions all collapse into one code.

Full ladder — every agent from the weakest to the strongest takes the same correct action:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "CREDENTIALS_EXPIRED",
    "message": "Access token expired at 2026-07-01T00:00:00Z",
    "retryable": false,
    "fix_required": "Refresh credentials, then reissue",
    "fix_command": "tool auth refresh"
  },
  "warnings": [],
  "meta": { "duration_ms": 120 }
}
```

The exit code carries the same classification out-of-band: `AUTH_REQUIRED (8)` here, `PERMISSION_DENIED (7)` for the terminal sibling, so even a caller that never parses stdout can distinguish correctable from hopeless.

---

## Related

| Reference | Relationship |
|-----------|--------------|
| [§18 Error Message Quality](../challenges/06-high-errors-and-discoverability/18-high-error-quality.md) | Sources: the failure mode this guide's ladder eliminates |
| [§19 Retry Hints in Error Responses](../challenges/06-high-errors-and-discoverability/19-high-retry-hints.md) | Sources: retry-loop and premature-abandonment failures addressed by rungs 2 and 3 |
| [§53 Credential Expiry Mid-Session](../challenges/01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md) | Sources: the canonical caller-correctable failure |
| [§25 Prompt Injection via Output](../challenges/03-critical-security/25-critical-prompt-injection.md) | Sources: the injection surface `fix_command` must not widen |
| [REQ-C-013](../requirements/c-013-error-responses-include-code-and-message.md) | Enforces: `code` + `message` (rung 1) |
| [REQ-C-014](../requirements/c-014-error-responses-include-retryable-and-retry-after-.md) | Enforces: `retryable` + `retry_after_ms` + `fix_required` (rungs 2–3) |
| [REQ-C-030](../requirements/c-030-error-responses-include-fix-command.md) | Enforces: executable `fix_command` (rung 4) with registration-time safety checks |
| [REQ-F-063](../requirements/f-063-credential-expiry-structured-error.md) | Specializes: auth-specific remediation fields |
| [`response-envelope.md`](../schemas/response-envelope.md) | Provides: the `ErrorDetail` shape carrying all four rungs |
| [`exit-code.md`](../schemas/exit-code.md) | Provides: the out-of-band classification (`retryable` semantics, *after fix* codes) |
