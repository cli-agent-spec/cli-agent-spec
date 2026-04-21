# Guide: Unix Naming Conventions for Agent-Facing CLIs

> **The principle:** Inherit Unix vocabulary and semantics. Replace Unix output format, exit code precision, interactivity, and glob contracts with agent-safe equivalents.

LLMs are trained on billions of shell sessions, man pages, scripts, and CLI documentation. That training encodes behavioral expectations into short names and flag patterns — a compressed semantic layer a CLI developer can exploit deliberately. This guide documents which Unix conventions to preserve, which to override, and how to align with the training corpora that give agents the strongest priors.

---

## The Inherit/Override Split

### Inherit — these activate correct agent priors

| Convention | Why it works |
|-----------|-------------|
| Unix verb vocabulary | `list`, `get`, `apply`, `exec`, `diff`, `watch` carry pre-trained behavioral expectations |
| Verb-noun subcommand grammar | `tool resource create` mirrors `git commit`, `kubectl get pods`; agent infers side-effect profile from the verb |
| Long-form flag names | `--dry-run`, `--force`, `--recursive`, `--verbose`, `--output` are near-universal; agents predict them correctly |
| `--format json` | Trained from `aws --output json`, `kubectl -o json`, `gh --json`; agents add it automatically for machine-readable output |
| `--dry-run` / `--apply` two-phase | Trained from rsync, ansible, terraform; agents use `--dry-run` before mutating unprompted |
| Man page document structure | SYNOPSIS / OPTIONS / EXAMPLES / EXIT STATUS; agents parse this with high fidelity |
| Exit codes 0 / 1 / 2 | 0=success, 1=error, 2=bad arguments — deeply trained across the entire Unix corpus |

### Override — these break agent workflows

| Convention | Why it fails | Spec coverage |
|-----------|-------------|---------------|
| Short cryptic flags `-f -r -n` | Same letter means different things across tools; drives hallucination | §35 |
| Positional arguments | Order-sensitive, no schema representation | §69 |
| Silent success (no output) | Agents need structured confirmation | §2 |
| Non-error non-zero exits | `grep` exit 1 = no match, not error; corrupts retry logic | §1 |
| Shell glob expansion | Bypassed when agent invokes via subprocess | §51 |
| Locale-dependent output | Breaks deterministic parsing across environments | §57 |
| Interactive prompts | Blocks indefinitely when stdin is not a TTY | §10 |
| Mixed stderr / stdout | No stable signal/noise boundary | §3 |

---

## Command Naming

### Use Unix verb analogues

Agents have pre-trained priors about what each verb implies:

| Verb | Implied semantics | Side-effect profile |
|------|-------------------|---------------------|
| `get` / `show` | Return one resource | Read-only, retry-safe |
| `list` | Return collection | Read-only, retry-safe |
| `create` | Create new resource | Has side effects, not idempotent |
| `apply` | Create-or-update | Idempotent, retry-safe |
| `update` / `set` | Modify existing | Has side effects |
| `delete` / `remove` | Destroy resource | Destructive, wants `--dry-run` |
| `describe` / `inspect` | Full resource detail | Read-only, more than `get` |
| `validate` / `check` | Verify without executing | Read-only, pre-flight |
| `diff` | Show what would change | Read-only, preview |
| `exec` | Run command in context | Context-dependent |
| `logs` | Stream event history | Read-only, streaming |
| `watch` | Stream state changes | Read-only, open-ended |
| `init` | One-time bootstrap | Has side effects, idempotent |
| `status` | Current state | Read-only |

### Support verb synonyms

Agents guess synonyms. Supporting them costs one alias per command:

| Canonical | Synonyms |
|-----------|----------|
| `delete` | `remove`, `rm` |
| `list` | `ls` |
| `create` | `add`, `new` |
| `apply` | `sync`, `reconcile` |
| `update` | `set`, `edit` |

### Use `up` / `down` for multi-component systems

