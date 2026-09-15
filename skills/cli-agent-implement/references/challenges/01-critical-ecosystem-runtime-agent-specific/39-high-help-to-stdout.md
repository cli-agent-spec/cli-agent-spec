# 39. Help To Stdout

> **MERGED** — This challenge has been consolidated into **§3** because it describes
> a specific case of the same root problem.
>
> See: [`03-high-stderr-stdout.md`](../04-critical-output-and-parsing/03-high-stderr-stdout.md)
>
> **Agent workaround:** apply the §3 workaround — treat `Usage:`/`Options:` on stdout with nonzero exit as a usage error, not data; recover mixed output with the JSON extraction rule in [`triage.md`](../triage.md)
