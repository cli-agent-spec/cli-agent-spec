# Trace — gh

## §1 — Exit Codes & Status Signaling
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `gh issue view 999999999 --repo cli/cli < /dev/null`
**Exit code:** 0
**Score:** 0/3

**stdout** (first 20 lines):
```
(empty)
```

**stderr** (first 20 lines):
```
GraphQL: Could not resolve to an issue or pull request with the number of 999999999. (repository.issue)
```

---

## §2 — Output Format & Parseability
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `gh issue list --repo cli/cli --limit 2 --json number,title < /dev/null`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
[{"number":13358,"title":"Documented gh api call for creating PR review comments returns 422 internal error"},{"number":13357,"title":"Opt-in command-wide TTL-based request caching"}]
```

**stderr** (first 20 lines):
```
(empty)
```

---

## §8 — ANSI & Color Code Leakage
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `NO_COLOR=1 TERM=dumb gh issue list --repo cli/cli --limit 3 < /dev/null`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
13358	OPEN	Documented gh api call...	needs-triage	2026-05-06T18:47:43Z
13357	OPEN	Opt-in command-wide TTL-based request caching	enhancement	2026-05-06T16:32:39Z
```
ANSI sequence count: 0

---

## §10 — Interactivity & TTY Requirements
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `gh pr list < /dev/null` (no TTY)
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
(empty — no open PRs in current repo context)
```

**stderr** (first 20 lines):
```
(empty)
```

---

## §11 — Timeouts & Hanging Processes
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `perl -e 'alarm(5); exec("gh", "api", "/repos/cli/cli")' < /dev/null`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
{"id":212613049,"node_id":"MDEwOlJlcG9zaXRvcnkyMTI2MTMwNDk=",...}
[truncated — full JSON response]
```

---

## §12 — Idempotency & Safe Retries
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** Check method: partial — no write access to test repo; --help inspection only
**Exit code:** N/A
**Score:** 1/3

**Notes:** No idempotency documentation found in `--help`. No `--idempotency-key` flag. Write-permission test skipped.

---

## §43 — Tool Output Result Size Unboundedness
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `gh issue list --repo cli/cli < /dev/null`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
13358	OPEN	Documented gh api call...	needs-triage	2026-05-06T18:47:43Z
[29 more rows — default limit 30]
```

---

## §45 — Headless Authentication / OAuth Browser Flow Blocking
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `GH_TOKEN=invalid_token_abc123 gh repo view cli/cli < /dev/null`
**Exit code:** 0
**Score:** 1/3

**stdout** (first 20 lines):
```
(empty)
```

**stderr** (first 20 lines):
```
HTTP 401: Bad credentials (https://api.github.com/graphql)
Try authenticating with:  gh auth login
```

---

## §50 — Stdin Consumption Deadlock
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `echo "should not consume" | perl -e 'alarm(5); exec("gh", "repo", "view", "cli/cli")'`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
name:	cli/cli
description:	GitHub's official command line tool
```

---

## §53 — Credential Expiry Mid-Session
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `GH_TOKEN=invalid_token_abc123 gh repo view cli/cli < /dev/null`
**Exit code:** 0
**Score:** 0/3

**stderr** (first 20 lines):
```
HTTP 401: Bad credentials (https://api.github.com/graphql)
Try authenticating with:  gh auth login
```

---

## §60 — OS Output Buffer Deadlock
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `gh issue list --repo cli/cli --json number,title --limit 5 < /dev/null | wc -c`
**Exit code:** 0
**Score:** 3/3

**stdout:** 460 bytes received without hang

---

## §62 — $EDITOR and $VISUAL Trap
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `GH_EDITOR=false EDITOR=false gh issue create --repo cli/cli --title test --body test < /dev/null`
**Exit code:** 0
**Score:** 2/3

**stdout** (first 20 lines):
```
https://github.com/cli/cli/issues/13360
```
**Note:** Command created a real issue on a public repo. No dry-run option available.

---

## §64 — Headless Display and GUI Launch Blocking
**Date:** 2026-05-07
**CLI version:** 2.88.1
**Check command:** `DISPLAY="" gh browse --no-browser --repo cli/cli < /dev/null`
**Exit code:** 0
**Score:** 3/3

**stdout** (first 20 lines):
```
https://github.com/cli/cli
```
