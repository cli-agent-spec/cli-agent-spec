# Failure Triage — From Observable Signal to §N

> A failed call gives the agent four observables: exit code, stdout, stderr, and timing. This table routes them to the failure modes most likely responsible. Walk it top to bottom; first match wins. Every failure mode file opens its `### Agent Workaround` with a `**Signature:**` line stating the same observables, so a match here can be confirmed there.

The workaround files assume you already know which failure mode you hit. This document is the missing first step: classification from raw evidence, requiring no judgment beyond pattern matching.

---

## How to use

1. Capture all four observables verbatim: the exact command, the integer exit code, full stdout, full stderr; note whether the process hung before being killed
2. Walk the decision table top to bottom; stop at the first matching row
3. Open the linked §N file(s), confirm the match against the `**Signature:**` line, apply that file's Agent Workaround
4. If no row matches, apply the default retry policy at the bottom, then escalate with all four observables attached

Signatures are greppable across the corpus:

```bash
grep -rn "^\*\*Signature:" challenges/
```

---

## Workaround capability tiers

Every `### Agent Workaround` carries a `**Tier:**` line stating the minimum caller capability the full workaround demands. Not all models are equally capable; the tier tells a weak model whether to attempt the workaround or take the fallback:

| Tier | Demands | Weak-model behavior |
|------|---------|---------------------|
| `A` | One safe command, possibly with a fixed env prefix; no branching | Execute directly |
| `B` | One observable check, then one command | Execute directly |
| `C` | Stateful logic: loops, accumulated state, judgment | Skip the body; apply the file's `**Fallback:**` line |

Tier `C` files carry a `**Fallback:**` line: a single command or single action that degrades gracefully (typically: one bounded retry with the right flags, then escalate with all four observables). A weak model executing only Signature → Tier → Fallback never enters logic it cannot reliably complete.

---

## Decision table

