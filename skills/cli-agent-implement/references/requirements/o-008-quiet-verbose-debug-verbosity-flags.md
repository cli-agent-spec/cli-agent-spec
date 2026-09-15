# REQ-O-008: --quiet / --verbose / --debug Verbosity Flags

**Tier:** Opt-In | **Priority:** P1

**Source:** [§4 Verbosity & Token Cost](../challenges/04-critical-output-and-parsing/04-medium-verbosity.md)

**Addresses:** Severity: Medium / Token Spend: High / Time: Low / Context: High

---

## Description

The framework MUST provide `--quiet` (suppress all stderr; stdout JSON only), `--verbose` (progress messages on stderr), and `--debug` (full debug trace on stderr) as standard flags on every command. These MUST override the auto-quiet behavior (REQ-F-038). The verbosity levels MUST be mutually exclusive. In `--debug` mode, all framework-internal operations (config loading, lock acquisition, HTTP requests) MUST be logged to stderr.

## Acceptance Criteria

- `--quiet` produces zero bytes on stderr (even for warnings)
- `--verbose` produces progress messages on stderr and the JSON result on stdout
- `--debug` produces full diagnostic trace on stderr including all HTTP requests and config resolution steps
- Passing `--verbose` with `CI=true` overrides the auto-quiet mode

---

## Schema

No dedicated schema type — verbosity flags govern stderr content only. In `--debug` mode, `meta.debug` fields may be added to the `ResponseEnvelope` by framework internals, but no new top-level schema type is defined.

---

## Wire Format

Quiet mode — no stderr output:

```bash
$ tool deploy --target staging --quiet --output json
```

```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 340 }
}
```

Debug mode — stderr diagnostic trace, stdout unchanged:

```bash
$ tool deploy --target staging --debug --output json
```

stderr:
```
[DEBUG] Loading config from /home/user/.config/tool/config.yaml
[DEBUG] HTTP POST https://api.example.com/deploys → 201 Created (142ms)
[DEBUG] Lock acquired: /tmp/tool.lock (pid 18432)
```

stdout:
```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 340, "debug": { "config_file": "/home/user/.config/tool/config.yaml" } }
}
```

---

## Example

The framework registers all three verbosity flags globally at opt-in time.

```
app = Framework("tool")
app.enable_verbosity_flags()

# tool deploy --quiet       →  zero stderr bytes
# tool deploy --verbose     →  progress on stderr, JSON on stdout
# tool deploy --debug       →  full trace on stderr, meta.debug in JSON
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-038](f-038-verbosity-auto-quiet-in-non-tty-context.md) | F | Provides: auto-quiet baseline that `--verbose` and `--debug` override |
| [REQ-F-006](f-006-stdout-stderr-stream-enforcement.md) | F | Enforces: diagnostic output stays on stderr, JSON stays on stdout |
| [REQ-F-051](f-051-debug-and-trace-mode-secret-redaction.md) | F | Enforces: secrets are redacted even in `--debug` output |
| [REQ-O-012](o-012-heartbeat-interval-flag.md) | O | Composes: heartbeat messages respect `--quiet` suppression |
