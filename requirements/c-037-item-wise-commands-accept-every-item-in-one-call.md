# REQ-C-037: Item-Wise Commands Accept Every Item in One Call

**Tier:** Command Contract | **Priority:** P1

**Source:** [§70 Single-Argument Arity Forcing Agent Loop Overhead](../challenges/01-critical-ecosystem-runtime-agent-specific/70-high-single-argument-arity.md)

**Addresses:** Severity: High / Token Spend: Medium / Time: Medium / Context: Low

---

## Description

A command whose operation applies to each of several items of the same kind, one item at a time (`delete`, `move`, `tag`, `archive`, a `get` by ID), MUST accept every item the caller has in one call. An item that is a single value (a path, an ID, a name) is taken by a variadic last positional, declared `variadic: true` on its `PositionalEntry` ([REQ-C-015](c-015-commands-declare-input-and-output-schema.md)). An item that carries more than one value is taken as a batch input: one line or record per item on stdin, declared in the command's `stdin` ([REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md)), with `--input-file` reading the same way ([REQ-O-039](o-039-input-file-flag-for-stdin-commands.md)). Either way the agent passes the whole list in one invocation instead of looping one process per item.

**The declaration is the arity.** A positional without `variadic: true` takes exactly one value, so an agent reads the manifest and knows, before calling, whether to pass the list or loop over it. A command that takes several items never relies on the agent discovering that by probing.

**One shape for one item or many.** The response reports every item as [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) does: `data.summary` with `total`, `succeeded`, and `failed`, and `data.results[]` with one entry per item in the order given, each with `id` and `ok`, and an `error` when `ok` is `false`. A call with a single item returns the same shape with one entry, so the agent parses every call alike. When any item fails, the top-level `ok` is `false` and the exit code is non-zero (`3`, `PARTIAL_FAILURE`, when some items succeeded).

**Validate the whole list first.** Every item is validated before any item is acted on ([REQ-C-006](c-006-all-args-validated-in-phase-1.md)): a malformed item exits `2` with nothing done, and the error names the item, so a typo in the tenth item never leaves nine items changed.

## Acceptance Criteria

- `tool manifest` shows `variadic: true` on the last positional of every command that takes several single-value items as positionals
- `tool delete a b c` processes all three items in one process and exits `0` when each succeeds; it is never rejected with an unrecognized-argument error
- The response `data` carries `summary` and a `results[]` entry for every item, in the order given, each with `id` and `ok`
- `tool delete a` returns the same `summary` and `results[]` shape with one entry
- When one item fails and the others succeed, every item appears in `results[]`, the failed entry carries an `error` object, the top-level `ok` is `false`, and the command exits `3`
- A malformed item anywhere in the list exits `2` before any item is acted on, and the error names that item
- A command whose items carry more than one value declares `stdin` and reads one item per line or record from stdin or `--input-file`, reporting `results[]` the same way

---

## Schema

**Types:**

- [`manifest-response.md`](../schemas/manifest-response.md): `variadic: true` on the last `PositionalEntry` of an item-wise command; `stdin` on `CommandEntry` for a batch input
- [`response-envelope.md`](../schemas/response-envelope.md): `summary` and `results` inside `data`, as [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) defines them

```json
{
  "variadic": {
    "type": "boolean",
    "description": "True if the argument takes every remaining value. Allowed on the last entry only."
  }
}
```

---

## Wire Format

Manifest entry:

```json
{
  "schema_version": "3.21",
  "framework_version": "2.5.0",
  "etag": "sha256:91c4d0",
  "commands": {
    "delete": {
      "description": "Delete one or more notes",
      "danger_level": "destructive",
      "required_scopes": ["notes:write"],
      "flags": { "dry-run": { "type": "boolean", "required": false, "description": "Report which notes would be deleted without deleting them" } },
      "positionals": [{ "name": "paths", "type": "string", "required": true, "variadic": true, "description": "Paths of the notes to delete, one or more" }],
      "exit_codes": {
        "0": { "name": "SUCCESS", "description": "Every note is deleted", "retryable": false, "side_effects": "complete" },
        "2": { "name": "ARG_ERROR", "description": "A path is malformed; no note is deleted", "retryable": false, "side_effects": "none" },
        "3": { "name": "PARTIAL_FAILURE", "description": "Some notes are deleted and others failed; results lists each", "retryable": false, "side_effects": "partial" }
      }
    }
  }
}
```

An agent deletes three notes in one call:

```bash
$ tool --format json delete /notes/a.md /notes/b.md /notes/c.md
```

```json
{
  "ok": false,
  "data": {
    "partial": true,
    "summary": { "total": 3, "succeeded": 2, "failed": 1 },
    "results": [
      { "id": "/notes/a.md", "ok": true, "effect": "deleted" },
      { "id": "/notes/b.md", "ok": false, "error": { "code": "NOT_FOUND", "message": "No note at /notes/b.md", "retryable": false } },
      { "id": "/notes/c.md", "ok": true, "effect": "deleted" }
    ]
  },
  "error": { "code": "PARTIAL_FAILURE", "message": "1 of 3 notes could not be deleted" },
  "warnings": [],
  "meta": { "exit_code": 3, "duration_ms": 41 }
}
```

---

## Example

```
register command "delete":
  danger_level: destructive
  positionals:
    paths: type: string, required: true, variadic: true
  exit_codes:
    SUCCESS        (0): description: "Every note is deleted",              retryable: false, side_effects: complete
    ARG_ERROR      (2): description: "A path is malformed; no note is deleted", retryable: false, side_effects: none
    PARTIAL_FAILURE(3): description: "Some notes are deleted and others failed", retryable: false, side_effects: partial

  validate(args):
    for path in args.paths:              # every item before any work
      require_note_path(path)            # exit 2, naming the path, on the first malformed one

  execute(args):
    results = []
    for path in args.paths:
      try:
        delete_note(path)
        results.append(id=path, ok=True, effect="deleted")
      except NoteError as e:
        results.append(id=path, ok=False, error=classify(e))
    failed = [r for r in results if not r.ok]
    return response(PARTIAL_FAILURE if failed else SUCCESS, partial=bool(failed),
                    summary={total: len(results), succeeded: len(results)-len(failed), failed: len(failed)},
                    results=results)

# Agent consults the manifest before calling:
# variadic: true on the last positional → pass every item in one call
# variadic absent → one item per call
```

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [§70](../challenges/01-critical-ecosystem-runtime-agent-specific/70-high-single-argument-arity.md) | — | Sources: the failure mode this requirement removes |
| [REQ-C-009](c-009-multi-step-commands-report-completed-failed-skippe.md) | C | Consumes: `summary` and per-item `results[]` report each item's outcome |
| [REQ-C-015](c-015-commands-declare-input-and-output-schema.md) | C | Extends: `variadic` on the last `PositionalEntry` declares the arity |
| [REQ-C-006](c-006-all-args-validated-in-phase-1.md) | C | Enforces: every item is validated before any item is acted on |
| [REQ-F-001](f-001-standard-exit-code-table.md) | F | Consumes: `ARG_ERROR (2)` for a malformed item, `PARTIAL_FAILURE (3)` when some items fail |
| [REQ-F-054](f-054-stdin-payload-size-cap-with-input-file-fallback.md) | F | Composes: a batch of multi-value items arrives on stdin under the declared `stdin` mode |
| [REQ-O-039](o-039-input-file-flag-for-stdin-commands.md) | O | Composes: `--input-file` reads the same batch from a file |
| [REQ-O-041](o-041-tool-manifest-built-in-command.md) | O | Exposes: `variadic` appears in the manifest |
