> **Part IV: Security** | Challenge §74

## 74. Credential Scope Declaration Absence

**Severity:** Critical | **Frequency:** Common | **Detectability:** Hard | **Token Spend:** Low | **Time:** Medium | **Context:** Low

### The Problem

CLI tools that authenticate with external services accept whatever credential the caller provides without declaring what permissions each command actually requires. Agents typically inherit the user's full personal credential — giving every invocation a blast radius equal to the entire account.

**Full-access token used for a read-only workflow:**
```bash
$ export GH_TOKEN=ghp_xxxxxxxxxxxxxxxx   # personal token: full repo + admin access
$ gh issue list --repo my-org/my-repo    # only needs repo:read
# Agent now holds keys to every repo, org setting, and team in the account
```

**Agent hallucinates a destructive command — nothing restricts it:**
```bash
$ gh repo delete my-org/my-repo         # requires delete_repo scope
# Succeeds because the token has it — never needed for this workflow
```

**No machine-readable scope declaration — agent cannot check:**
```bash
$ gh issue list --schema
# No output: gh has no --schema flag
# Agent has no way to discover required_scopes before choosing a credential
```

**Over-privileged credential leaks through error messages:**
```bash
$ gh api /orgs/my-org/teams
Error: GET /orgs/my-org/teams: 403 Resource not accessible by personal access token
# Error reveals the token is a PAT and hints at org-level access attempts
# Agent may retry with escalated scopes rather than failing safely
```

### Impact

- Agent operating with full personal credentials can permanently delete repositories, revoke tokens, or modify org-wide settings — without any declared boundary
- Compromised or hallucinating agent session has maximum account blast radius
- Agent cannot select or validate a minimally-scoped credential before starting a workflow
- No pre-flight check exists to verify that the credential is sufficient but not excessive
- Audit logs show the user's identity, not the agent session — no separation of blast radius from the person

### Solutions

**Declare `required_scopes` per command in `--schema` output:**
```json
{
  "command": "issue list",
  "danger_level": "safe",
  "required_scopes": ["repo:read"],
  "flags": { "repo": { "type": "string", "required": true } }
}
```

**Provide a `check-permissions` pre-flight command:**
```bash
$ tool check-permissions --for issue:list
{
  "ok": true,
  "required_scopes": ["repo:read"],
  "active_scopes": ["repo:read", "repo:write"],
  "over_privileged": true,
  "warnings": ["Active credential has scopes beyond what this command needs"]
}
```

**Warn in `warnings[]` when active credential exceeds declared scopes:**
```json
{
  "ok": true,
  "data": { ... },
  "warnings": [
    "Credential has write access; this command only requires read — consider a scoped token"
  ]
}
```

**Document minimal credential recipes in AGENTS.md:**
```markdown
## Minimal credentials by workflow

| Workflow | Required scopes | How to create |
|----------|----------------|---------------|
| Read issues and PRs | `repo:read` | Fine-grained PAT → Contents: Read |
| Comment on issues | `repo:read`, `issues:write` | Fine-grained PAT → Issues: Read+Write |
| Never needed by agents | `delete_repo`, `admin:org` | Do not grant |
```

**For framework design:**
- Commands declare `required_scopes: []` at registration; framework enforces that the field is present
- Framework compares `required_scopes` against the credential's active scopes at invocation and emits structured warnings on over-privilege
- `check-permissions` is a built-in command that accepts `--for <command>` and returns a machine-readable scope report
- Credentials with `admin` or `owner`-level scopes trigger an unconditional warning when used in agent sessions

### Evaluation

| Score | Condition |
|-------|-----------|
| 0 | No scope declaration anywhere; commands accept any credential silently; no documentation on minimal credentials for agent use |
| 1 | AGENTS.md or equivalent lists which scopes each command group needs (human-readable text only); no machine-readable declaration |
| 2 | `required_scopes` field present in `--schema` or manifest output for each command; documentation covers how to create minimally-scoped credentials |
| 3 | Framework warns (via `warnings[]`) when active credential has scopes beyond `required_scopes`; `check-permissions` pre-flight returns machine-readable scope report; over-privileged credentials are flagged at startup |

**Check:** Run `tool --schema` (or equivalent manifest command) — verify every command entry includes a `required_scopes` field. Then run `tool check-permissions --for <some-command>` — verify it returns `required_scopes`, `active_scopes`, and `over_privileged` fields.

---

### Agent Workaround

**Create a minimally-scoped credential before starting any agentic workflow:**

```python
# Principle: request only the permissions the workflow actually needs.
# For GitHub: fine-grained PAT scoped to specific repos and operations.
# For AWS: an IAM role with a policy limited to the required actions/resources.
# For GCP: a service account with only the IAM roles the workflow calls.

env = {
    **os.environ,
    "GH_TOKEN": fine_grained_pat,     # scoped to repo:read + issues:write only
}
result = subprocess.run(["gh", "issue", "list", "--repo", repo], env=env, ...)
```

**Scan the manifest or help text for scope hints before authenticating:**
```python
help_text = subprocess.run(["gh", "issue", "list", "--help"],
                           capture_output=True, text=True).stdout

# Look for scope hints in help or README
scope_hints = re.findall(r'scope[s]?[:\s]+([a-z:_,\s]+)', help_text, re.IGNORECASE)
# Treat absence of any hint as unknown — default to maximally restricted credential
```

**Treat absence of scope declaration as maximum blast radius:**
```python
COMMANDS_KNOWN_DESTRUCTIVE_SCOPES = {
    "gh repo delete":    ["delete_repo"],
    "gh org remove-member": ["admin:org"],
}

def credential_needed(command: str) -> list[str]:
    for prefix, scopes in COMMANDS_KNOWN_DESTRUCTIVE_SCOPES.items():
        if command.startswith(prefix):
            return scopes
    return []  # unknown — use most-restricted credential available
```

**Limitation:** If the tool declares no `required_scopes`, the agent cannot determine minimal credential needs from the CLI itself — consult external API documentation for the service and manually construct a credential scope list before starting the workflow; do not reuse personal or admin tokens for agentic sessions
