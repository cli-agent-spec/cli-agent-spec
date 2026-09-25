> **Part VII: Ecosystem, Runtime & Agent-Specific** | Challenge §78

## 78. Output Flag Meaning Collision

**Source:** FP

**Severity:** High | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Medium | **Time:** Medium | **Context:** Low

### The Problem

Agents learn what `--output` means from two traditions that disagree. Cloud CLIs read it as a representation: `aws --output json`, `kubectl -o json`, `az -o table`, `helm -o yaml`. Build and transfer tools read it as a destination path: `gcc -o main`, `curl -o page.html`, `sort -o sorted.txt`, `pandoc -o doc.pdf`. An agent that wants JSON reaches for `--output json` or `-o json` by habit, whatever the tool in front of it does with that flag.

When the tool's `--output` takes a path, the call succeeds:

```bash
$ tool export --output json
$ echo $?
0
$ ls
json
```

The result went into a file named `json` in the working directory. Stdout is empty, or carries a one-line human summary (`Exported 42 records`). Nothing on stdout or stderr says the flag was read as a path. The agent sees exit `0`, finds no data to parse, and typically retries with other flags or reports that the command returned nothing. Each retry may write or overwrite another stray file.

The mirror case is louder but still costly: a tool whose `--output` selects a format, called with `--output report.json` by an agent that wanted a file, fails with an "invalid choice" error, and the agent has to rediscover which flag writes files.

`--format` has its own silent case. Some tools accept a template in `--format` as well as named formats, and read any value that is not a known name as literal template text. `docker` reads any value other than `json` or `table` as a Go template, so the typo `docker version --format jsn` exits `0` and prints `jsn`. The agent gets well-formed but meaningless lines instead of an error.

Short aliases make it worse. `-o` has the same split, and a tool may bind `-o` to a path while its long `--output` does not exist, so even `--help` inspection keyed on the long name misses it.

### Impact

- Exit `0` with no parseable output; nothing signals a retry or a wrong flag
- Stray files (`json`, `yaml`, `table`) in the working directory, which may be committed, overwritten on retry, or picked up by later globs
- A second invocation with the "fixed" flags overwrites the stray file silently, so its contents cannot be used to confirm what happened
- Token and round-trip cost: the agent debugs an empty result instead of a flag error

### Solutions

**Select representation with `--format`; reserve `--output` for a destination path (REQ-O-001):**

```bash
tool export --format json                     # envelope with data on stdout
tool export --format csv --output report.csv  # CSV in the file, envelope on stdout
```

`--format` selects a representation wherever it appears (`gcloud`, `docker`, `git`), so an agent's trained guess lands on the right flag. The representation applies to any destination: stdout by default, the `--output` file otherwise. `-o` is not bound to a format.

**Keep `--format` a closed set (REQ-O-001):**

An unknown `--format` value exits `2` with the supported values listed; it is never read as a template. Field projection goes through `--fields` (REQ-O-002), and a CLI that wants text templates for humans registers a separate `--template` flag.

**Reject a format name where a path is expected:**

A path-typed `--output` that receives a value exactly matching a supported format name (`json`, `jsonl`, `tsv`, `plain`, `table`, `id`, and common extras such as `yaml`, `csv`, `text`) exits `2` with a structured error and writes nothing:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "ARG_ERROR",
    "message": "--output takes a file path; \"json\" is a format name",
    "retryable": false,
    "fix_command": "tool export --format json"
  },
  "warnings": [],
  "meta": { "exit_code": 2, "duration_ms": 1 }
}
```

A caller who really wants a file named `json` passes `./json`.

**Report every file written:**

A command that writes to disk names the absolute path in the envelope (`data.path`, REQ-F-040), so an agent that did not expect a file can still see that one was created.

**Framework design:**
- Register `--format` as the global representation flag; never register `--output` or `-o` as an alias for it (REQ-O-001)
- Apply the format-name guard to every path-typed flag named `--output`, `-o`, or `--output-dir` at the framework level, not per command

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | `--output json` (or `-o json`) exits `0` and writes a file named `json`; stdout gives no sign of it |
| 1 | `--output json` writes the file, but stdout or the envelope names the path written |
| 2 | `--output` selects a format (an alias of the representation flag), or `--output json` is rejected with a plain-text error |
| 3 | Representation is `--format`; a path-typed `--output` rejects format names with exit `2` and a structured error naming `--format <value>`; no file is written |

**Check:** In an empty temporary directory, run `tool <cmd> --output json` and `tool <cmd> -o json`. Record the exit code, stdout, and the directory listing afterwards. A new file named `json` with exit `0` scores 0.

---

### Agent Workaround

**Signature:** `exit 0` with empty or non-JSON stdout after passing `--output <format>` or `-o <format>`; a file named after the format value (`json`, `yaml`, `table`) appears in the working directory; or `exit 0` after `--format <value>` with stdout repeating that literal value on every line

**Tier:** B (one observable check, then one command)

**Check the flag's type in `--help` before using it; if a stray file appeared, remove it and rerun with `--format`:**

```python
import os
import re
import subprocess

FORMAT_NAMES = {"json", "jsonl", "yaml", "yml", "table", "text", "plain", "tsv", "csv", "id"}

def output_takes_path(help_text: str) -> bool:
    """True when --output/-o is documented with a path-like metavar or wording."""
    for line in help_text.splitlines():
        if re.search(r"(^|\s)(-o|--output)\b", line):
            return bool(re.search(r"FILE|PATH|DIR|<file>|<path>|write .* to|destination", line, re.I))
    return False

def run_for_json(cmd: list[str]) -> subprocess.CompletedProcess:
    help_text = subprocess.run([*cmd, "--help"], capture_output=True, text=True).stdout
    flag = ["--format", "json"] if "--format" in help_text or output_takes_path(help_text) else ["--output", "json"]
    before = set(os.listdir("."))
    result = subprocess.run([*cmd, *flag], capture_output=True, text=True)
    stray = {name for name in set(os.listdir(".")) - before if name.lower() in FORMAT_NAMES}
    for name in stray:
        os.remove(name)
    if stray and flag[0] == "--output":
        result = subprocess.run([*cmd, "--format", "json"], capture_output=True, text=True)
    return result
```

If every stdout line equals the `--format` value you passed, the tool read it as a template: rerun with `--json` if listed, or with a template the tool documents (`--format '{{json .}}'` for `docker`), and parse that.

When `--help` shows neither `--format` nor a path hint, prefer `--json` if it is listed, then `--format json`, and only then `--output json`; after any call with `--output`, compare the working directory listing against the one taken before the call.

**Limitation:** A tool that writes the file somewhere other than the working directory, or under a name that is not the bare format value, leaves no stray file to detect; and `--help` wording is free text, so the path check is a heuristic that one failed call may be needed to confirm
