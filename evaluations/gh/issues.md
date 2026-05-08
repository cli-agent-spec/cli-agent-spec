# gh — Issues

### §1 candidate — HTTP error responses exit 0
`gh issue view 999999999 --repo cli/cli` returns a GraphQL error message to stderr but exits 0.
`GH_TOKEN=invalid_token gh repo view cli/cli` returns `HTTP 401: Bad credentials` to stderr but exits 0.
`gh label create ... --repo cli/cli` (no write permission) returns `HTTP 404: Not Found` but exits 0.
All three should exit non-zero per gh's own documented exit code conventions.
Discovered during §1 and §53 evaluation on 2026-05-07.

### §62 candidate — `gh issue create` created a live issue during testing
Running `gh issue create --repo cli/cli --title test --body test` with `EDITOR=false` silently created a real issue (#13360) on the public cli/cli repository. The command did not warn that it was about to create a permanent resource, and exited 0 with just the issue URL printed. Agents running §62 checks without dry-run awareness will create real resources.
Discovered during §62 evaluation on 2026-05-07.

### §45/§53 candidate — Auth failure not machine-readable
`GH_TOKEN=invalid_token gh repo view cli/cli` produces `HTTP 401: Bad credentials (https://api.github.com/graphql)\nTry authenticating with:  gh auth login` on stderr, exits 0. An agent has no way to distinguish this from a network error or permissions error programmatically. The suggested fix (`gh auth login`) is interactive-only.
Discovered during §45 and §53 evaluation on 2026-05-07.
