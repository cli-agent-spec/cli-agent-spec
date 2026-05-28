# shopify — Issues

### §45 candidate — auth login blocks non-interactive agents
`shopify auth login` under non-TTY printed a device-code URL and kept running until manually terminated instead of exiting with a structured auth-required response.
Discovered during §45 evaluation on 2026-05-28.

### §37 candidate — Liquid REPL path hangs under non-TTY
`shopify theme console` launched in a non-TTY context emitted release notes and did not exit before the 3s alarm killed it.
Discovered during §37 evaluation on 2026-05-28.

### §2 candidate — release notes and preference errors pollute command output
Theme commands emitted release-note boxes, analytics/storage errors, and stack traces before the actual command result, making stdout/stderr unsuitable for deterministic parsing.
Discovered during §2 evaluation on 2026-05-28.

### §24 candidate — secret material can be supplied as command-line flags
Theme commands accept `--password=<value>` even though that places credentials in command histories/process lists; env var alternatives exist but are not enforced.
Discovered during §24 evaluation on 2026-05-28.

### §30 candidate — undeclared writes to user preferences
Several commands attempted to write under `/Users/roman/Library/Preferences/...`, causing sandbox `EPERM` failures and stack traces before command-specific validation could run.
Discovered during §10 and §2 evaluation on 2026-05-28.
