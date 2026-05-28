# omd — Issues

## §1 / §2 — Invocation errors bypass JSON envelope

**Date:** 2026-05-28
**Trigger:** `./target/debug/omd patch --output json`
**Observed:** Exit code 2 with clap prose on stderr and no JSON stdout.
**Impact:** Agents requesting JSON cannot uniformly parse required-argument failures.

## §11 — Timeout taxonomy collapses to GENERAL_ERROR

**Date:** 2026-05-28
**Trigger:** `./target/debug/omd search orders --host http://127.0.0.1:<hanging-port> --timeout 1 --output json`
**Observed:** Process exited after about 1 second, but returned `GENERAL_ERROR`, `retryable: false`, and exit code 1.
**Impact:** Agents cannot distinguish a timeout from a non-retryable general failure.

## §53 / §24 — Auth status can emit two JSON envelopes

**Date:** 2026-05-28
**Trigger:** `./target/debug/omd auth status --host http://localhost:8585 --token invalid-secret-value --output json`
**Observed:** stdout contained an `ok: true` status envelope followed by an `ok: false` `AUTH_REQUIRED` envelope.
**Impact:** Agents that parse the first JSON object may incorrectly conclude auth is valid.

## §74 — Required credential scopes are not declared

**Date:** 2026-05-28
**Trigger:** `./target/debug/omd search --schema`
**Observed:** Command schema included typed inputs, capabilities, and transport metadata, but no `required_scopes`.
**Impact:** Agents cannot choose minimally scoped credentials from the machine-readable interface.
