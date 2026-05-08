> **Part I: Ecosystem, Runtime & Agent-Specific** | Challenge §71

## 71. Non-Interactive Installation Absence

**Severity:** Critical | **Frequency:** Common | **Detectability:** Easy | **Token Spend:** Low | **Time:** Critical | **Context:** Low

### The Problem

Agents operating in fresh environments — CI runners, containers, sandboxes, newly provisioned VMs — must install the CLI tool before they can use it. If the installation process requires any human interaction (license acceptance prompts, configuration wizards, browser OAuth flows, interactive package manager confirmations), the agent is completely blocked before a single command can be run.

This is distinct from §45 (Headless Authentication / OAuth Browser Flow Blocking), which covers auth flows during *use*. This challenge covers the *installation step itself* — which often runs under a different user, in a different shell, with no persistent state.

```bash
# Agent attempts to install CLI in a CI container
$ pip install my-cli
Collecting my-cli
  Downloading my-cli-2.1.0.tar.gz
Do you accept the license agreement? [y/N]: _   # hangs forever
```

Common interactive patterns during installation:
1. **License prompts** — EULA or terms-of-service acceptance required before install completes
2. **Post-install configuration wizards** — tool runs a setup wizard on first install (database location, API endpoint, user name)
3. **Package manager confirmation** — `apt install` without `-y` prompts for disk space confirmation; `brew install` may prompt for sudo password or Xcode CLT installation
4. **First-run initialization** — binary installs silently but first execution triggers an interactive setup flow indistinguishable from normal use
5. **System dependency installation** — install script uses `sudo apt-get install` without `-y` or interactive `dpkg-configure`

The agent has no way to detect that install is interactive before attempting it — the process hangs or exits with an error that does not indicate what input was expected.

### Impact

- **Total blocker:** the agent cannot proceed at all — no command can be run until installation completes
- **No recovery path:** unlike most failure modes, there is no workaround that keeps the agent in control; human intervention is required
- **Silent hang:** many interactive installers wait on stdin indefinitely without printing a timeout or help message, making the failure indistinguishable from a slow download
- **Cascading failure:** in multi-step agent workflows, installation is typically step one; blocking here wastes all prior context investment
- **CI amplification:** CI runners are the most common agent environment and the least tolerant of interactive steps — a single interactive prompt fails the entire pipeline

### Solutions

**For CLI authors:**

Document a fully non-interactive install command in AGENTS.md:

```bash
# In AGENTS.md — exact non-interactive install command agents must use
## Installation
pip install my-cli==2.1.0        # exact version pin
my-cli --version                  # verify install succeeded
```

Design installation to be non-interactive by default:
- Accept license terms implicitly when `--yes` or `CI=true` is detected
- Move post-install configuration to first-use, with `--non-interactive` producing a JSON error rather than a wizard
- Use package manager flags: `pip install --yes`, `apt-get install -y`, `brew install --quiet`
- Document any system dependency with its non-interactive install command

Make installation idempotent — running the install command twice must succeed:

```bash
# Idempotent: second run must exit 0
pip install my-cli==2.1.0   # first run: installs
pip install my-cli==2.1.0   # second run: already satisfied, exit 0
```

Provide a health-check command agents can run after install to confirm the binary is functional:

```bash
my-cli --version             # exits 0, prints version string
my-cli doctor --json         # optional: structured health check
```

**For framework designers:**

Provide a `--non-interactive` flag that suppresses all post-install prompts and fails fast with a JSON error if any required configuration is absent.

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | Installation requires interactive input with no bypass; or install hangs on stdin with no documented workaround |
| 1 | Non-interactive install is possible (e.g. via undocumented `-y` flag) but not documented in AGENTS.md or README |
| 2 | Non-interactive install documented and works; but not idempotent (second run fails or prompts) |
| 3 | Non-interactive idempotent install documented in AGENTS.md; verify command documented; second run exits 0 |

**Check:** Look for a documented non-interactive install command in AGENTS.md and README. If found, run it once, confirm exit 0. Run it a second time, confirm exit 0 again (idempotency). Run the documented verify command (e.g. `--version`), confirm exit 0 and parseable version output.

### Agent Workaround

Before attempting installation, scan AGENTS.md and README for an explicit non-interactive install command. Prefer commands that include `-y`, `--yes`, `--non-interactive`, `DEBIAN_FRONTEND=noninteractive`, or equivalent flags.

Set these environment variables before running any install command:

```
CI=true
DEBIAN_FRONTEND=noninteractive
PIP_NO_INPUT=1
NPM_CONFIG_YES=true
```

If installation hangs, send EOF to stdin (`Ctrl-D` equivalent) and observe the exit code. If it exits non-zero, report the exact install command and exit code to the user — do not retry interactively.

If no non-interactive install path exists, halt and report: the CLI cannot be installed in an agent environment without human intervention. Do not attempt workarounds that require reading stdin.

**Limitation:** If the installer has no non-interactive mode at all, no workaround exists — agent must escalate to a human operator to perform the installation step.
