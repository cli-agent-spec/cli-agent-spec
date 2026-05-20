# docuseal-cli - Runtime Brief
Generated: 2026-05-20 | CLI version: 1.0.3 | Findings: 71 failure modes | Scope: all

## Invoke As

node bin/run.js

## Always Include

| Flag / Env var | Reason | §N |
|---|---|---|
| DOCUSEAL_API_KEY=<secret> | Avoid interactive configure and missing-auth stack trace | §10, §24, §45 |
| DOCUSEAL_SERVER=<global/europe/url> | Avoid implicit config precedence ambiguity | §28 |
| XDG_CONFIG_HOME=<isolated temp dir> | Avoid shared global config state | §26, §65 |
| wrapper timeout | CLI has no built-in timeout | §11 |
| stdin=DEVNULL | Prevent prompt paths from consuming agent input | §10 |

## Never Do

| Action | Risk | §N |
|---|---|---|
| Parse stdout as a stable envelope | No ok/data/error envelope; failures may be prose or stack traces | §1, §2, §18 |
| Trust exit code 1 as semantically meaningful | Validation, auth, file, and network failures collapse to generic exit 1 | §1 |
| Run configure without both --api-key and --server | Non-TTY prompt path can exit 0 without configuring | §10 |
| Let commands write default user config in shared runs | Config writes default to global user config | §58, §65 |
| Assume bundled skill metadata matches binary | Skill version 1.0.6 differs from binary 1.0.3 | §72 |

## Watch in Output

| Pattern | Meaning | Action |
|---|---|---|
| ^error: unknown option | Unsupported flag/schema mode | Abort and update wrapper capability map |
| Error: No API key found | Missing credentials | Inject DOCUSEAL_API_KEY or --api-key |
| SyntaxError: | Invalid JSON in -d or runtime parse crash | Treat as structured parse failure; do not retry unchanged |
| Error: ENOENT | Missing local file path | Surface FILE_NOT_FOUND to caller |
| Node.js v | Unhandled exception footer | Treat stderr as crash evidence |

## Score Summary

