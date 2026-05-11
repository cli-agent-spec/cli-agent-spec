# Guide: Designing AI-Native CLI Commands That Read from stdin

> **The principle:** Every stdin-reading path must be explicit, declared in the schema, and fail immediately with a structured error when invoked without data in a non-TTY context.

stdin seems simple. It is not. When a human runs `my-tool import`, they type data and press Ctrl-D. When an AI agent runs the same command, there is no human, no TTY, and often no data flowing yet. The result: the tool hangs silently, burns the agent's timeout budget, and produces no error. The agent retries. It hangs again. The task fails.

This guide covers the three failure modes that break stdin-reading commands under agent orchestration, the spec-grounded solutions for each, and the safe invocation patterns every agent builder should use today.

---

## The Three Failure Modes

### §50 — Stdin Consumption Deadlock

A command silently falls back to stdin when an argument is missing. In a TTY, this looks like a helpful prompt. In a non-TTY (agent) context, it blocks indefinitely — no output, no error, no timeout until the process is killed externally.

```bash
# Agent omits --input-file
bean commodity import
# ← blocks forever waiting for stdin EOF

# Password defaults to stdin when flag omitted
my-tool --user admin
Password:
# ← blocking read in non-TTY mode: hangs until timeout
```

The tell: the process is running, consuming no CPU, producing no output — indistinguishable from slow initialization until the full timeout fires.

### §61 — Bidirectional Pipe Payload Deadlock

UNIX pipes have a 64 KB kernel buffer. If a tool reads a large payload from stdin *and* writes a large response to stdout, both sides fill their buffers and wait for the other to drain. Neither does. Silent deadlock.

```bash
# Agent sends 200 KB CSV and expects a 200 KB response
echo "$large_csv" | bean commodity import --output json > result.json

# Timeline:
# 1. Agent writes 200 KB to tool's stdin
# 2. Tool reads stdin, starts writing response to stdout
# 3. Tool's stdout fills the 64 KB pipe buffer — tool blocks
# 4. Agent is still writing stdin, hasn't started reading stdout yet
# DEADLOCK. Both processes hang forever.
```

### §10 — Interactive Prompt in Non-TTY Context

A confirmation prompt (`Proceed? [y/N]`) that works fine interactively hangs an agent that has no way to answer. Even tools that detect non-TTY and suppress confirmation prompts sometimes leave stdin-reading codepaths that predate the non-TTY requirement.

---

## Solutions for CLI Authors

### Never silently fall back to stdin

Require an explicit flag. There must be no hidden stdin reads. Every stdin-reading path must be declared in the command's `--schema` output. `-` as the flag value is the explicit opt-in; omitting the flag entirely in non-TTY context must fail immediately.

```bash
# Wrong — auto-reads stdin when no args given → hangs in non-TTY
bean commodity import

# Correct — named file (no stdin, safe for any payload size)
bean commodity import --input-file commodities.csv

# Correct — explicit stdin opt-in via `-`
cat commodities.csv | bean commodity import --input-file -
```

When `--input-file` is omitted in a non-TTY context, the command must fail immediately with a structured error:

```json
{
  "ok": false,
  "error": {
    "code":    "STDIN_REQUIRED",
    "message": "Argument '--input-file' is required when stdin is not a TTY",
    "hint":    "Pass --input-file <path> or pipe: cat file.csv | bean commodity import --input-file -",
    "retryable": false,
    "phase":   "validation"
  }
}
```

Exit code **4**. Immediately. Under one second.

### Detect non-TTY at startup, not at read time (REQ-F-009)

The framework checks `isatty(stdin)` once at startup and globally disables interactive prompts. Any command that would block waiting for stdin in non-TTY mode must fail at validation time — before any side effects run. This is a Framework-Automatic behavior; command authors should not have to think about it.

```python
import sys

def bootstrap():
    if not sys.stdin.isatty():
        os.environ["NON_INTERACTIVE"] = "1"
        _install_stdin_guard()  # raises STDIN_REQUIRED before any blocking read
```

### Cap stdin at 64 KB, auto-register `--input-file` (REQ-F-054, REQ-O-039)

For any command that declares `stdin_input: true`, the framework automatically registers `--input-file <path>`. When the payload would exceed 64 KB, reject at stdin read time and direct the caller to the flag. `--input-file <path>` (non-stdin) has no size limit — it reads in streaming chunks.

```python
MAX_STDIN_BYTES = 65_536  # configurable via TOOL_MAX_STDIN_BYTES

def read_stdin() -> str:
    data = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    if len(data) > MAX_STDIN_BYTES:
        fail_structured(
            code="STDIN_TOO_LARGE",
            message=f"Stdin payload exceeds {MAX_STDIN_BYTES}-byte limit",
            hint="Use --input-file <path> instead",
            context={"limit_bytes": MAX_STDIN_BYTES},
            exit_code=2,
        )
    return data.decode()
```

### Declare stdin paths in `--schema` output

Agents discover capabilities from machine-readable schema. Every stdin-reading argument must document `stdin_fallback`, `stdin_format`, and `non_tty_behavior` so agents can find the correct invocation pattern without trial-and-error.