Trained from docker-compose, vagrant, terraform. `up` = bring described state into existence (dependency-ordered). `down` = tear everything down cleanly. These imply completeness and ordering that `start`/`stop` do not.

### Use `start` / `stop` / `restart` / `reload` / `status` for daemons

Trained from systemctl, supervisorctl, pm2. Agents managing persistent processes know this five-verb lifecycle cold.

---

## Flag Conventions

### Flags worth inheriting exactly

| Flag | Convention | Trained from |
|------|-----------|--------------|
| `--dry-run` / `-n` | Preview without side effects | rsync, make, ansible |
| `--format json` | Machine-readable output | aws, kubectl, gh |
| `--output` / `-o` | Output destination or format | many |
| `--verbose` / `-v` | More output; stack for levels | ssh, curl, ansible |
| `--quiet` / `-q` | Less output | apt, many |
| `--force` / `-f` | Skip confirmation | rm, git |
| `--all` / `-a` | Include all items | ls, git, docker |
| `--recursive` / `-r` | Traverse depth | cp, rsync, grep |
| `--no-*` negation | `--no-color`, `--no-pager` | git, many |
| `--timeout` with suffixes | `30s`, `5m`, `1h` | curl, kubectl |
| `--since` / `--until` | Time-bounded queries | journalctl, git log |
| `--follow` / `-f` | Live-stream | tail, kubectl logs |
| `--watch` | Stream updates | kubectl, webpack |
| `--label` / `-l` | Filter by metadata | kubectl |
| `--namespace` / `-n` | Scope isolation | kubectl |
| `--output-file` | Write to file instead of stdout | many |
| `--color=auto\|always\|never` | Three-value color control | ls, grep, git |
| `-` for stdin | Pipe input as file argument | cat, diff, jq |
| `--` end-of-flags | Protect downstream args | all shells |

### Flags with well-trained interaction protocols

| Flag / Pattern | Protocol | Trained from |
|---------------|----------|-------------|
| `--dry-run` → `--apply` | Preview then commit | terraform, ansible, rsync |
| `--wait` / `--no-wait` | Sync vs async invocation | kubectl, az |
| `--for=condition` | Bounded waiting | kubectl wait |
| `--var` / `--var-file` | Variable injection | terraform, ansible |
| `--set key=value` | Inline config override | helm |
| `--tags` / `--skip-tags` | Selective execution | ansible, pytest |
| `--on-error fail\|continue\|rollback` | Error strategy | make, helm |
| `--generate-skeleton` + `--input-file` | Complex input template | aws cli |
| `--from-file` / `--from-literal` | Multiple input sources | kubectl |
| `--idempotency-key` | Safe retry deduplication | aws sdk, stripe |
| `--jq <expr>` | Embedded output filter | jq (embedded) |
| `--porcelain` | Stable, versioned output | git |

---

## Output Conventions

### Formats in preference order for agent pipelines

| Format | When to use | Notes |
|--------|------------|-------|
| JSON (`--format json`) | Default for agent consumption | Use `response-envelope` schema |
| JSONL | Streaming / `--follow` output | One object per line, independently parseable |
| TSV | Tabular data without JSON | No quoting rules; safe for `cut`, `awk` |
| `KEY=VALUE` per line | Config/state output | Parseable without libraries |
| One item per line | ID lists, bulk piping | Safe for `xargs`, shell loops |

### Output invariants

- **One-item-per-line for lists** enables `xargs -0` composition
- **`---` document separator** for multi-result YAML/text streams
- **`--no-headers`** for tabular output — agents add this before piping to `awk`
- **Zero results → empty structure**, not silence (`[]`, `{}`, `{"count": 0}`)
- **Verb output contracts:** `create` returns ID, `get` returns full resource, `list` returns array, `delete` returns confirmation

---

## Training Corpus Alignment

The most important design decision: **which corpus does your tool most resemble?** Match that corpus's conventions to activate the densest available prior.

