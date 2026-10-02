# REQ-O-001: --format Output Format Flag

**Tier:** Opt-In | **Priority:** P0

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md) · [§78 Output Flag Meaning Collision](../challenges/01-critical-ecosystem-runtime-agent-specific/78-high-output-flag-meaning-collision.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MUST register `--format <format>` as a standard flag on all commands. Supported formats MUST include at minimum: `json` (default in non-TTY), `jsonl` (one JSON object per line), `tsv` (tab-separated, for piping), and `plain` (minimal human-readable, no decoration). In `json` mode, color and prose are always suppressed. The selected format MUST be consistent across all commands in the framework.

`--format` is the sole canonical flag for selecting response representation. The framework SHOULD NOT expose aliases such as `--output` or `-o` for the same behavior, because aliases increase discovery ambiguity, complicate help and schema extraction, and reduce transferability of agent behavior across commands and tools.

`--output` is reserved for a destination path. A command that writes its result to a file MUST name that flag `--output <path>` (or `--output-dir <path>` for a directory); it MUST NOT use `--output` to select a representation. When `--output <path>` is present, `--format` selects the representation written to the file (except for the cases `output_file` declares otherwise, below) and stdout carries the `ResponseEnvelope` describing the write. A command that registers `--output <path>` MUST reject a value that exactly matches a supported format name (`json`, `jsonl`, `tsv`, `plain`, `table`, `id`) with exit `2` and a suggestion naming `--format <value>`, instead of writing a file with that name.

**Binary results.** A command whose result is a single binary value (the payload [REQ-F-017](f-017-binary-field-base64-encoding.md) wraps as `{"type": "binary", ...}`) is the exception: its result *is* a file (a downloaded report, an export dump, a rendered image), and no `--format` representation of it is that file. When such a command receives `--output <path>`, the framework MUST write the raw bytes to the path through the atomic-write primitive ([REQ-F-070](f-070-atomic-write-via-rename.md)), and `--format` selects only the representation of the response on stdout. The envelope's `data` describes the write as `{path, bytes, content_type, sha256}`: `bytes` is the byte count, `sha256` the lowercase hex digest of the file's contents, and `content_type` is present only when the command declares one. `--output -` on a binary result MUST exit `2` and write nothing, because stdout carries only envelopes. Without `--output`, the payload stays in the envelope as REQ-F-017 encodes it. Downloaders already behave this way (`curl -o`, `gh release download`, `aws s3 cp`).

**Declaring what the file holds.** The manifest entry of every command that registers `--output <path>` MUST carry `output_file`, so an agent knows before the call what lands in the file. Absence means the command has no `--output`. The value is one of:

| Value | Who writes the file | What the file holds |
|-------|---------------------|---------------------|
| `formatted` | Framework | The `--format` representation of the result |
| `binary` | Framework | The raw bytes of a binary result; `data` describes the write (above) |
| `handler` | Command handler | Content the command's own documentation describes; `--format` does not select it |
| `envelope` | Framework | The command's final `ResponseEnvelope` as JSON, whatever `--format` selects; `--format` shapes only stdout |

`handler` covers a command whose handler owns the path (a compiler's object file, an archiver's tarball); the handler SHOULD write it through the atomic-write primitive ([REQ-F-070](f-070-atomic-write-via-rename.md)). `envelope` covers a command whose stdout carries something other than a single envelope, such as a child process's output streamed through, so the file is where the agent reads the structured result. The format-name rejection above applies whatever the value.

**`--output` versus an `output` side effect.** `output_file` declares a path the caller names per call. A location the command picks itself for its product (a fixed or templated directory such as `{project_root}/tmp/dashboard/`) is declared instead as a `filesystem_side_effects` entry with `type: "output"` (REQ-C-011). The two never describe the same write: the `--output` path is not repeated as an `output` entry, though a default location used when `--output` is absent is one.

**Where a relative path lands.** A relative `--output` path resolves against the working directory unless the command declares otherwise in `output_file_base`, which is present only alongside `output_file`. An absolute path is used as given, whatever the base. The values:

- `cwd` (the default, also meant by absence): the working directory of the invocation
- `project_root`: the project root the tool resolves for this invocation (for example the nearest ancestor holding its project file), so the same relative path lands in the same place from any subdirectory
- `resource`: the directory of the resource the command acts on (a package, a workspace, a deployment's folder), which the command's description names

A command whose base is not `cwd` MUST declare it, because an agent that resolves the path against its working directory otherwise looks for the file in the wrong place.

**Why not `--output`:** agents learn format selection from two conflicting traditions. Cloud CLIs (`aws`, `kubectl`, `az`, `helm`) use `--output json`; build and transfer tools (`gcc`, `curl`, `sort`, `pandoc`, `go build`) use `--output` for a file path. `--format` selects a representation wherever it appears (`gcloud`, `docker`, `git`, `pandoc`'s `--to`), and the representation applies to whatever destination the result goes to: stdout by default, the file named by `--output` otherwise. An agent that passes `--output json` to a path-typed flag gets exit `0`, an empty stdout, and a stray file named `json`; the reverse mistake (`--format report.json`) fails loudly as an unsupported value.

`--format` values MUST come from a closed set declared at registration and listed in the manifest. An unknown value exits `2` with a structured error listing the supported values; the framework MUST NOT interpret an unrecognized value as a template. Tools that overload `--format` with templates show why: `docker` reads any value other than `json` or `table` as a Go template, so the typo `docker version --format jsn` prints `jsn` instead of failing. `git` guesses from the value (a `%` or a `tformat:` prefix means a template, anything else must be a preset name), which catches `--format=json` but still leaves the agent to learn a second grammar; `gcloud` rejects the typo and lists the valid values, which is the behavior this requirement asks for. Field projection belongs to `--fields` ([REQ-O-002](o-002-fields-selector.md)): `--format tsv --fields hash,subject` covers what `--format='%H %s'` does, with field names validated against the schema. A CLI that wants free-form text templates for human use registers them under a separate flag (`--template`), never as a `--format` value.

**Media types.** The spec fixes the media type of each format value it defines:

| Value | Media type |
|-------|------------|
| `json` | `application/json` |
| `jsonl` | `application/x-ndjson` |
| `tsv` | `text/tab-separated-values` |
| `plain` | `text/plain` |
| `table` | `text/plain` |
| `id` | `text/plain` |

A tool MAY register its own format values beside these, such as `html` for a self-contained page a person reads. The manifest's root `format` flag MUST then carry `media_types`, a map from format value to media type (`{"html": "text/html"}`), with an entry for every value outside the table above; an entry for a value in the table is optional and, when present, MUST equal the table's media type. Every key MUST be one of the flag's `enum_values`, and only the `format` flag carries `media_types`. A media type is written lowercase as `type/subtype`, without parameters. A command-specific format value (REQ-O-049) declares its media type in the command's `output_media_types` instead. An agent parses a format's output as JSON only when its media type is `application/json`, `application/x-ndjson`, or a `+json` type, and treats any other format's output as an opaque artifact.

If the framework also implements [REQ-O-042](o-042-output-format-env-var-default.md), the environment variable provides only a default value. `--format` remains the authoritative interface and MUST override the environment variable whenever both are present.

## Output modes and the role of `--format`

The framework has two distinct output contexts. The `--format` flag governs structured output only — it does not replace the default rich terminal experience.

| Context | Trigger | What the user sees |
|---------|---------|-------------------|
| TTY (default) | No flag, stdout is a terminal | Rich output: colors, borders, spinners, progress bars (Click / Rich style) |
| `--format table` | Explicit flag | Structured table, no color, ASCII borders — readable in CI logs, SSH sessions, `NO_COLOR` environments |
| `--format plain` | Explicit flag | Flat text lines, no decoration, no structure |
| `--format json` | Explicit flag or non-TTY auto | `ResponseEnvelope` JSON — primary agent format |
| `--format jsonl` | Explicit flag | One JSON object per line — streaming agent format |
| `--format tsv` | Explicit flag | Tab-separated rows — shell pipeline format |

**Rich output (TTY default) is not a `--format` value.** It is the framework's natural rendering mode when stdout is a terminal. REQ-F-007, REQ-F-008, and REQ-F-009 govern its suppression in non-TTY contexts. Do not expose it as `--format rich` — that conflates the rendering layer with the format selection flag.

**`table` is recommended but not mandatory.** It fills the gap between `plain` (no structure) and `json` (machine-oriented). Implement it when your users regularly work in color-stripped environments (CI, SSH, `NO_COLOR`) and need human-readable tabular output without requiring JSON parsing. Borders degrade gracefully: Unicode → ASCII when the terminal cannot render them.

## Format trade-offs

| Format | Best for | Pros | Cons |
|--------|----------|------|------|
| TTY default | Interactive human use | Colors, borders, spinners — full Rich/Click experience | Unparseable; suppressed automatically in non-TTY |
| `table` | Humans in color-stripped environments | Structured, scannable; degrades to ASCII borders gracefully | Not machine-parseable; column widths vary |
| `plain` | Minimal human output, log-friendly | No decoration, consistent line-per-item | No column alignment; no type information |
| `json` | Agent consumption, structured data | Unambiguous schema, envelope preserves `ok`/`error`/`meta`, universal parser support | Verbose for humans; not streamable |
| `jsonl` | Streaming, large result sets, piping | One object per line — agent processes incrementally without buffering full response | No envelope wrapper; agent must handle partial reads |
| `tsv` | Shell pipelines, `awk`/`cut` composition | Compact, trivial to pipe into `awk`/`cut`/`sort` | No type information; multi-line values break the format |

**Why YAML is not included:** YAML has multiple incompatible spec versions, implicit type coercion (the Norway problem: `NO` parses as `false`), and no streaming form. For agent consumption it adds parsing risk with no benefit over JSON. For human readability `table` or `plain` cover the use case. YAML belongs on the config input side only — never as structured CLI output.

## Acceptance Criteria

- `--format json` produces valid JSON on stdout
- `--format jsonl` produces one valid JSON object per line
- `--format tsv` produces tab-separated values with a header row
- The `--format` flag is available on every command without per-command implementation
- No alias flag such as `--output` or `-o` selects the same response representation behavior
- `--output json` on a command whose `--output` takes a path exits `2` with a suggestion naming `--format json`, and writes no file
- `--format csv --output report.csv` writes CSV to `report.csv` and emits a `ResponseEnvelope` on stdout
- `download --output report.xml --format json` on a command with a binary result writes the raw bytes to `report.xml`; stdout is a `ResponseEnvelope` whose `data.bytes` equals the file size and whose `data.sha256` matches the file's digest
- `download --output -` on a command with a binary result exits `2` and writes nothing to stdout or to any file
- `download` without `--output` returns the binary payload in the envelope as REQ-F-017 encodes it
- A failed run of a command with a binary result leaves no file at the `--output` path
- The manifest entry of every command that registers `--output <path>` carries `output_file`: `"binary"` when its result is binary, `"handler"` when its handler writes the file, `"envelope"` when the framework writes the final JSON envelope to the file, `"formatted"` otherwise; no other command carries it
- A command that resolves a relative `--output` against anything but the working directory declares `output_file_base`; `output_file_base` never appears without `output_file`
- On an `output_file_base: "project_root"` command run from a subdirectory, `--output out/r.json` writes `<project root>/out/r.json`, and an absolute `--output` path is written as given
- On an `output_file: "envelope"` command, `--output result.json --format plain` writes a valid JSON `ResponseEnvelope` to `result.json`
- The root `format` flag in the manifest carries `media_types` with an entry for every `enum_values` value outside the spec's media type table, every key is one of `enum_values`, and every spec value it lists maps to the table's media type
- No flag other than the root `format` flag carries `media_types`
- `--format` with a value outside the declared set (`--format jsn`, `--format '%H %s'`) exits `2`, lists the supported values, and writes nothing to stdout or to any file

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

The `--format json` format uses the `ResponseEnvelope` shape. The `--format jsonl` and `--format tsv` formats use command-specific row shapes without the envelope wrapper.

The manifest declares the media type of a tool's own format values in the root `format` flag's `media_types` ([`manifest-response.md`](../schemas/manifest-response.md)), and the `--output` behavior in `CommandEntry.output_file` and the base of a relative path in `CommandEntry.output_file_base` ([`manifest-response.md`](../schemas/manifest-response.md)).

---

## Wire Format

```bash
$ tool deploy --target staging --format json
```

```json
{
  "ok": true,
  "data": { "id": "deploy-42", "status": "complete", "target": "staging" },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 340 }
}
```

JSONL format (one object per line, no envelope wrapper):

```bash
$ tool list --format jsonl
```

```
{"id": "1", "name": "alice"}
{"id": "2", "name": "bob"}
```

Binary result written to `--output`: the file holds the raw bytes, stdout holds the envelope describing the write:

```bash
$ tool download --output report.xml --format json
```

```json
{
  "ok": true,
  "data": {
    "path": "report.xml",
    "bytes": 48213,
    "content_type": "application/xml",
    "sha256": "9f2c4a7e1b0d83f5c6a2e9d417b38c05f1e6a9d2c4b7e8f03a5d6c1b2e9f4a70"
  },
  "error": null,
  "warnings": [],
  "meta": { "exit_code": 0, "duration_ms": 812 }
}
```

---

## Example

The framework registers `--format` as a global option (REQ-F-079). Command authors do not implement it per command, and no command registers a local `--format` or reuses its short alias.

```
app = Framework("tool")
app.enable_format_flag(formats=["json", "jsonl", "tsv", "plain"])

# All commands automatically accept --format json / --format jsonl / etc.
# tool deploy --target staging --format json  →  ResponseEnvelope JSON
# tool list --format tsv  →  tab-separated rows with header
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-003](f-003-json-output-mode-auto-activation.md) | F | Extends: `--format json` makes auto-activation explicit and overridable |
| [REQ-F-004](f-004-consistent-json-response-envelope.md) | F | Provides: `ResponseEnvelope` used by `--format json` mode |
| [REQ-F-017](f-017-binary-field-base64-encoding.md) | F | Consumes: a binary result is written raw to `--output` instead of base64-encoded in the envelope |
| [REQ-F-070](f-070-atomic-write-via-rename.md) | F | Consumes: every `--output` write, formatted or raw, goes through the atomic rename |
| [REQ-F-079](f-079-global-option-scope.md) | F | Enforces: `--format` is accepted in any position on every command and listed in the manifest root `flags` |
| [REQ-O-002](o-002-fields-selector.md) | O | Composes: `--fields` filters the `data` object within `--format json` responses |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Specializes: `--format jsonl` is the non-buffered streaming variant |
| [REQ-O-042](o-042-output-format-env-var-default.md) | O | Specializes: tool-scoped env var may supply the default when `--format` is omitted |
| [REQ-C-011](c-011-commands-declare-filesystem-side-effects.md) | C | Composes: a command-chosen product path is a `type: "output"` side effect, not an `--output` path |
| [REQ-O-049](o-049-llm-token-budget-flags.md) | O | Composes: a command-specific format value declares its media type in `output_media_types` |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `media_types` appears on the root `format` flag in the manifest |
