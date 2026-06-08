# neonctl — CLI Agent Audit Report for CLI Authors

**Date:** 2026-06-06
**Version:** 2.22.2
**Scope:** Critical failure modes
**Findings:** 23

## Summary

Neon CLI has useful foundations for agents: global JSON/YAML/table output, `NEON_API_KEY`, config-dir isolation, and a strong `link --agent` state-machine workflow. The critical gaps are that these affordances are not framework-wide. Auth, init, destructive commands, common errors, and mutating operations still behave like human terminal workflows.

Failure mode score: **0.38/3** over scored Critical checks.

| Bucket | Count |
|---|---:|
| Passing (3/3) | 0 |
| Partial (1-2/3) | 7 |
| Failing (0/3) | 14 |
| Indeterminate (?/3) | 2 |

## Highest Priority Fixes

### 1. Make non-TTY auth fail fast or emit JSON fallback

Affected: §45, §64, §10.

`neonctl auth` currently starts browser OAuth and waits. In non-TTY/CI, return a JSON object with `code: "AUTH_REQUIRED"`, supported `auth_methods`, and exact next steps. Prefer API-key/env instructions over browser launch.

### 2. Apply `--agent` semantics beyond `link`

Affected: §2, §10, §50, §60.

`link --agent` is the best current pattern. Extend it to `auth`, `init`, and mutating workflows so agent invocations get a single parseable JSON object instead of prompts, spinners, and prose stderr.

### 3. Add a machine-readable manifest

Affected: §1, §23, §24, §37, §42, §43, §53, §74, §75.

Implement `neonctl --schema` or `neonctl manifest` with commands, flags, output schemas, exit codes, required scopes, danger levels, auth requirements, stdin/editor/GUI requirements, and sensitive flag metadata.

### 4. Standardize JSON envelopes and error handling

Affected: §1, §2, §11, §13, §53.

Make `--output json` apply to errors too. Use a stable envelope: `ok`, `data`, `error`, `warnings`, `meta`. Include semantic error codes and retryability information.

### 5. Make destructive operations previewable

Affected: §12, §23, §75.

Add `--dry-run` and explicit `effect` fields for create/update/delete commands. Declare `danger_level` and require explicit confirmation for irreversible deletes.

## Passing List

None.

## Indeterminate List

§61, §62.

## Observed Bugs

- Invalid explicit `--api-key` auth failures printed that credentials were being deleted from the default config path.
- `neonctl init` prompted for editor selection under `stdin=DEVNULL`.
- `neonctl auth` did not exit within the timeout under non-TTY.
- JSON mode did not apply to common auth errors.

## Recommended Implementation Order

1. Add non-TTY guards for `auth` and `init`.
2. Route all failures through JSON when `--output json` or `--agent` is active.
3. Add manifest/schema output.
4. Add dry-run/effect/idempotency support for mutating commands.
5. Add required-scope declarations and permission preflight.