| §N | Title | Severity | Score |
|---|---|---|---|
| §1 | Exit Codes & Status Signaling | Critical | 0/3 |
| §2 | Output Format & Parseability | Critical | 1/3 |
| §10 | Interactivity & TTY Requirements | Critical | 1/3 |
| §11 | Timeouts & Hanging Processes | Critical | 0/3 |
| §12 | Idempotency & Safe Retries | Critical | 0/3 |
| §13 | Partial Failure & Atomicity | Critical | 0/3 |
| §23 | Side Effects & Destructive Operations | Critical | 0/3 |
| §24 | Authentication & Secret Handling | Critical | 0/3 |
| §25 | Prompt Injection via Output | Critical | 0/3 |
| §34 | Shell Injection via Agent-Constructed Commands | Critical | 1/3 |
| §37 | REPL / Interactive Mode Accidental Triggering | Critical | 3/3 |
| §42 | Debug / Trace Mode Secret Leakage | Critical | 2/3 |
| §43 | Tool Output Result Size Unboundedness | Critical | 0/3 |
| §45 | Headless Authentication / OAuth Browser Flow Blocking | Critical | 1/3 |
| §50 | Stdin Consumption Deadlock | Critical | 3/3 |
| §53 | Credential Expiry Mid-Session | Critical | 0/3 |
| §60 | OS Output Buffer Deadlock | Critical | 0/3 |
| §61 | Bidirectional Pipe Payload Deadlock | Critical | 3/3 |
| §62 | $EDITOR and $VISUAL Trap | Critical | 3/3 |
| §64 | Headless Display and GUI Launch Blocking | Critical | 3/3 |
| §71 | Non-Interactive Installation Absence | Critical | 2/3 |
| §74 | Credential Scope Declaration Absence | Critical | 0/3 |
| §3 | Stderr vs Stdout Discipline | High | 1/3 |
| §5 | Pagination & Large Output | High | 1/3 |
| §8 | ANSI & Color Code Leakage | High | 3/3 |
| §9 | Binary & Encoding Safety | High | 2/3 |
| §14 | Argument Validation Before Side Effects | High | 1/3 |
| §15 | Race Conditions & Concurrency | High | 0/3 |
| §16 | Signal Handling & Graceful Cancellation | High | 0/3 |
| §18 | Error Message Quality | High | 0/3 |
| §19 | Retry Hints in Error Responses | High | 0/3 |
| §22 | Schema Versioning & Output Stability | High | 0/3 |
| §26 | Stateful Commands & Session Management | High | 0/3 |
| §28 | Config File Shadowing & Precedence | High | 1/3 |
| §31 | Network Proxy Unawareness | High | 0/3 |
| §32 | Self-Update & Auto-Upgrade Behavior | High | 3/3 |
| §35 | Agent Hallucination Input Patterns | High | 0/3 |
| §38 | Runtime Dependency Version Mismatch | High | 0/3 |
| §40 | parse() vs parseAsync() Silent Race Condition | High | 0/3 |
| §41 | Update Notifier Side-Channel Output Pollution | High | 2/3 |
| §46 | API Schema to CLI Flag Translation Loss | High | 1/3 |
| §47 | MCP Wrapper Schema Staleness | High | 0/3 |
| §49 | Async Job / Polling Protocol Absence | High | 0/3 |
| §51 | Shell Word Splitting and Glob Expansion Interference | High | 1/3 |
| §54 | Conditional / Dependent Argument Requirements | High | 0/3 |
| §55 | Silent Data Truncation | High | 0/3 |
| §56 | Exit Code Masking in Shell Pipelines | High | 0/3 |
| §58 | Multi-Agent Concurrent Invocation Conflict | High | 0/3 |
| §59 | High-Entropy String Token Poisoning | High | 1/3 |
| §65 | Global Configuration State Contamination | High | 0/3 |
| §66 | Symlink Loop and Recursive Traversal Exhaustion | High | 3/3 |
| §67 | Agent-Generated Input Syntax Rejection | High | 0/3 |
| §68 | Third-Party Library Stdout Pollution | High | 0/3 |
| §69 | Argument Order Ambiguity | High | 1/3 |
| §70 | Single-Argument Arity Forcing Agent Loop Overhead | High | 0/3 |
| §72 | Integration Artifact Version Drift | High | 0/3 |
| §73 | Documentation Accuracy Drift | High | 1/3 |
| §4 | Verbosity & Token Cost | Medium | 1/3 |
| §6 | Command Composition & Piping | Medium | 0/3 |
| §7 | Output Non-Determinism | Medium | 0/3 |
| §17 | Child Process Leakage | Medium | 3/3 |
| §20 | Environment & Dependency Discovery | Medium | 0/3 |
| §21 | Schema & Help Discoverability | Medium | 0/3 |
| §27 | Platform & Shell Portability | Medium | 1/3 |
| §29 | Working Directory Sensitivity | Medium | 0/3 |
| §30 | Undeclared Filesystem Side Effects | Medium | 0/3 |
| §33 | Observability & Audit Trail | Medium | 0/3 |
| §44 | Agent Knowledge Packaging Absence | Medium | 1/3 |
| §52 | Recursive Command Tree Discovery Cost | Medium | 0/3 |
| §57 | Locale-Dependent Error Messages | Medium | 0/3 |
| §63 | Terminal Column Width Output Corruption | Medium | 0/3 |

**Worst gaps (score 0):** §43, §53, §60, §35, §38, §40, §47, §49, §54, §55, §56, §58, §65, §67, §68, §70, §72, §52, §57, §63, §11, §12, §13, §15, §16, §23, §24, §25, §74, §1, §6, §7, §26, §31, §29, §30, §18, §19, §22, §20, §21, §33
**Partial (score 1-2):** §34, §42, §45, §71, §41, §46, §51, §59, §69, §73, §44, §10, §14, §2, §3, §5, §9, §4, §28, §27
**Indeterminate (?/3 - timed out):** None
**Passing:** §37, §50, §61, §62, §64, §66, §17, §8, §32