| Tool type | Model after | Key patterns to inherit |
|-----------|------------|------------------------|
| Cloud resource manager | kubectl | `-n namespace`, `-l selector`, `-o json`, `apply`, `wait --for`, `describe` |
| HTTP / API client | curl | `-X METHOD`, `-H header`, `-d data`, `--fail`, `--retry`, `--silent` |
| Infrastructure provisioner | terraform | `plan` / `apply` / `destroy`, `--var`, `--plan-file`, workspaces |
| Configuration manager | ansible | `--tags`, `--limit`, `--check`, `--diff`, `--extra-vars` |
| Package / dependency manager | npm / pip | `install`, `uninstall`, `upgrade`, `outdated`, `--frozen-lockfile` |
| Deployment orchestrator | helm | `--set`, `--values`, `--atomic`, `--dry-run`, `--wait` |
| Container / process manager | docker | `exec`, `logs --follow`, `-e KEY=VALUE`, `--rm`, `run` |
| Multi-service orchestrator | docker-compose | `up -d`, `down -v`, `logs -f`, `scale` |
| Version control wrapper | git | `--porcelain`, ref syntax (`HEAD~N`), `--patch`, `--stat` |
| Project build system | make | `install`, `test`, `clean`, `build` as subcommand names |
| Data query / transform | jq | `--jq` flag accepting jq expressions; `-r` for raw output |

### Mixed-corpus tools

A tool that manages versioned cloud resources should look like **kubectl + terraform**: kubectl's resource vocabulary (`get`, `apply`, `describe`, `-l selector`) combined with terraform's lifecycle (`plan`, `apply`, `--var`). Pick the dominant corpus for the primary interface and borrow selectively from secondary ones.

---

## Environment Variables

### Universal conventions (read without prefix)

| Variable | Convention |
|----------|-----------|
| `NO_COLOR` | Disable ANSI output |
| `CI` | Headless mode: suppress prompts, spinners, color, telemetry |
| `HOME` | User home directory |
| `XDG_CONFIG_HOME` / `XDG_DATA_HOME` / `XDG_CACHE_HOME` | Config/data/cache locations |
| `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` | Network proxy |
| `PAGER` | Pager program (set to `cat` for non-interactive) |
| `EDITOR` / `VISUAL` | Editor (must be no-op in non-TTY; see §62) |

### Tool-specific variables (always use `TOOLNAME_` prefix)

See REQ-F-073. All tool-specific env vars must be namespaced to prevent cross-tool contamination in multi-tool agent pipelines.

---

## The Three Design Layers

A fully agent-compatible CLI operates at three levels:

```
┌─────────────────────────────────────────────────┐
│  Layer 3: Runtime Self-Documentation             │
│  --explain, --help --format json, __complete,   │
│  deprecation warnings, next_steps in errors,    │
│  tool capabilities, --generate-skeleton          │
│  → Reduces epistemic load at runtime            │
├─────────────────────────────────────────────────┤
│  Layer 2: Mechanics (enforced by requirements)  │
│  Structured output, precise exit codes,         │
│  isatty detection, signal handling,             │
│  atomic writes, fd cleanup, LF endings          │
│  → Makes behavior predictable                   │
├─────────────────────────────────────────────────┤
│  Layer 1: Naming (this guide)                   │
│  Unix vocabulary, verb-noun grammar,            │
│  flag conventions, corpus alignment             │
│  → Activates correct pre-trained priors         │
└─────────────────────────────────────────────────┘
```

Layer 1 is free — it costs nothing to name a command `apply` instead of `upsert`. Layers 2 and 3 require implementation effort but are covered by the spec's requirements. A tool that invests in all three layers achieves correct agent behavior on the first invocation, without documentation, across the full range of agent tasks.

---

## Related

| Document | Relationship |
|----------|-------------|
| [challenges/index.md](../challenges/index.md) | Provides: failure modes that arise when Unix mechanics are inherited without override |
| [requirements/index.md](../requirements/index.md) | Provides: implementation contracts for Layer 2 (mechanics) |
| [schemas/manifest-response.md](../schemas/manifest-response.md) | Provides: manifest schema that supports Layer 3 runtime self-documentation |
