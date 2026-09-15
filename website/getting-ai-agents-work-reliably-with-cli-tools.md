# Getting AI Agents to Work Reliably with CLI Tools

It seems pretty well accepted that AI agents are bad at using tools.

They get stuck in retry loops. They hang on commands that wait for input. They fill the context with logs nobody needed. They misread successful-looking failures. They sometimes retry operations that should never be retried.

The common explanation is usually some version of: the model is not smart enough yet.

I think that is only partly true.

After working on this for a while, I am now convinced that a large part of the problem is much more boring: most CLI tools were designed for humans sitting at a terminal, not for agents calling subprocesses inside a constrained loop.

Humans can scroll, read prose, press `q`, answer `yes`, inspect a weird error, and decide whether retrying is safe.

Agents need contracts.

I built CLI Agent Spec to document those contracts:

https://cli-agent-spec.github.io/

The repo currently has 74 failure modes, 158 requirements, JSON schemas, a framework comparison matrix covering 71 of those modes so far, installable evaluation and implementation skills, and the beginning of FixLayer: an automatic diagnostic layer for failed tool calls.

## How This Started

I started with a question to an LLM:

> What problems do you know about when agents execute CLI tools, MCP tools, API wrappers, and shell commands?

My working assumption was simple: the model was trained on a huge amount of tool-use failure. GitHub issues, docs, CI logs, Stack Overflow answers, agent traces, shell snippets, and workaround-heavy code.

The model cannot show me its training data. But it can surface the patterns it has learned to route around.

The first answer was basically a wall of pain: bad exit codes, broken JSON, color codes in `stdout`, interactive prompts, pagers, unbounded logs, OAuth browser flows, partial failures, secret leakage, stale schemas, and commands that look successful while doing the wrong thing.

So I kept asking.

What assumptions do agents make when they call CLI tools?

Which failures waste the most tokens?

Which failures burn time?

Which failures pollute context?

Which failures are impossible for the agent to recover from?

At some point I had to stop the conversation and turn it into structure. The stream did not feel exhausted. It felt like I had opened a catalog of recurring workaround patterns agents seem to have learned.

## What Is Actually Possible Today

This is not theoretical.

A lot of the highest impact improvements are small:

- Detect non-TTY execution
- Provide `--yes` and `--non-interactive`
- Disable pagers outside a real terminal
- Keep `stdout` machine-parseable
- Send diagnostics to `stderr`
- Disable ANSI color when there is no TTY
- Provide `--output json`
- Bound output size by default
- Use exit codes that mean something
- Report whether a failed command is retryable
- Report whether side effects happened
- Expose a machine-readable command manifest

None of this requires a new model.

It requires CLI authors and framework maintainers to accept that "works great in my terminal" is not the same as "works great for an agent."

## The Naive Way to Fix Agent Tool Use

The naive solution is to add more prompt instructions.

> Always pass `--json`

> Never retry destructive commands

> Set `PAGER=cat`

> Remember to use `--no-color`

This helps until it does not.

The prompt gets longer. The agent forgets. A different tool uses a different flag. A wrapper hides the underlying command. A new version changes output. The agent burns another turn rediscovering something the tool could have declared directly.

Prompting around bad CLI ergonomics is like asking every user to memorize undefined behavior.

## There Is an Executable Layer

This is not only a document.

The repo includes installable agent skills that use the taxonomy directly. The core public-facing ones are:

- `cli-agent-audit` runs an end-to-end CLI audit: install, onboard, readiness score, failure-mode evaluation, and reports
- `cli-agent-evaluate` scores one CLI against one failure mode
- `cli-agent-diagnose` classifies a failed CLI call against the failure-mode taxonomy and returns an agent workaround
- `cli-agent-implement` helps framework authors implement the requirements tier by tier

There are supporting skills under the hood for onboarding, batch evaluation, readiness scoring, report generation, visual trace reports, and spec validation. They are pipeline pieces, not separate product claims.

That changed how I think about the project.

The spec is the source of truth. The skills are the executable layer.

An agent can hit a bad CLI call, classify the failure as interactivity, unbounded output, mixed `stdout` and `stderr`, stale schema, unsafe retry, partial failure, or another named failure mode, then read the documented workaround and produce a stable memory or implementation fix.

That is much better than asking every agent to rediscover the same workaround in every new context window.

## FixLayer

I am also working on FixLayer, an early attempt to solve tool-execution failures automatically.

The current repo includes a trace-reporting piece for FixLayer. The broader idea is to sit around agent tool calls and use the CLI Agent Spec taxonomy as the diagnostic layer.

Before a call, the goal is for FixLayer to detect command shapes that are likely to fail: unbounded `git log`, missing `--no-pager`, interactive editor traps, unsafe destructive commands.

During a call, the intended wrapper can apply safer defaults: timeouts, non-interactive stdin, pager suppression, color suppression, and output limits.

After a call, the diagnostic layer can classify failures such as timeout, bad parse, mixed `stdout` and `stderr`, prompt waiting for input, unbounded output, stale schema, unsafe retry, or partial failure.

