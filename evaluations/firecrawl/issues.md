# firecrawl - Issues

## §1, §10, §45 - Auth-required commands exit 0 after printing an interactive prompt

**Date:** 2026-05-27
**Trigger:** `./node_modules/.bin/firecrawl scrape https://example.com` with `stdin=subprocess.DEVNULL` and no `FIRECRAWL_API_KEY`
**Observed:** Exit code 0 with a stdout login prompt ending in `Enter choice [1/2]:`.
**Impact:** Agents may treat the command as successful even though no scrape occurred, and may attempt to parse prompt text as result data.

## §64 - Browser login hangs in headless execution

**Date:** 2026-05-27
**Trigger:** `./node_modules/.bin/firecrawl login --browser` with `DISPLAY` unset and stdin closed
**Observed:** The CLI printed an auth URL, then repeatedly waited for browser authentication until the 4s external timeout killed it.
**Impact:** Agents need an external timeout and URL extraction workaround for browser auth.

## §2 - JSON mode does not cover error/auth paths

**Date:** 2026-05-27
**Trigger:** `./node_modules/.bin/firecrawl search firecrawl --json` without credentials
**Observed:** Exit code 0 with a human login prompt on stdout instead of JSON.
**Impact:** Agents cannot safely rely on `--json` before authentication.

## §13 - `init --skip-skills` reported skills installed

**Date:** 2026-05-27
**Trigger:** `./node_modules/.bin/firecrawl init -y --skip-install --skip-auth --skip-skills`
**Observed:** Exit code 0 and stdout included `Skills installed across your AI coding agents` despite `--skip-skills`.
**Impact:** Agents cannot tell whether a skipped setup step actually ran, was skipped, or only reported stale status.

## §23 - Destructive/config-mutating commands lack dry-run

**Date:** 2026-05-27
**Trigger:** `./node_modules/.bin/firecrawl logout --dry-run`
**Observed:** Exit code 1 with `error: unknown option '--dry-run'`.
**Impact:** Agents cannot preview credential/config side effects before executing them.
