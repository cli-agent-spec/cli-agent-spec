# Firecrawl CLI - Integration Guide for Agent Builders

**Generated:** 2026-05-27
**Binary:** `./node_modules/.bin/firecrawl`
**Timeout method:** `subprocess.run(timeout=N)`

## Required Wrapper Behavior

1. Provide credentials through `FIRECRAWL_API_KEY`; do not pass API keys on the command line.
2. Wrap every call with stdin closed, captured stdout/stderr, and a hard timeout.
3. Treat auth prompts as failures even when the CLI returns exit code 0.
4. Validate JSON strictly. If parsing fails, surface stdout/stderr as an unstructured CLI error.
5. For browser auth, extract the printed URL and stop; do not wait indefinitely for the CLI process.

## Suggested Python Wrapper Skeleton

```python
import json, os, subprocess

def run_firecrawl(args, timeout=60):
    env = os.environ | {
        "CI": "true",
        "NO_COLOR": "1",
        "FIRECRAWL_NO_TELEMETRY": "1",
        "PAGER": "cat",
        "EDITOR": "true",
        "VISUAL": "true",
    }
    result = subprocess.run(
        ["./node_modules/.bin/firecrawl", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    text = result.stdout.strip()
    if "Enter choice" in text or "Welcome! To get started" in text:
        raise RuntimeError("Firecrawl authentication required")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Unstructured Firecrawl output: rc={result.returncode} "
            f"stdout={text[:300]} stderr={result.stderr[:300]}"
        )
```

## Missing CLI Contract

A robust integration would benefit from `firecrawl --schema` containing commands, flags, exit codes, auth methods, required scopes, safe defaults, and headless behavior.
