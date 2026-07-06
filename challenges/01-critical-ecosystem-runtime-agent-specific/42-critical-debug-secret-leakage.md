> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §42

## 42. Debug / Trace Mode Secret Leakage

**Severity:** Critical | **Frequency:** Situational | **Detectability:** Hard | **Token Spend:** Low | **Time:** Low | **Context:** High

### The Problem

CLI frameworks often provide debug/trace modes that dump full invocation context to aid debugging. Python Fire's `--trace` flag prints the complete call trace including all argument values. Many tools have `--debug` or `--verbose` flags that log full request/response details. In agent contexts, these modes are dangerous because:

1. **Secrets in argument values are exposed verbatim**: An agent invokes `my-tool deploy --api-key sk-abc123` and adds `--trace`. The trace output includes `sk-abc123` in plaintext. If this trace is captured to logs or returned to the LLM context, the secret is exposed.

2. **Secrets in process tables**: Arguments passed as `--token <value>` appear in `process.argv` (Node.js), `sys.argv` (Python), and the system process table (`ps aux`). Any process with read access to `/proc/<pid>/cmdline` can extract the secret.

3. **Secrets in error messages**: Many frameworks echo back invalid argument values in error messages. `argparse` error for a bad `--api-url` value: `error: argument --api-url: invalid url value: 'http://secret-host/'`. If the "secret" is in a URL, it is now in stderr.

This is distinct from challenge #24 (Authentication & Secret Handling), which concerns the *storage* and *loading* of secrets (env vars, keychain, SecretStr). This challenge concerns the *leakage of secrets into diagnostic output* — traces, error messages, debug logs — that occurs after the secret has been successfully loaded.

```python
# Python Fire: --trace dumps everything
$ python my_fire_app.py deploy --api_key=sk-abc123 --region=us-east-1 -- --trace
Fire trace:
  1. Initial component
  2. ('deploy',): Called routine deploy(api_key='sk-abc123', region='us-east-1')
# api_key is now in plaintext in stdout
```

```bash
# Process table exposure
$ ps aux | grep my-tool
user 12345 ... my-tool deploy --api-key sk-abc123 --region us-east-1
# Secret visible to any user who can run ps
```

### Impact

- Secrets (API keys, tokens, passwords) exposed in debug output that may be captured by log collectors, audit systems, or LLM context
- Process table exposure makes secrets visible to all users on the system during command execution
- Error messages that echo back argument values can expose partial secrets
- If the LLM context receives a trace with a secret, the secret may be included in future prompts, embeddings, or log entries
- Particularly dangerous when agents run in shared infrastructure (CI/CD, multi-tenant environments)

### Solutions

**For CLI authors:**
```python
from pydantic import SecretStr

class DeployConfig(BaseModel):
    api_key: SecretStr  # repr never shows value; model_dump() returns "[REDACTED]"
    region: str

# Argparse: use action to mask value in namespace repr
import argparse
class SecretAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
    def __repr__(self):
        return f"{self.dest}=[REDACTED]"
```

**For framework design:**
- Apply name-based heuristics to automatically redact argument values whose names match `token|secret|password|key|credential|auth|apikey` in all trace/debug output
- Never echo argument values in error messages for arguments marked `sensitive=True` or matching the redaction pattern
- Provide a framework-level `--trace-safe` mode that produces a trace with sensitive fields replaced by `[REDACTED]`
- For `--trace` or `--debug` modes: require explicit `--no-redact` opt-out to expose sensitive values
- Use environment variables (not CLI flags) as the preferred injection mechanism for secrets — they are not visible in `process.argv` or process tables
- Document in `--schema` output which arguments are marked sensitive: `"sensitive": true`

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | `--trace` or `--debug` mode exposes secret flag values verbatim; no redaction; error messages echo secret argument values |
| 1 | Some redaction in debug output; error messages still echo values for sensitive flags |
| 2 | Sensitive flag values redacted as `[REDACTED]` in all trace/debug/error output; no flag values in process table |
| 3 | `--trace-safe` mode available; `"sensitive": true` declared in schema; env var injection preferred over flag injection documented |

**Check:** Pass `--token <secret>` and `--debug`, then verify stdout/stderr contains `[REDACTED]` instead of the secret value.

---

### Agent Workaround

**Signature:** stdout or stderr from a `--debug`/`--trace`/`--verbose` run echoes a secret flag value verbatim; secret also visible in `ps` output while the command runs

**Tier:** A (one safe command, no branching)

**Always inject secrets via environment variables, never via CLI flags; scan output for leaked secrets:**

```python
import subprocess, os, re

# Inject secrets via env vars — not visible in process table or traces
env = {
    **os.environ,
    "MY_TOOL_TOKEN": secret_token,   # env var injection (safe)
    # NEVER: ["tool", "--token", secret_token]  ← appears in ps aux
}

result = subprocess.run(
    ["tool", "deploy"],   # no secret flag
    capture_output=True, text=True,
    env=env,
)

# Scan captured output for accidental secret leakage
SENSITIVE_PATTERN = re.compile(
    r'(token|secret|password|api.?key|credential)["\s:=]+([A-Za-z0-9+/._\-]{8,})',
    re.IGNORECASE,
)
for stream_name, content in [("stdout", result.stdout), ("stderr", result.stderr)]:
    matches = SENSITIVE_PATTERN.findall(content)
    if matches:
        print(f"WARNING: Possible secret leak in {stream_name}: {[m[0] for m in matches]}")
```

**Limitation:** If the tool's debug mode unconditionally prints all argument values and there is no `--trace-safe` mode, the only safe option is to avoid debug mode entirely — never pass `--trace`, `--debug`, or `--verbose` when secrets are present in any argument
