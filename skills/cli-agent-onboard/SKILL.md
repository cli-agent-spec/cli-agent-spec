---
name: cli-agent-onboard
description: Onboard a CLI tool for agent evaluation — reads agent docs, detects OS, runtime, toolchain, and binary, discovers non-interactive flags and config. Saves the result as evaluations/<cli-name>/environment.md for reuse by cli-agent-evaluate and other skills. Run once per CLI before starting evaluations.
license: MIT
compatibility: Requires access to the CLI being onboarded. Works on macOS, Linux, and Windows.
---

# CLI Onboard — Environment Profile

Build and save a reusable environment profile for a CLI tool.

## Inputs

- **CLI** — the CLI tool to profile: a command name (e.g. `gh`), a binary path, or enough context to locate it in the current working directory
- **`--force`** _(optional)_ — skip the confirmation prompt in Step 0 and overwrite any existing profile without asking. Used by `cli-agent-audit` when `--refresh` is set.

## Local Memory Artifact

This skill produces one local artifact:

| File | Content |
|---|---|
| `evaluations/<cli-name>/environment.md` | OS, runtime, binary, version, non-interactive flags, config env vars |

See **Step 0** for handling an existing profile.

---

## Step 0 — Check for existing profile

Before doing anything else: check whether `evaluations/<cli-name>/environment.md` already exists.

- **If it exists and `--force` is set:** proceed directly to Step 1 and overwrite on Step 6 — no prompt.
- **If it exists and `--force` is not set:** display its contents, then ask the user: "A profile already exists for `<cli-name>`. Refresh it? (yes/no)". If no: skip Steps 1–6 — the existing profile is ready to use as-is by the calling skill. If yes: proceed to Step 1 and overwrite on Step 6.
- **If it does not exist:** proceed directly to Step 1.

---

## Step 1 — Read agent-facing docs

Check for these files in the current working directory and read any that exist:

1. `AGENTS.md` — canonical invocation, env vars, non-interactive flags, input conventions
2. `CODING_AGENTS.md` — runtime constraints, package manager, language version
3. `README.md` — fallback for binary name and install instructions

---

## Step 2 — Detect runtime and toolchain

Identify the project type from manifest files in CWD:

| Manifest | Runtime | Preferred runner |
|---|---|---|
| `pyproject.toml` / `setup.py` | Python | Check for `uv`, `poetry`, `pip`; read `[project.scripts]` for entry point name |
| `package.json` | Node | Check for `pnpm`, `yarn`, `npm`; read `bin` field |
| `Cargo.toml` | Rust | Look for compiled binary in `target/release/` |
| `go.mod` | Go | `go run .` or compiled binary |
| None of the above | Unknown | Try the CLI name directly on PATH |

---

## Step 3 — Locate the binary

Resolve the actual invocable command in this order:

1. Entry point from manifest (`[project.scripts]` / `bin`)
2. Scripts in `.venv/bin/`, `node_modules/.bin/`, `target/release/`
3. PATH lookup
4. Preferred runner prefix (e.g. `uv run <entry>`, `npx <entry>`)

Verify with `<resolved-command> --version` or `<resolved-command> --help`.

If no manifest is found AND the CLI name is not on PATH: ask the user for the binary location or install command. Do not proceed with an incomplete runtime — the profile requires a verified binary path.

---

## Step 4 — Detect OS constraints

| OS | Constraint | Implication |
|---|---|---|
| macOS | No GNU `timeout` / `gtimeout` | Use `subprocess.run(..., timeout=N)` in Python, or `perl -e 'alarm(N); exec(...)'` |
| macOS | `python` not on PATH (Xcode stub) | Use `python3` or venv-qualified path |
| Linux | GNU coreutils present | `timeout N <cmd>` works |
| Windows | Different shell semantics | Use PowerShell `Start-Process` with `-Wait` and timeout |

---

## Step 5 — Discover non-interactive flags and config

Run `<resolved-command> --help` and scan for:

- Flags that suppress prompts: `--yes`, `--no`, `--non-interactive`, `--force`, `--defaults`, `--answers`
- Flags that control output format: `--format`, `--json`, `--output`
- Flags that set input data: `--json`, `--input`, `--data`
- Environment variables used for config (look in `AGENTS.md` first, then `--help` output)

---

## Step 6 — Save the profile

Create `evaluations/<cli-name>/` if it does not exist. Save as `evaluations/<cli-name>/environment.md`:

```markdown
# Environment Profile — <cli-name>

**Generated:** <ISO date>
**CWD:** <absolute path>

## OS
- Platform: <darwin | linux | win32>
- Version: <uname -r or equivalent>

## Runtime
- Language: <Python | Node | Go | Rust | ...>
- Version: <x.y.z>
- Toolchain: <uv | poetry | npm | pnpm | cargo | ...>

## Binary
- Entry point: <exact command to invoke, e.g. `uv run bean`>
- Version: <output of --version>
- Resolved path: <absolute path if known>

## Non-Interactive Flags
- <flag>: <what it does>

## Output Format Flags
- <flag>: <what it does>

## Config
- <env var>: <purpose>

## Timeout Method
- <`subprocess.run(timeout=N)` | `timeout N` | `perl -e 'alarm(N); exec(...)'`>

## Source
- <which docs were read: AGENTS.md, CODING_AGENTS.md, README.md, pyproject.toml, ...>
```

---

## Rules

- Create `evaluations/<cli-name>/` if it does not exist before saving the profile
- Do not overwrite an existing `evaluations/<cli-name>/environment.md` without user confirmation, unless `--force` is passed
- Record only values actually discovered — no placeholders or guesses
- If a doc file (AGENTS.md, etc.) contradicts what `--help` shows, note the discrepancy in Source
