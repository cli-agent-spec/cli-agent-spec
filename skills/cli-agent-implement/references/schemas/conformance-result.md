# Schema: ConformanceResult

**File:** [`conformance-result.json`](conformance-result.json)

> **Used by:** [`conformance/run.py`](../conformance/README.md) · `cli-agent-evaluate-batch` skill
> Returned as the `data` field of a [`ResponseEnvelope`](response-envelope.md).

---

## Purpose

The result of running the conformance kit: one verdict per check, one verdict per conformance level, and evidence precise enough to reproduce each failure. The kit wraps it in a `ResponseEnvelope` and exits `0` or `4`, so the tool that checks the spec follows the spec.

Key decisions:

- **Evidence is argv, not prose.** Every failure records the exact argv, stdin mode, exit code, timing, and a one-line reason
- **Levels summarize only what was checked.** A skipped check makes a level `incomplete`, never `pass`
- **Checks carry their traceability.** Each check lists the §N it detects and the requirements it verifies

---

## Values

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `"1.0"` | Result format version |
| `tool` | string | Tool name from the profile |
| `levels` | object | `level_1`, `level_2`, `level_3`: `pass` \| `fail` \| `incomplete` |
| `summary` | object | `passed`, `failed`, `skipped` counts |
| `checks` | `Check[]` | One entry per reported check |

### Check

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier such as `json_envelope` |
| `title` | string | What the check verifies |
| `status` | `"pass"` \| `"fail"` \| `"skip"` | Outcome |
| `level` | `1` \| `2` \| `3` | Lowest level that requires the check |
| `failure_modes` | string[] | `§N` the check detects |
| `requirements` | string[] | `REQ-*` the check verifies |
| `runs_checked` | integer | Probe runs evaluated |
| `failures` | `Evidence[]` | Failing runs |
| `skipped_reason` | string | Present only when skipped |

### Evidence

| Field | Type | Description |
|-------|------|-------------|
| `probe` | string | Probe name |
| `argv` | string[] | Exact argv |
| `stdin` | `"closed"` \| `"open"` | `/dev/null` or a silent open pipe |
| `exit_code` | integer \| null | `null` when killed |
| `timed_out` | boolean | Exceeded the profile timeout |
| `duration_ms` | integer | Run time |
| `detail` | string | Why the run failed |

---

## Examples

**Failing check with evidence**
```json
{
  "schema_version": "1.0",
  "tool": "democli (non-compliant mock)",
  "levels": { "level_1": "fail", "level_2": "fail", "level_3": "fail" },
  "summary": { "passed": 0, "failed": 1, "skipped": 0 },
  "checks": [
    {
      "id": "stdout_no_ansi",
      "title": "No ANSI escape sequences on stdout in a non-TTY",
      "status": "fail",
      "level": 1,
      "failure_modes": ["§8"],
      "requirements": ["REQ-F-007"],
      "runs_checked": 5,
      "failures": [
        {
          "probe": "list deployments",
          "argv": ["/repo/benchmark/harness/cli/bad/democli", "deployments", "list"],
          "stdin": "closed",
          "exit_code": 0,
          "timed_out": false,
          "duration_ms": 14,
          "detail": "stdout contains ANSI escape sequences"
        }
      ]
    }
  ]
}
```

**Invalid — passing check that still lists failures**
```json
{
  "schema_version": "1.0",
  "tool": "democli",
  "levels": { "level_1": "pass", "level_2": "pass", "level_3": "pass" },
  "summary": { "passed": 1, "failed": 0, "skipped": 0 },
  "checks": [
    { "id": "json_envelope", "title": "Envelope", "status": "passed", "level": 1, "failure_modes": [], "requirements": [], "runs_checked": 1, "failures": [] }
  ]
}
```
Violation: `status` must be `pass`, `fail`, or `skip`.

---

## Common mistakes

- **Reading `levels.level_1: "pass"` as full Level 1 conformance.** The kit covers the mechanically checkable subset; judgment-based requirements still need review
- **Ignoring `incomplete`.** A skipped check means the profile lacked a probe kind; add the probe rather than treating the level as met
- **Parsing `detail` to classify failures.** Branch on `id`; `detail` is for humans

---

## Agent interpretation

- Exit `4` with `error.code: "CONFORMANCE_CHECKS_FAILED"` — iterate `data.checks` where `status` is `fail`; each `failures[].argv` reproduces the problem verbatim
- `skipped_reason` present — extend the profile with the missing probe kind, then rerun
- Map failing checks to fixes through `requirements`; the requirement files carry acceptance criteria and wire formats

---

## Coding agent notes

- Treat `levels` as derived: recompute from `checks` in tests to catch aggregation bugs
- Store results per commit to track conformance regressions; `argv` paths are absolute, so normalize them before diffing
- Tests: a result with any failing level-1 check has `level_1: "fail"`; a result with only skips has `incomplete`

---

## Implementation notes

Level verdicts nest: `level_2` considers checks at levels 1 and 2, and `level_3` considers all checks. Runtime evidence is capped to failing runs, which keeps the output bounded (§43) even for profiles with many probes.
