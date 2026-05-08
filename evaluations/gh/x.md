# X Thread — gh

<!-- Post each numbered block separately, in order -->

---
**1/**
If your agent uses `gh` today, it's flying blind.

We ran a live evaluation: 13 Critical failure modes against the real binary. Here's what's actually breaking.

🧵
---

**2/**
🔴 `gh` exits 0 on every HTTP error.

401s. 404s. GraphQL failures.

They all look identical to success. Your agent has zero signal when commands fail.
---

**3/**
🔴 Token expires mid-session?

`gh` prints "Try `gh auth login`" to stderr and exits 0.

That's a browser flow. Your agent can't complete it. It just keeps going, thinking it succeeded.
---

**4/**
🔴 `gh issue create` with all flags = real issue, immediately.

No dry-run. No idempotency key.

Every retry on a failed call creates a duplicate in your repo.
---

**5/**
2 Critical gaps score 0/3.
7 score 1–2/3.
Readiness: 7/15.

Runtime brief, integration guide & fix list → [PASTE LINK HERE]

@github

#AIAgents
---