| # | Signal (observable) | Likely §N | First action |
|---|---------------------|-----------|--------------|
| 1 | stdout parses as a JSON envelope containing `"ok": false` | [§18](06-high-errors-and-discoverability/18-high-error-quality.md) [§19](06-high-errors-and-discoverability/19-high-retry-hints.md) | Branch on `error.code`; obey `retryable`, `retry_after_ms`, `fix_required`; run `fix_command` verbatim when present, then reissue once |
| 2 | `exit 0` but output text indicates failure, or a pipeline swallowed the code | [§1](04-critical-output-and-parsing/01-critical-exit-codes.md) [§56](01-critical-ecosystem-runtime-agent-specific/56-high-pipeline-exit-masking.md) | Trust the envelope over the exit code; check `PIPESTATUS`; add `set -o pipefail` |
| 3 | Process hangs with no output; completes only when killed by timeout | [§10](02-critical-execution-and-reliability/10-critical-interactivity.md) [§50](01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) [§37](01-critical-ecosystem-runtime-agent-specific/37-critical-repl-triggering.md) [§62](01-critical-ecosystem-runtime-agent-specific/62-critical-editor-trap.md) [§64](01-critical-ecosystem-runtime-agent-specific/64-critical-headless-gui.md) [§45](01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) [§60](01-critical-ecosystem-runtime-agent-specific/60-critical-output-buffer-deadlock.md) [§11](02-critical-execution-and-reliability/11-critical-timeouts.md) | Re-run once with the non-interactive bundle below: stdin closed, suppression env vars, timeout wrapper |
| 4 | `exit 127`, or `command not found` in stderr | [§20](06-high-errors-and-discoverability/20-medium-dependency-discovery.md) [§71](01-critical-ecosystem-runtime-agent-specific/71-critical-noninteractive-installation.md) | Check the binary is on `PATH`; run `tool doctor` if available; install non-interactively |
| 5 | `SyntaxError`, `ImportError`, or a version complaint at startup | [§38](01-critical-ecosystem-runtime-agent-specific/38-high-dependency-version-mismatch.md) | Compare the runtime version against the tool's declared requirement |
| 6 | `exit 2`, or usage/help text in stderr | [§1](04-critical-output-and-parsing/01-critical-exit-codes.md) [§14](02-critical-execution-and-reliability/14-high-arg-validation.md) [§35](01-critical-ecosystem-runtime-agent-specific/35-high-hallucination-inputs.md) [§54](01-critical-ecosystem-runtime-agent-specific/54-high-conditional-args.md) [§69](01-critical-ecosystem-runtime-agent-specific/69-high-argument-order-ambiguity.md) | Re-read `--help` for the exact flags; correct the arguments; reissue once |
| 7 | Input rejected as invalid JSON | [§67](01-critical-ecosystem-runtime-agent-specific/67-high-json5-input.md) | Normalize the payload to strict JSON; use `error.corrected_input` when provided |
| 8 | `Traceback`, `panic:`, or an unhandled exception in stderr | [§18](06-high-errors-and-discoverability/18-high-error-quality.md) | Extract the final stack line as the cause; treat as non-retryable |
| 9 | stdout contains JSON mixed with prose, banners, or ANSI codes | [§41](01-critical-ecosystem-runtime-agent-specific/41-high-update-notifier.md) [§68](01-critical-ecosystem-runtime-agent-specific/68-high-stdout-pollution.md) [§3](04-critical-output-and-parsing/03-high-stderr-stdout.md) [§8](04-critical-output-and-parsing/08-high-ansi-leakage.md) | Apply the JSON extraction rule below; only if it recovers nothing, re-run with `NO_COLOR=1` |
| 10 | stdout is enormous, or ends mid-structure | [§43](01-critical-ecosystem-runtime-agent-specific/43-critical-output-size-unboundedness.md) [§55](01-critical-ecosystem-runtime-agent-specific/55-high-silent-truncation.md) [§5](04-critical-output-and-parsing/05-high-pagination.md) | Check `meta.truncated`; re-run with `--limit`, pagination, or field selectors |
| 11 | `429`, `rate limit`, or `quota` in output, or `exit 11` | [§19](06-high-errors-and-discoverability/19-high-retry-hints.md) | Wait `error.retry_after_ms` (default 60 s), then retry with exponential back-off |
| 12 | `401`/`403`, `unauthorized`, `forbidden`, or token text, or `exit 7`/`exit 8` | [§53](01-critical-ecosystem-runtime-agent-specific/53-critical-credential-expiry.md) [§24](03-critical-security/24-critical-auth-secrets.md) [§45](01-critical-ecosystem-runtime-agent-specific/45-critical-headless-auth.md) [§74](03-critical-security/74-critical-credential-scope-declaration.md) | Distinguish expiry from denial via `error.code`; run the remediation command (`fix_command`, `reauth_command`, or `refresh_command`) when present; never retry denial |
| 13 | `ECONNREFUSED`, DNS failure, TLS error, or proxy text in stderr | [§31](05-high-environment-and-state/31-high-network-proxy.md) | Check `HTTPS_PROXY`/`NO_PROXY` env vars; test connectivity outside the tool |
| 14 | Exit code in `129–143` (128 + signal number) | [§11](02-critical-execution-and-reliability/11-critical-timeouts.md) [§16](02-critical-execution-and-reliability/16-high-signal-handling.md) | The process was killed externally (outer timeout, OOM); inspect partial state before any retry |
| 15 | Error text in a non-English locale | [§57](01-critical-ecosystem-runtime-agent-specific/57-medium-locale-errors.md) | Re-run with `LC_ALL=C LANG=C` |
| 16 | `exit 1` with prose stderr; none of the above | — | Apply the default retry policy below; then classify with `/cli-agent-diagnose` or escalate |

---

## The JSON extraction rule

Several failure modes pollute stdout around a JSON body: update banners (§41), third-party library logs (§68), warnings and help text on the wrong stream (§2, §3), ANSI escape codes (§8, neutralized by the strip step). §2, §3, §41, and §68 embed this same reference implementation, so the rule is learned once and applied everywhere:

