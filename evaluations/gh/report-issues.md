# Issues Report — gh

**Generated:** 2026-05-07
**CLI version:** 2.88.1
**Scope:** Critical failure modes
**Findings in scope:** 13 failure modes

---

## Observed Bugs  _(from evaluation notes)_

### §1 candidate — HTTP error responses exit 0

**Discovered during:** §1 and §53 evaluation — 2026-05-07
**Symptom:** `gh issue view 999999999`, `GH_TOKEN=invalid gh repo view`, and HTTP 404 responses all exit 0 despite being errors
**Impact:** Agent cannot branch on exit code to detect failures — must parse stderr prose for error detection
**Trigger:** Any command that produces an HTTP 4xx response

### §62 candidate — `gh issue create` creates live resources during checks

**Discovered during:** §62 evaluation — 2026-05-07
**Symptom:** `gh issue create --title X --body Y` immediately creates a permanent resource with no confirmation and no dry-run option; prints only the URL
**Impact:** Agent testing invocation patterns will create real issues, PRs, or gists in production repos
**Trigger:** `gh issue create`, `gh pr create`, `gh gist create` with all required flags supplied

### §45/§53 candidate — Auth failure not machine-readable

**Discovered during:** §45 and §53 evaluation — 2026-05-07
**Symptom:** Invalid token produces `HTTP 401: Bad credentials` on stderr and exits 0; suggested fix is `gh auth login` (interactive-only)
**Impact:** Agent cannot distinguish auth failure from network error or permissions error; cannot self-remediate
**Trigger:** Any command run with an expired or invalid `GH_TOKEN`

---

## Failure-Mode Gaps  _(score < 3, sorted: score asc, severity desc)_

### §1 — Exit Codes & Status Signaling  [Critical · score 0/3]

**What fails:** Error responses (HTTP 4xx, resource not found, GraphQL errors) all exit 0 — agent cannot detect failure without parsing stderr
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (must parse stderr; fragile)

### §53 — Credential Expiry Mid-Session  [Critical · score 0/3]

**What fails:** Expired or invalid token produces a human-readable stderr message and exits 0 — agent has no machine-readable signal that re-auth is needed and no non-interactive re-auth path
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** Partial (grep stderr for "401" or "Bad credentials")

### §12 — Idempotency & Safe Retries  [Critical · score 1/3]

**What fails:** No idempotency guarantees or keys on mutating commands — retrying a failed `gh issue create` may create duplicate issues
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: High
**Workaround exists:** No

### §45 — Headless Authentication / OAuth Browser Flow Blocking  [Critical · score 1/3]

**What fails:** Invalid/expired token error is not machine-readable (plain text stderr, exit 0); suggested recovery (`gh auth login`) requires a browser
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Partial (pre-set `GH_TOKEN`; grep stderr for auth error patterns)

### §2 — Output Format & Parseability  [Critical · score 2/3]

**What fails:** `--json` works but is not auto-activated in non-TTY; no response envelope (`ok`/`error`/`meta`); field list must be specified manually per command
**Frequency:** Very Common
**Token/time cost when it triggers:** Token Spend: High · Time: Medium
**Workaround exists:** Yes (always pass `--json <fields>` explicitly)

### §10 — Interactivity & TTY Requirements  [Critical · score 2/3]

**What fails:** No `--non-interactive` flag; interactive suppression requires env vars (`GH_PROMPT_DISABLED=1`, `GH_PAGER=cat`) that are not prominently documented for agents
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes (set env vars; see runtime brief)

### §11 — Timeouts & Hanging Processes  [Critical · score 2/3]

**What fails:** No built-in timeout flag; long API operations can hang indefinitely; no structured timeout exit code
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes (wrap with `perl -e 'alarm(N); exec(...)'` on macOS)

### §43 — Tool Output Result Size Unboundedness  [Critical · score 2/3]

**What fails:** Default limit is 30 items (good), but no JSON pagination metadata — agent cannot detect whether results were truncated without knowing the default limit
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: Critical · Time: High
**Workaround exists:** Partial (always pass `--limit N` explicitly)

### §62 — $EDITOR and $VISUAL Trap  [Critical · score 2/3]

**What fails:** Commands that open an editor (e.g. `gh issue create` without `--body`) will invoke `$EDITOR` and block; bypass requires supplying all content flags — not documented for agent use
**Frequency:** Common
**Token/time cost when it triggers:** Token Spend: High · Time: Critical
**Workaround exists:** Yes (always pass `--title` and `--body`; set `GH_EDITOR=/bin/false`)

---

## Passing  _(score 3/3 — safe to use without special handling)_

§8 ANSI & Color Code Leakage, §50 Stdin Consumption Deadlock, §60 OS Output Buffer Deadlock, §64 Headless Display and GUI Launch Blocking

---

## Risk Summary

| Category | Count | §N list |
|---|---|---|
| Observed bugs | 3 | §1, §53, §62 |
| Score 0 — complete failure | 2 | §1, §53 |
| Score 1 — major gap | 2 | §12, §45 |
| Score 2 — minor gap | 5 | §2, §10, §11, §43, §62 |
| Score 3 — passing | 4 | §8, §50, §60, §64 |

**Highest-risk combination:** §1 (exit 0 on all errors) combined with §53 (auth failure exits 0) means an agent has no reliable signal that any command failed — it must parse stderr prose for every invocation.
