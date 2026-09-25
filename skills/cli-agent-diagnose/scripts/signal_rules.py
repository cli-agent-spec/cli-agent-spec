"""Deterministic signal rules for diagnose.py, keyed by failure mode (§N).

Every rule implements a row of the decision table in challenges/triage.md and the
**Signature:** line of the failure mode it names. tests/test_diagnose.py checks that
every rule targets an active failure mode in challenges/index.json and that every
triage row with candidate failure modes is reachable by at least one rule.

Rules see one event at a time through the EventView protocol, so this module has no
dependency on diagnose.py. Python 3.10 compatible (the skill's runtime floor).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Protocol, Sequence


class EventView(Protocol):
    command: str
    args: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


@dataclass(frozen=True)
class Hit:
    failure_mode_id: int
    confidence: float
    evidence: str


def _compile(patterns: Sequence[str], flags: int = re.IGNORECASE) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, flags) for p in patterns)


# ---------------------------------------------------------------------------
# Pattern tables shared with runner.py and traj.py (names kept stable)
# ---------------------------------------------------------------------------

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB012]")

INTERACTIVE_PATTERNS = _compile([
    r"\[y/n\]", r"\[Y/n\]", r"\(yes/no\)", r"Are you sure", r"Press any key", r"Password:",
    r"Enter passphrase", r"Confirm:", r"\[enter to continue\]", r"continue\?", r"proceed\?",
])

TTY_REQUIREMENT_PATTERNS = _compile([
    r"requires?\s+a\s+tty", r"not\s+a\s+tty", r"no\s+tty\s+present", r"input\s+device\s+is\s+not\s+a\s+tty",
    r"stdin\s+is\s+not\s+a\s+terminal", r"must\s+be\s+connected\s+to\s+a\s+terminal", r"terminal\s+required",
    r"tty\s+required", r"inappropriate\s+ioctl\s+for\s+device", r"device\s+or\s+resource\s+busy.*tty",
])

# UI text a pager paints on the captured screen
PAGER_PATTERNS = _compile([
    r"\(END\)", r"^:$", r"^More$", r"^--More--", r"SUMMARY OF LESS COMMANDS", r"^Manual page .+ line \d+",
], re.MULTILINE)

VERSION_PATTERNS = _compile([
    r"SyntaxError:.*module", r"RUNTIME_VERSION", r"requires\s+(?:python|node|ruby|go)\s+\d", r"incompatible.*version",
    r"version.*incompatible", r"requires\s+version", r"minimum.*version",
    r"ModuleNotFoundError", r"ImportError:", r"Unsupported engine", r"GLIBC_\d+\.\d+'? not found",
])

# Subcommand and flag discovery failures (§52). A missing binary is §20, not a discovery failure.
DISCOVERY_PATTERNS = _compile([
    r"unknown (sub)?command", r"invalid (sub)?command", r"unknown flag", r"did you mean", r"unrecognized arguments",
])

CREDENTIAL_PATTERNS = _compile([
    r"token expired", r"credentials? expired", r"auth(?:entication)? failed", r"unauthorized", r"\b401\b",
    r"403.*forbidden", r"re-?auth(?:enticate)?", r"login required",
])

RETRYABLE_RE = re.compile(r'"retryable"\s*:', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatternRule:
    """Fires when any pattern matches the chosen stream and the guard (if any) holds."""

    failure_mode_id: int
    triage_row: int
    confidence: float
    patterns: tuple[re.Pattern[str], ...]
    stream: str                      # "stdout" | "stderr" | "combined"
    evidence: str
    guard: Callable[[EventView], bool] | None = None

    def apply(self, event: EventView) -> Hit | None:
        if self.guard is not None and not self.guard(event):
            return None
        text = {"stdout": event.stdout, "stderr": event.stderr}.get(self.stream, event.stdout + "\n" + event.stderr)
        for pattern in self.patterns:
            if pattern.search(text):
                return Hit(self.failure_mode_id, self.confidence, f"{self.evidence}: {pattern.pattern!r}")
        return None


@dataclass(frozen=True)
class PredicateRule:
    """Fires when the predicate returns evidence text."""

    failure_mode_id: int
    triage_row: int
    confidence: float
    predicate: Callable[[EventView], str | None]

    def apply(self, event: EventView) -> Hit | None:
        evidence = self.predicate(event)
        return Hit(self.failure_mode_id, self.confidence, evidence) if evidence else None


def _json_document(text: str) -> object | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _envelope_ok_false_with_exit_zero(event: EventView) -> str | None:
    document = _json_document(event.stdout)
    if event.exit_code == 0 and isinstance(document, dict) and document.get("ok") is False:
        return 'exit_code=0 but stdout envelope reports "ok": false'
    return None


def _failure_envelope_without_retry_guidance(event: EventView) -> str | None:
    document = _json_document(event.stdout)
    if not isinstance(document, dict) or document.get("ok") is not False:
        return None
    error = document.get("error")
    if isinstance(error, dict) and "retryable" not in error and "fix_required" not in error and "redirect" not in error:
        return "failure envelope has no retryable, fix_required, or redirect guidance"
    return None


def _envelope_ok_false_in_pipeline(event: EventView) -> str | None:
    full = " ".join((event.command, *event.args))
    if _envelope_ok_false_with_exit_zero(event) and "|" in full:
        return "failure envelope behind exit_code=0 in a shell pipeline"
    return None


def _missing_binary(event: EventView) -> str | None:
    if event.exit_code == 127:
        return "exit_code=127: binary not found or not executable"
    if re.search(r"(?:^|: )command not found|: not found$|No such file or directory.*exec", event.stdout + "\n" + event.stderr, re.I | re.M):
        return "shell reports the command was not found"
    return None


def _usage_error(event: EventView) -> str | None:
    if event.exit_code == 2 and re.search(r"^\s*usage:", event.stderr + "\n" + event.stdout, re.I | re.M):
        return "exit_code=2 with usage text"
    return None


def _truncated_structure(event: EventView) -> str | None:
    text = event.stdout.strip()
    if len(text) < 2 or text[0] not in "{[" or text[-1] in "}]":
        return None
    if _json_document(text) is None:
        return "stdout starts as JSON but ends mid-structure"
    return None


def _declared_truncation(event: EventView) -> str | None:
    document = _json_document(event.stdout)
    if isinstance(document, dict) and isinstance(document.get("meta"), dict) and document["meta"].get("truncated") is True:
        return "envelope reports meta.truncated: true"
    return None


def _mixed_json_and_prose(event: EventView) -> str | None:
    """Banner or log lines followed by a JSON object payload that runs to the end of stdout."""
    text = ANSI_RE.sub("", event.stdout).strip()
    if not text.endswith("}") or _json_document(text) is not None:
        return None
    decoder = json.JSONDecoder()
    for match in re.finditer(r"^\{", text, re.M):
        if match.start() == 0:
            continue
        try:
            value, consumed = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value and match.start() + consumed == len(text):
            return "stdout carries a JSON object payload preceded by non-JSON lines"
    return None


def _signal_exit(event: EventView) -> str | None:
    if 129 <= event.exit_code <= 159 and event.exit_code != 124:
        return f"exit_code={event.exit_code} (128 + signal {event.exit_code - 128}): process was killed or cancelled"
    return None


def _sigkill_or_sigterm(event: EventView) -> str | None:
    if event.exit_code in (137, 143):
        return f"exit_code={event.exit_code}: killed by an outer timeout or the OOM killer"
    return None


def _silent_hang(event: EventView) -> str | None:
    if (event.timed_out or event.exit_code == 124) and not event.stdout.strip() and not event.stderr.strip():
        return "timed out with no output at all: likely blocked reading stdin"
    return None


def _hang_with_full_buffer(event: EventView) -> str | None:
    if (event.timed_out or event.exit_code == 124) and len(event.stdout) >= 64_000:
        return f"timed out after writing {len(event.stdout):,} chars: output pipe likely full"
    return None


_FORMAT_AS_OUTPUT_RE = re.compile(r"(?:^|\s)(?:--output|-o)(?:=|\s+)['\"]?(json|jsonl|ya?ml|table|text|plain|tsv|csv|id)['\"]?(?=\s|$)", re.I)


def _format_value_passed_as_output_path(event: EventView) -> str | None:
    """--output json exits 0 but stdout carries no JSON: the flag took a path (§78)."""
    match = _FORMAT_AS_OUTPUT_RE.search(" ".join((event.command, *event.args)))
    if match and event.exit_code == 0 and _json_document(event.stdout) is None:
        return f"exit_code=0 without JSON on stdout after {match.group(0).strip()!r}: --output likely wrote a file named {match.group(1)!r}"
    return None


def invocation_tokens(command: str, args: Sequence[str]) -> list[str]:
    """Whitespace tokens of the full invocation; traces may carry args inside command."""
    return [*command.split(), *args]


# Long options that take exactly one value across the CLIs agents call. Only these count
# as a conflicting repeat: repeatable options (--header, --env, --label, --field, --exclude)
# legitimately appear several times, and a switch such as --verbose takes no value, so the
# word after it is a positional, not its value. --output is absent too: curl repeats it,
# one --output per URL.
SINGLE_VALUE_OPTIONS = frozenset({
    "--format", "--limit", "--timeout", "--region", "--profile", "--cursor", "--page-size",
})


def conflicting_repeat(tokens: Sequence[str]) -> tuple[str, str, str] | None:
    """First single-value option given twice with different values, as (flag, first, second) (§69).

    Reads `--name value` and `--name=value` for names in SINGLE_VALUE_OPTIONS; stops at `--`.
    """
    seen: dict[str, str] = {}
    for index, token in enumerate(tokens):
        if token == "--":
            return None
        flag, _, inline = token.partition("=")
        if flag not in SINGLE_VALUE_OPTIONS:
            continue
        if inline or token.endswith("="):
            value = inline
        elif index + 1 < len(tokens):
            value = tokens[index + 1]
        else:
            continue
        first = seen.setdefault(flag, value)
        if first != value:
            return flag, first, value
    return None


def _conflicting_repeat_rejected(event: EventView) -> str | None:
    conflict = conflicting_repeat(invocation_tokens(event.command, event.args))
    if conflict and event.exit_code == 2:
        flag, first, second = conflict
        return f"exit_code=2 after {flag} was given twice ({first!r}, then {second!r}): pass each option once"
    return None


def _install_command(event: EventView) -> bool:
    full = " ".join((event.command, *event.args))
    return bool(re.search(r"\b(install|setup|bootstrap)\b|curl .*\|\s*(sh|bash)", full))


def _auth_context(event: EventView) -> bool:
    return bool(re.search(r"auth|login|sign.?in|oauth|device code", event.stdout + event.stderr + event.command + " ".join(event.args), re.I))


RULES: tuple[PatternRule | PredicateRule, ...] = (
    # Row 1: structured failure that still leaves the caller guessing about retries
    PredicateRule(19, 1, 0.55, _failure_envelope_without_retry_guidance),
    # Row 2: exit 0 but the output reports failure
    PredicateRule(1, 2, 0.90, _envelope_ok_false_with_exit_zero),
    PredicateRule(56, 2, 0.80, _envelope_ok_false_in_pipeline),
    # Row 3: hangs — §10/§11 live in diagnose.match_signals; these add the rest of the family
    PredicateRule(50, 3, 0.55, _silent_hang),
    PredicateRule(60, 3, 0.70, _hang_with_full_buffer),
    PatternRule(62, 3, 0.95, _compile([r"Waiting for your editor", r"hint: Waiting for your editor to close the file", r"EDITOR.*(not set|unset)"]), "combined", "editor launch in output"),
    PatternRule(37, 3, 0.85, _compile([r"^>>> ?$", r"Type \"?\.help\"? for more information", r"Welcome to Node\.js", r"^irb\(main\)"], re.MULTILINE), "stdout", "REPL prompt in output"),
    PatternRule(45, 3, 0.90, _compile([r"open(ing)? (the following|this) (url|link)", r"device code", r"opening browser", r"xdg-open", r"visit .*https?://\S+.*(login|auth|device)"]), "combined", "browser-based auth flow", guard=_auth_context),
    PatternRule(64, 3, 0.85, _compile([r"cannot open display", r"no display (name|environment)", r"DISPLAY (is )?not set", r"Gtk-WARNING", r"xdg-open: no method available"]), "combined", "GUI launch without a display"),
    # Row 4: missing binary or installation
    PredicateRule(20, 4, 0.85, _missing_binary),
    PatternRule(71, 4, 0.75, _compile([r"\[y/n\]", r"Do you want to continue", r"interactive", r"press enter", r"accept the license"]), "combined", "installer expects interaction", guard=_install_command),
    # Row 6: usage errors
    PredicateRule(14, 6, 0.70, _usage_error),
    PredicateRule(69, 6, 0.80, _conflicting_repeat_rejected),
    # Row 7: agent-generated input rejected as JSON
    PatternRule(67, 7, 0.85, _compile([r"Expecting property name enclosed in double quotes", r"JSONDecodeError", r"Unexpected token .* in JSON", r"invalid character .* looking for beginning", r"trailing comma", r"is not valid JSON"]), "combined", "input rejected as invalid JSON"),
    # Row 8: crashes instead of structured errors
    PatternRule(18, 8, 0.70, _compile([r"^Traceback \(most recent call last\)", r"^panic: ", r"^thread '.*' panicked", r"Unhandled(Promise)?Rejection", r"^\s+at .+\(.+:\d+:\d+\)$"], re.MULTILINE), "stderr", "unhandled exception instead of a structured error"),
    # Row 9: polluted stdout
    PatternRule(41, 9, 0.90, _compile([r"update available", r"new (minor |major |patch )?version of .* is available", r"npm notice", r"a new release of .* is available", r"run .* to update"]), "combined", "update notifier text"),
    PredicateRule(68, 9, 0.80, _mixed_json_and_prose),
    PredicateRule(3, 9, 0.60, _mixed_json_and_prose),
    PatternRule(8, 9, 0.85, (ANSI_RE,), "stdout", "ANSI escape sequences on stdout"),
    # Row 10: output size and truncation
    PredicateRule(55, 10, 0.80, _truncated_structure),
    PredicateRule(5, 10, 0.85, _declared_truncation),
    # Row 11: rate limits
    PatternRule(19, 11, 0.85, _compile([r"\b429\b", r"rate.?limit", r"too many requests", r"quota (exceeded|exhausted)", r"retry after \d+"]), "combined", "rate limit without structured retry guidance"),
    PredicateRule(19, 11, 0.80, lambda e: "exit_code=11 (RATE_LIMITED)" if e.exit_code == 11 else None),
    # Row 12: auth — §53 lives in diagnose.match_signals; scope and secret leakage here
    PatternRule(74, 12, 0.80, _compile([r"insufficient (scope|permission)s?", r"missing (required )?scopes?", r"requires? (the )?\S+ scope", r"resource not accessible by integration"]), "combined", "credential lacks a required scope"),
    PatternRule(24, 12, 0.90, _compile([r"\bghp_[A-Za-z0-9]{36}\b", r"\bsk-[A-Za-z0-9_-]{20,}\b", r"\bAKIA[0-9A-Z]{16}\b", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"], 0), "combined", "credential material printed in output"),
    # Row 13: network and proxy
    PatternRule(31, 13, 0.85, _compile([r"\bECONNREFUSED\b", r"\bENOTFOUND\b", r"\bEAI_AGAIN\b", r"getaddrinfo (ENOTFOUND|failed)", r"\bSSLError\b", r"\bSSL_ERROR_\w+", r"x509: certificate"], 0), "combined", "network or TLS error code"),
    PatternRule(31, 13, 0.85, _compile([r"Could not resolve host", r"certificate verify failed", r"Name or service not known", r"proxy(connect)? (error|failed|authentication)", r"407 Proxy Authentication"]), "combined", "network, TLS, or proxy failure"),
    # Row 14: killed by a signal
    PredicateRule(16, 14, 0.80, _signal_exit),
    PredicateRule(11, 14, 0.60, _sigkill_or_sigterm),
    # Row 15: localized errors
    PatternRule(57, 15, 0.80, _compile([r"\bFehler\b", r"\berreur\b", r"\berrore\b", r"\bошибка\b", r"错误", r"エラー", r"오류", r"\bnicht gefunden\b", r"\bintrouvable\b"]), "combined", "error text in a non-English locale"),
    # Row 16: a format value passed to a path-typed --output
    PredicateRule(78, 16, 0.80, _format_value_passed_as_output_path),
)


def apply_rules(event: EventView) -> list[Hit]:
    """Every rule hit for one event, in table order."""
    return [hit for rule in RULES if (hit := rule.apply(event)) is not None]
