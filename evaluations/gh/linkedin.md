# LinkedIn Post — gh

<!-- Copy everything between the lines below into LinkedIn -->
---
If your agent uses `gh` today, it's flying blind.

We ran a live evaluation against the real binary — 13 Critical failure modes, every check executed. Here's what's silently breaking your agent right now:

🔴 `gh` exits 0 on every HTTP error. 401s, 404s, GraphQL failures — they all look identical to success. Your agent has no signal that anything went wrong.

🔴 When a token expires mid-session, `gh` prints "Try authenticating with: gh auth login" to stderr and exits 0. That's a browser flow your agent can't complete. It just keeps going, assuming it succeeded.

🔴 `gh issue create` with all flags provided creates a real resource immediately — no dry-run, no idempotency key. Every retry on a failed call creates a duplicate issue in your repo.

Whether you're building agents that call `gh` or running workflows that depend on it — these aren't edge cases. They're the default behavior.

2 Critical failure modes score 0/3. 7 score 1–2/3. Readiness score: 7/15.

Runtime brief, integration guide, issues report, and fix list for the gh team — all in the first comment.

@GitHub

#AIAgents #GitHub
---

<!-- First comment to post separately: -->
Full evaluation report: [PASTE LINK HERE]
