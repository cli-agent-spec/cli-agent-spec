# Schema: FailureModeIndex

**File:** [`failure-mode-index.json`](failure-mode-index.json)

> **Used by:** [`challenges/index.json`](../challenges/index.json) · `scripts/build_failure_index.py` · `cli-agent-diagnose` skill

---

## Purpose

The failure mode corpus is written for people in markdown. Harnesses, classifiers, and agents need the same content as data: which §N a signal points to, what tier of caller can apply the workaround, and which requirements fix the root cause. `challenges/index.json` is that data, generated from the markdown so it can never drift into a second source of truth.

Key decisions:

- **Generated, never edited.** `scripts/build_failure_index.py` parses every numbered file; CI fails when the committed JSON is stale
- **Merged numbers stay visible.** A merged stub keeps its entry with `merged_into`, so an old §N reference still resolves
- **Workaround text travels whole.** `workaround` includes the Signature, Tier, Fallback, and Limitation lines, so a consumer can quote it without reopening the file

---

## Values

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `"1.0"` | Index format version |
| `active_count` | integer | Entries with `status: "active"` |
| `failure_modes` | array | One entry per numbered file, sorted by `id` |

### ActiveFailureMode

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | §N |
| `title` | string | From the `## N. Title` heading |
| `path` | string | Repository-relative source file |
| `part` | string | Part directory |
| `status` | `"active"` | Entry carries full content |
| `severity` | `"critical"` \| `"high"` \| `"medium"` | From the metadata line |
| `frequency`, `detectability`, `token_spend`, `time`, `context` | string | Remaining metadata labels, verbatim |
| `signature` | string | Observable trigger |
| `tier` | `"A"` \| `"B"` \| `"C"` | Minimum caller capability for the workaround |
| `fallback` | string | Degraded single action; present exactly when `tier` is `C` |
| `limitation` | string | What the workaround cannot handle |
| `requirements` | string[] | `REQ-*` ids mapped to this §N in `requirements/index.md` |
| `triage_rows` | integer[] | Triage decision table rows that route here |
| `problem` | string | Markdown body of The Problem |
| `workaround` | string | Markdown body of Agent Workaround |

### MergedFailureMode

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Retired §N |
| `title` | string | Retired title |
| `path` | string | Merged stub file |
| `part` | string | Part directory |
| `status` | `"merged"` | Content lives elsewhere |
| `merged_into` | integer | Active §N that covers it |

---

## Examples

**Merged entry**
```json
{
  "id": 36,
  "title": "Pager Blocking",
  "path": "challenges/01-critical-ecosystem-runtime-agent-specific/36-critical-pager-blocking.md",
  "part": "01-critical-ecosystem-runtime-agent-specific",
  "status": "merged",
  "merged_into": 10
}
```

**Active entry (`problem` and `workaround` cut to their first line)**
```json
{
  "id": 11,
  "title": "Timeouts & Hanging Processes",
  "path": "challenges/02-critical-execution-and-reliability/11-critical-timeouts.md",
  "part": "02-critical-execution-and-reliability",
  "status": "active",
  "severity": "critical",
  "frequency": "Common",
  "detectability": "Hard",
  "token_spend": "High",
  "time": "Critical",
  "context": "Low",
  "signature": "no output or partial progress lines, then silence until killed by timeout; `exit 124` from an external `timeout` wrapper with no JSON error emitted",
  "tier": "B",
  "limitation": "If the tool buffers all output and flushes nothing before timeout, the agent receives no partial result — there is no workaround for fully-buffered tools; use a shorter timeout to fail fast and avoid wasting turn budget",
  "requirements": [
    "REQ-C-012",
    "REQ-F-011",
    "REQ-F-012",
    "REQ-F-039",
    "REQ-F-078",
    "REQ-O-012"
  ],
  "triage_rows": [
    3,
    14
  ],
  "problem": "Agents have finite time budgets per tool call. A command that runs forever (network hang, deadlock, waiting for input) burns the budget and returns nothing.",
  "workaround": "**Signature:** no output or partial progress lines, then silence until killed by timeout; `exit 124` from an external `timeout` wrapper with no JSON error emitted"
}
```

---

## Common mistakes

- **Editing `challenges/index.json` by hand.** The next generation overwrites it and CI rejects the drift; edit the markdown and regenerate
- **Treating `requirements: []` as "nothing to do".** An empty list is a coverage gap in the spec, not proof the failure mode is harmless
- **Dropping merged entries when filtering.** Keep them so historical §N references in traces and memories still resolve through `merged_into`

---

## Agent interpretation

- Look up a §N by `id`; if `status` is `merged`, follow `merged_into` once
- Match a failed call against `signature` before reading `problem`; the signature is written to be matched without knowing the cause
- Tier `A` or `B` — apply `workaround` directly; tier `C` — a weak model applies `fallback` instead
- Quote `limitation` when reporting a workaround so the caller knows what remains unhandled

---

## Coding agent notes

- Load the file once and index entries by `id`; the array is small enough to keep in memory
- Validate the file against `failure-mode-index.json` at load time and fail fast on mismatch
- Do not regex the markdown in `challenges/` at runtime; read `signature`, `tier`, `fallback`, and `limitation` from this index
- Tests: every merged entry's `merged_into` resolves to an active entry; every tier `C` entry has `fallback`

---

## Implementation notes

The generator reads requirement mappings from the failure mode column of `requirements/index.md` and triage rows from the decision table in `challenges/triage.md`. Both are the same tables humans maintain, so the index reflects exactly what the spec states. The generator fails with exit code `3` when a file lacks a parseable heading, metadata line, or workaround line, which turns silent markdown drift into a build error.