1. Strip ANSI escape sequences
2. Parse the whole stream; if it parses, done
3. Otherwise collect every maximal JSON value in the stream by brace-matched decoding (never by regex)
4. Prefer the last candidate object containing the `"ok"` key: the envelope invariant makes it unambiguous
5. Otherwise take the last complete JSON value
6. If nothing parses, the output is unstructured: stop, do not guess

```python
import json, re

def extract_envelope(stdout: str):
    """Canonical JSON extraction rule — defined in challenges/triage.md."""
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", stdout)   # 1. strip ANSI codes
    try:
        return json.loads(text)                            # 2. fast path: clean stream
    except json.JSONDecodeError:
        pass
    candidates = []                                        # 3. every maximal JSON value
    decoder = json.JSONDecoder()
    i = 0
    while True:
        starts = [s for s in (text.find(c, i) for c in "{[") if s != -1]
        if not starts:
            break
        start = min(starts)
        try:
            obj, end = decoder.raw_decode(text[start:])
            candidates.append(obj)
            i = start + end
        except json.JSONDecodeError:
            i = start + 1
    envelopes = [c for c in candidates if isinstance(c, dict) and "ok" in c]
    if envelopes:
        return envelopes[-1]                               # 4. last envelope wins
    if candidates:
        return candidates[-1]                              # 5. last complete value
    return None                                            # 6. unstructured: do not guess
```

Why "last", not "first": banners and logs are usually emitted before the payload, and progress objects before the final envelope; the final envelope is authoritative. Text appended after the payload is not valid JSON, so it produces no candidate and cannot displace the envelope. The one unrecoverable case is pollution interleaved inside a single JSON value (a banner printed mid-object): no extraction rule fixes that, only suppression at the source.

---

## The non-interactive bundle

One fixed prefix neutralizes the entire hang family (row 3) without diagnosing which member fired. Apply it on the single retry:

```bash
PAGER=cat GIT_PAGER=cat MANPAGER=cat EDITOR=true VISUAL=true \
CI=true NO_COLOR=1 TERM=dumb DEBIAN_FRONTEND=noninteractive \
BROWSER=true DISPLAY= \
timeout 60 tool <args> </dev/null
```

- `</dev/null` closes stdin: kills prompt waits (§10), stdin deadlocks (§50), and REPL fallbacks (§37)
- `EDITOR=true VISUAL=true` makes editor launches exit instantly (§62)
- `PAGER=cat GIT_PAGER=cat MANPAGER=cat` disables pagers (§10; the full pager var set is in [REQ-F-046](../requirements/f-046-pager-environment-variable-suppression.md))
- `BROWSER=true DISPLAY=` makes browser and GUI launches no-ops (§45, §64)
- `CI=true TERM=dumb` signals a non-TTY context to most frameworks (§10)
- `timeout 60` bounds the damage if the tool still hangs (§11)

If the bundled retry also times out with no output, the tool blocks on something the environment cannot suppress (browser auth §45, GUI §64, full output buffer §60): stop and escalate rather than retrying again.

---

## Default retry policy

When no signal decides, these rules bound the damage. They restate the corpus-wide consensus (§1, §12, §13, §19, §53) in one place; the attempt budgets and back-off constants are canonical in the Agent interpretation sections of [`exit-code.md`](../schemas/exit-code.md) and [`response-envelope.md`](../schemas/response-envelope.md):

- Read-only command: retry once after a 1 s back-off; a second identical failure is deterministic — stop
- Mutating command: never blind-retry; verify what was committed first ([§12](02-critical-execution-and-reliability/12-critical-idempotency.md), [§13](02-critical-execution-and-reliability/13-critical-partial-failure.md)); resume rather than re-run
- Explicitly retryable signals (`retryable: true`, `exit 11`, `exit 12`): at most 3 attempts with exponential back-off
- Unknown signals: at most 1 retry, then treat as non-retryable
- Escalate with all four observables captured verbatim; never paraphrase stderr

---

*Companion to [`index.md`](index.md). When adding a failure mode with a distinct observable signature, add or extend a row here.*
