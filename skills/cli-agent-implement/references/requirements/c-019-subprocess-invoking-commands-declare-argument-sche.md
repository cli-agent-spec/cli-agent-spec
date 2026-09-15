# REQ-C-019: Subprocess-Invoking Commands Declare Argument Schema

**Tier:** Command Contract | **Priority:** P1

**Source:** [§34 Shell Injection via Agent-Constructed Commands](../challenges/01-critical-ecosystem-runtime-agent-specific/34-critical-shell-injection.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: High / Context: Medium

---

## Description

Any command that invokes a subprocess with arguments derived from user input MUST declare in its registration schema: the subprocess binary name, which of its arguments originate from user input (by field name), and which arguments are framework-hardcoded. The framework enforces this declaration at registration and uses it to apply REQ-F-044 metacharacter rejection to exactly the user-derived arguments. Commands MUST use the framework's `subprocess()` API rather than raw `os.system()`, `subprocess.Popen(shell=True)`, or `child_process.exec()`.

## Acceptance Criteria

- A command using the framework's `subprocess()` API with a user-supplied argument is automatically protected by REQ-F-044
- A command that uses `os.system()` directly is flagged by the framework's registration linter
- The `--schema` output for subprocess-invoking commands includes a `subprocess` section listing the binary and user-controlled arguments
- An attempt to pass a shell metacharacter in a user-derived subprocess argument is rejected with exit code 2

---

## Schema

**Types:** [`manifest-response.md`](../schemas/manifest-response.md)

A `subprocess` section is added to `CommandEntry` in `--schema` output:

| Field | Type | Description |
|-------|------|-------------|
| `subprocess.binary` | string | Executable name invoked by this command |
| `subprocess.user_controlled_args` | string[] | Flag names whose values are passed as subprocess arguments |
| `subprocess.hardcoded_args` | string[] | Argument fragments always passed verbatim by the framework |

---

## Wire Format

```bash
$ tool run --schema
```
```json
{
  "parameters": {
    "script": { "type": "string", "required": true,  "description": "Path to script file to execute" },
    "args":   { "type": "array",  "required": false, "description": "Arguments passed to the script" }
  },
  "subprocess": {
    "binary": "bash",
    "user_controlled_args": ["script", "args"],
    "hardcoded_args": ["--norc", "--noprofile"]
  },
  "exit_codes": {
    "0": { "name": "SUCCESS",   "description": "Script completed successfully", "retryable": false, "side_effects": "complete" },
    "2": { "name": "ARG_ERROR", "description": "Shell metacharacter in argument", "retryable": false,"side_effects": "none" }
  }
}
```

---

## Example

```
register command "run":
  subprocess:
    binary: bash
    hardcoded_args: ["--norc", "--noprofile"]
    user_controlled_args: [script, args]
  parameters:
    script: type=string, required=true, description="Path to script file"
    args:   type=array,  required=false, description="Arguments passed to the script"

  # framework applies REQ-F-044 metacharacter rejection to 'script' and 'args' automatically
  # framework raises registration error if raw os.system() is detected instead of subprocess()
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-044](f-044-shell-argument-escaping-enforcement.md) | F | Enforces: metacharacter rejection applied to all declared `user_controlled_args` |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Composes: `subprocess` section is part of the `--schema` output |
| [REQ-C-020](c-020-resource-id-fields-declare-validation-pattern.md) | C | Composes: `user_controlled_args` that are resource IDs also declare validation patterns |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Enforces: subprocess argument validation happens in Phase 1 before any I/O |
