# REQ-O-001: --format Output Format Flag

**Tier:** Opt-In | **Priority:** P0

**Source:** [§2 Output Format & Parseability](../challenges/04-critical-output-and-parsing/02-critical-output-format.md)

**Addresses:** Severity: Critical / Token Spend: High / Time: Medium / Context: High

---

## Description

The framework MUST register `--format <format>` as a standard flag on all commands. Supported formats MUST include at minimum: `json` (default in non-TTY), `jsonl` (one JSON object per line), `tsv` (tab-separated, for piping), and `plain` (minimal human-readable, no decoration). In `json` mode, color and prose are always suppressed. The selected format MUST be consistent across all commands in the framework.

`--format` is the sole canonical flag for selecting response representation. The framework SHOULD NOT expose aliases such as `--output` or `-o` for the same behavior, because aliases increase discovery ambiguity, complicate help and schema extraction, and reduce transferability of agent behavior across commands and tools.

`--output` is reserved for a destination path. A command that writes its result to a file MUST name that flag `--output <path>` (or `--output-dir <path>` for a directory); it MUST NOT use `--output` to select a representation. When `--output <path>` is present, `--format` selects the representation written to the file and stdout carries the `ResponseEnvelope` describing the write. A command that registers `--output <path>` MUST reject a value that exactly matches a supported format name (`json`, `jsonl`, `tsv`, `plain`, `table`, `id`) with exit `2` and a suggestion naming `--format <value>`, instead of writing a file with that name.

**Why not `--output`:** agents learn format selection from two conflicting traditions. Cloud CLIs (`aws`, `kubectl`, `az`, `helm`) use `--output json`; build and transfer tools (`gcc`, `curl`, `sort`, `pandoc`, `go build`) use `--output` for a file path. `--format` has one meaning almost everywhere it appears (`gcloud`, `docker`, `git`). An agent that passes `--output json` to a path-typed flag gets exit `0`, an empty stdout, and a stray file named `json`; the reverse mistake (`--format report.json`) fails loudly as an unsupported value.

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

---

## Schema

**Type:** [`response-envelope.md`](../schemas/response-envelope.md)

The `--format json` format uses the `ResponseEnvelope` shape. The `--format jsonl` and `--format tsv` formats use command-specific row shapes without the envelope wrapper.

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

---

## Example

The framework registers `--format` globally. Command authors do not implement it per command.

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
| [REQ-O-002](o-002-fields-selector.md) | O | Composes: `--fields` filters the `data` object within `--format json` responses |
| [REQ-O-004](o-004-output-jsonl-stream-flag.md) | O | Specializes: `--format jsonl` is the non-buffered streaming variant |
| [REQ-O-042](o-042-output-format-env-var-default.md) | O | Specializes: tool-scoped env var may supply the default when `--format` is omitted |
