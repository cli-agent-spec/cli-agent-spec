# Changelog fragments

Each pull request adds its changelog entry here as its own file instead of editing
`CHANGELOG.md`, so two pull requests never conflict on it. A stable release writes the
fragments into its section of `CHANGELOG.md` and deletes them; this README stays.

Name a fragment `<issue>-<slug>.md`, such as `changelog.d/244-merged-pr-head-landed.md`, and
write what the pull request would have added under Unreleased, in the CHANGELOG's style:

```markdown
### Worktrees: a branch whose tip was a merged PR's head landed (#244)

It lands no more.
```