```json
{
  "command": "bean commodity import",
  "flags": [
    {
      "name":             "--input-file",
      "type":             "string",
      "required":         true,
      "stdin_fallback":   true,
      "stdin_format":     "CSV with headers: symbol,name,precision,currency",
      "non_tty_behavior": "fail_with_exit_4",
      "overflow_flag":   "--input-file",
      "overflow_hint":   "For payloads >64 KB use --input-file <path> instead of stdin"
    }
  ]
}
```

---

## Safe Invocation Pattern for Agent Builders

Use this pattern for any command that accepts stdin input. The key: 32 KB is the conservative threshold — half the 64 KB pipe buffer, leaving headroom for output-side expansion.

```python
import subprocess, json, tempfile, os

PIPE_SAFE_BYTES = 32 * 1024  # conservative: 32 KB, half the pipe buffer

def invoke_stdin_command(cmd: list[str], payload: str) -> dict:
    payload_bytes = payload.encode()

    if len(payload_bytes) > PIPE_SAFE_BYTES:
        # Large payload → temp file to avoid §61 pipe deadlock
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(payload)
            tmp = f.name
        try:
            result = subprocess.run(
                [*cmd, "--input-file", tmp],
                capture_output=True, text=True,
                stdin=subprocess.DEVNULL,  # never inherit agent stdin (§50)
                timeout=30,
            )
        finally:
            os.unlink(tmp)
    else:
        # Small payload → safe to pipe via explicit -
        result = subprocess.run(
            [*cmd, "--input-file", "-"],
            input=payload,
            capture_output=True, text=True,
            timeout=30,
        )

    if result.returncode != 0:
        try:
            err = json.loads(result.stdout)
            raise RuntimeError(f"[{err['error']['code']}] {err['error']['message']}")
        except (json.JSONDecodeError, KeyError):
            raise RuntimeError(f"exit {result.returncode}: {result.stderr[:200]}")

    return json.loads(result.stdout)
```

`stdin=DEVNULL` is not optional. Without it, the subprocess inherits the agent's own stdin. If the agent is running non-interactively, that stdin is a pipe or `/dev/null` — any tool that silently falls back to stdin will consume it, corrupting the agent's own input stream.

---

## Checklist for AI Agents

Before calling any command that might read stdin:

1. Run `<tool> <command> --schema --output json` — check `flags[*].stdin_fallback`
2. If `stdin_fallback: true` is present, the flag accepts `-` for stdin input
3. If `non_tty_behavior` is absent or not `"fail_with_exit_4"`, use a temp file instead of piping
4. Always set `stdin=DEVNULL` unless explicitly sending data via `input=`
5. A process with zero CPU and zero output after 1 second is almost certainly blocked on an undeclared stdin read — kill it, switch to `--input-file`

If the schema has no stdin declaration at all, assume the command may silently fall back to stdin. Use a temp file for any payload and set a short timeout (5–10 seconds) as a circuit breaker.

---

## Implementation Checklist for CLI Authors

| Rule | Requirement | What to implement |
|------|-------------|-------------------|
| No silent stdin fallback | REQ-F-009 | Require explicit `--input-file` or `-`; no hidden stdin reads |
| Non-TTY fail-fast | REQ-F-009 · §50 | On `isatty() == false` with no `--input-file`: exit 4, `STDIN_REQUIRED`, under 1 s |
| 64 KB stdin cap | REQ-F-054 · §61 | Read at most 64 KB; reject with `STDIN_TOO_LARGE` + hint to `--input-file` |
| `--input-file` auto-registration | REQ-O-039 | Any command with `stdin_input: true` gets the flag; `--input-file -` == stdin |
| Schema declaration | §50 · §61 | `stdin_fallback`, `stdin_format`, `non_tty_behavior` present on every stdin arg |
| Structured errors | REQ-F-004 | All rejections use the response envelope; `code`, `message`, `hint` always present |

---

## Related

| Document | Relationship |
|----------|-------------|
| [§50 Stdin Consumption Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/50-critical-stdin-deadlock.md) | Provides: the blocking failure mode this guide prevents |
| [§61 Bidirectional Pipe Payload Deadlock](../challenges/01-critical-ecosystem-runtime-agent-specific/61-critical-pipe-payload-deadlock.md) | Provides: the pipe buffer failure mode this guide prevents |
| [§10 Interactivity & TTY Requirements](../challenges/02-critical-execution-and-reliability/10-critical-interactivity.md) | Provides: the interactive prompt failure mode referenced in this guide |
| [REQ-F-009](../requirements/f-009-non-interactive-mode-auto-detection.md) | Enforces: non-TTY detection and fail-fast at validation time |
| [REQ-F-054](../requirements/f-054-stdin-payload-size-cap-with-input-file-fallback.md) | Enforces: 64 KB stdin cap and `STDIN_TOO_LARGE` error |
| [REQ-O-039](../requirements/o-039-input-file-flag-for-stdin-commands.md) | Provides: `--input-file` auto-registration for stdin commands |
| [REQ-O-006](../requirements/o-006-stdin-as-id-source.md) | Provides: `-` convention for reading a single ID value from stdin |
| [schemas/response-envelope.md](../schemas/response-envelope.md) | Provides: canonical envelope schema used in all structured errors |