The output is not just "something went wrong." It is:

- The matching failure mode
- Confidence
- The immediate workaround
- A memory string the agent can reuse
- A skill patch or implementation recommendation

So the longer-term goal is not only better CLIs.

It is an automatic repair loop for tool execution: detect known failure classes, apply the safe workaround when possible, and push the permanent fix back into the CLI or framework.

## What Exactly Needs to Be Fixed?

When an agent calls a CLI, the tool output becomes part of the agent's context.

That means CLI behavior affects correctness directly.

The worst outcomes are:

1. Incorrect information
2. Missing information
3. Too much noise

A bad error code is incorrect information.

A timeout with no partial-state report is missing information.

A giant log dump is noise.

This is why boring CLI details become expensive in agent systems. A human sees terminal output. An agent sees input to the next reasoning step.

## The Core Contract

I think agent-safe CLIs need three basic contracts.

First: execution contract.

The tool must not block on hidden interactivity. It should know when there is no TTY. It should fail fast or switch to non-interactive behavior.

Second: parse contract.

The tool must make machine-readable output the default or at least a reliable mode. `stdout` should be data. `stderr` should be diagnostics. JSON should not be preceded by warnings, banners, colors, progress bars, or update notices.

Third: recovery contract.

The tool must tell the agent what happened. Was the error retryable? Did side effects happen? Was the operation partial? Is there a safe next command?

Without that, the agent guesses.

And when agents guess, users pay for it in tokens, time, and occasionally damaged state.

## A Concrete Example

One real example is `git log`.

For a human, the default output is fine. You scroll until you find what you need.

For an agent, unbounded history is often just context pollution. On a small repository it can add thousands of tokens. On a large one, it can dominate the turn. The agent usually wanted something closer to:

```bash
git --no-pager log --format='%h %s' -n 20
```

That is the pattern FixLayer is meant to detect automatically: the command is valid, but its default output shape is hostile to the agent loop.

For recovery semantics, imagine this command:

```bash
deploy --env staging
```

It runs for 30 seconds and exits with code `1`.

For a human, that might be enough. The human reads the logs and decides what to do.

For an agent, this is under-specified.

Exit code `1` might mean validation failed before anything happened.

It might mean the deploy started and half the resources changed.

It might mean the deploy succeeded but the client timed out while waiting.

Those are three different recovery paths.

The agent needs something closer to:

```json
{
  "ok": false,
  "error": {
    "code": "PARTIAL_FAILURE",
    "message": "Deployment failed after service update",
    "retryable": false,
    "side_effects": "partial",
    "suggestion": "Run deploy status --env staging before retrying"
  },
  "meta": {
    "request_id": "req_123",
    "duration_ms": 30000
  }
}
```

That response is not just nicer formatting. It changes what the agent can safely do next.

## Existing Solutions Get Part of the Way There

I compared argparse, Click, Typer, Python Fire, Pydantic, OpenAPI, Cobra, Clap, Commander.js, MCP, agentyper, and an agent-DX rubric against 71 mapped failure modes. The newest modes still need to be folded into the matrix.

MCP scores highest in my matrix because structured invocation avoids many shell and parsing problems.

But MCP does not automatically fix the behavior of the underlying tool.

If the wrapped CLI has stale schemas, unsafe retries, destructive defaults, unbounded output, bad error semantics, or hidden browser auth, the agent still inherits the failure. The protocol helps with transport and discovery. The invoked tool still needs behavioral guarantees.

That is the gap CLI Agent Spec tries to define.

## This Is Not Magic

The source story matters.

Some failure modes came from asking the LLM what it had learned to work around. Some came from first-principles reasoning about subprocesses and context windows. Some came from reading real framework docs and existing tools.

This is not telemetry. The frequency labels are estimates, not measured rates.

The spec will be wrong in places.

But the failures are concrete enough to test. Each challenge has an evaluation section. A CLI either hangs on non-interactive input or it does not. It either keeps JSON clean or it does not. It either distinguishes retryable errors from non-retryable ones or it does not.

That is the useful part.

## Why I Think This Belongs in Frameworks

Most command authors will not implement all of this by hand.

They should not have to.

Frameworks already standardize argument parsing, help text, validation, and command registration. They can also standardize agent-safe defaults:

- Automatic JSON envelope mode
- Standard exit code table
- Non-TTY detection
- Pager suppression
- Color suppression
- Timeout handling
- Stream separation
- Schema generation
- Command manifests
- Retry metadata
- Side-effect declarations
- Output limits

If the framework owns the contract, every command built on top gets better.

## Recap

The project started as an experiment: ask an LLM what CLI and tool-execution failures it has learned to bypass.

That turned into a taxonomy.

The taxonomy turned into requirements.

The requirements turned into schemas, comparisons, skills, and FixLayer.

The bigger point is simple: AI agents do not need prettier terminal output. They need CLIs with machine-readable behavior.

I would like feedback from CLI authors, framework maintainers, and people building coding agents.

Which failure modes are wrong?

Which ones are missing?

Which requirements should be framework defaults?

Which ones are unrealistic in real tools?
