## Git recovery — merge strategy

When the task asks you to recover lost changes and merge them into master:

- The user's changes are the **incoming** side of the merge (the commit or branch being merged in)
- If `git merge <ref>` exits 1 with CONFLICT, **do not stop to ask the user** — they already told you their changes should win
- Resolve by always taking the incoming side:
  ```
  git checkout --theirs <conflicted-file>
  git add <conflicted-file>
  git commit --no-edit
  ```
- Prefer avoiding the conflict entirely: use `git merge -X theirs <ref> --no-edit`
