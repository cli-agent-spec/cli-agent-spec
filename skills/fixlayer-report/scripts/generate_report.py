# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
fixlayer-report generator

Runs diagnose.py --explain on a trace file, then renders the result as a
self-contained HTML report in the FixLayer design system.

Usage:
    uv run scripts/generate_report.py <trace-file> [--out report.html] [--challenges-dir PATH]

Exit codes:
    0  report written
    1  input error or classifier error
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MIN_PYTHON = (3, 10)

_SKILL_DIR = Path(__file__).parent.parent
_DIAGNOSE = _SKILL_DIR.parent / "cli-agent-diagnose" / "scripts" / "diagnose.py"


def require_supported_python() -> None:
    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = ".".join(str(part) for part in sys.version_info[:3])
        print(
            f"generate_report.py requires Python {required}+; current Python is {current}. Run it with `uv run` or a Python {required}+ interpreter.",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# Run classifier
# ---------------------------------------------------------------------------

def run_diagnose(trace_path: Path, challenges_dir: Path | None) -> dict:
    cmd = ["uv", "run", str(_DIAGNOSE), "--history", str(trace_path), "--explain"]
    if challenges_dir:
        cmd += ["--challenges-dir", str(challenges_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"Error: diagnose.py produced no output\nstderr: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Session stats from JSONL
# ---------------------------------------------------------------------------

def session_stats(trace_path: Path) -> dict:
    records: list[dict] = []
    text = trace_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
        records = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    tool_counts: dict[str, int] = {}
    durations: list[int] = []
    interrupted = 0
    session_id = ""

    for r in records:
        if not isinstance(r, dict):
            continue
        tool = r.get("tool_name", "unknown")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        if "duration_ms" in r:
            durations.append(int(r["duration_ms"]))
        if r.get("tool_response", {}).get("interrupted"):
            interrupted += 1
        if not session_id and r.get("session_id"):
            session_id = r["session_id"]

    bash = tool_counts.get("Bash", 0)
    return {
        "total": len(records),
        "tool_counts": tool_counts,
        "bash": bash,
        "durations": durations,
        "total_ms": sum(durations),
        "max_ms": max(durations) if durations else 0,
        "avg_ms": sum(durations) // len(durations) if durations else 0,
        "interrupted": interrupted,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def h(s: str) -> str:
    return html.escape(str(s))


def severity_badge(sev: str) -> str:
    cls = "critical" if sev == "critical" else "high" if sev == "high" else "med"
    return f'<span class="badge {cls}">{h(sev)}</span>'


def conf_badge(conf: float) -> str:
    return f'<span class="badge conf">{int(conf * 100)}% confident</span>'


def render_event_row(ev: dict) -> str:
    cmd = h(ev.get("command", "")[:120])
    ec = ev.get("exit_code", 0)
    attempt = ev.get("attempt", 1)
    stderr = h(ev.get("stderr_excerpt", "")[:200])
    stdout = h(ev.get("stdout_excerpt", "")[:200])
    timed_out = ev.get("timed_out", False)

    ec_class = "fail" if ec != 0 else "ok"
    ec_label = f"exit {ec}" if not timed_out else "timed out"
    retry_tag = f'<span class="event-tag retry">attempt {attempt}</span>' if attempt > 1 else ""
    excerpt = stderr or stdout

    return f"""
    <div class="event-row">
      <div class="event-cmd">{cmd}</div>
      <div class="event-meta">
        <span class="event-tag {ec_class}">{ec_label}</span>
        {retry_tag}
      </div>
      {"<div class='event-excerpt'>" + excerpt + "</div>" if excerpt else ""}
    </div>"""


def render_match(m: dict) -> str:
    fid = m["failure_mode_id"]
    title = h(m.get("title", f"§{fid}"))
    sev = m.get("severity", "unknown")
    conf = m.get("confidence", 0.0)
    evidence = h(m.get("evidence", ""))
    workaround = m.get("workaround", "")
    limitation = h(m.get("limitation", ""))
    memory = h(m.get("memory", ""))
    skill_patch = h(m.get("skill_patch", ""))
    events = m.get("triggering_events", [])

    # Render workaround: convert markdown code fences to <pre>
    import re
    wa_html = h(workaround)
    wa_html = re.sub(r"```(?:\w+)?\n(.*?)```", lambda x: f"<pre>{x.group(1)}</pre>", wa_html, flags=re.DOTALL)
    wa_html = re.sub(r"`([^`]+)`", lambda x: f"<code>{x.group(1)}</code>", wa_html)
    wa_html = re.sub(r"\*\*([^*]+)\*\*", lambda x: f"<strong>{x.group(1)}</strong>", wa_html)

    events_html = "".join(render_event_row(e) for e in events)
    event_count = len(events)

    return f"""
  <div class="match-card {sev}">
    <div class="match-header">
      <span class="match-code">§{fid}</span>
      <span class="match-title">{title}</span>
      <div class="match-badges">
        {severity_badge(sev)}
        {conf_badge(conf)}
        <span class="badge det">deterministic · 0 tokens</span>
      </div>
    </div>
    <div class="match-body">
      <div class="match-evidence"><strong>Evidence:</strong> {evidence}</div>

      <div class="events-label">Triggering tool calls ({event_count} event{"s" if event_count != 1 else ""})</div>
      <div class="event-list">{events_html}</div>

      <div class="workaround-block">
        <div class="workaround-label">Workaround</div>
        <div class="workaround-body">{wa_html}</div>
      </div>

      {"<div class='limitation-block'><strong>Limitation:</strong> " + limitation + "</div>" if limitation else ""}

      <div class="store-grid">
        <div class="store-card">
          <div class="store-label">Memory — store this</div>
          <div class="store-body">[{h(m.get("title","")[:20])} §{fid}] {memory}</div>
        </div>
        <div class="store-card">
          <div class="store-label">Skill patch</div>
          <div class="store-body">{skill_patch}</div>
        </div>
      </div>
    </div>
  </div>"""


def render_action_items(matches: list[dict]) -> str:
    items = []
    colors = ["var(--red)", "var(--orange)", "var(--green)", "var(--accent)"]
    border_colors = ["rgba(248,81,73,0.3)", "rgba(240,136,62,0.3)", "rgba(63,185,80,0.25)", "rgba(88,166,255,0.25)"]
    bg_colors = ["rgba(248,81,73,0.15)", "rgba(240,136,62,0.15)", "rgba(63,185,80,0.12)", "rgba(88,166,255,0.12)"]

    for i, m in enumerate(matches):
        fid = m["failure_mode_id"]
        title = h(m.get("title", f"§{fid}"))
        patch = h(m.get("skill_patch", "apply the documented workaround"))
        c = min(i, 3)
        items.append(f"""
      <div style="display:flex;gap:1.25rem;padding:1.25rem 0;border-bottom:1px solid var(--border);align-items:flex-start;">
        <div style="width:28px;height:28px;border-radius:50%;background:{bg_colors[c]};border:1px solid {border_colors[c]};color:{colors[c]};font-weight:800;font-size:0.8rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:0.1rem">{i+1}</div>
        <div>
          <div style="font-weight:700;margin-bottom:0.25rem">Resolve §{fid} — {title}</div>
          <div style="font-size:0.85rem;color:var(--muted)">{patch}</div>
        </div>
      </div>""")

    return "\n".join(items)


# ---------------------------------------------------------------------------
# Full HTML template
# ---------------------------------------------------------------------------

CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d1117; --bg2: #161b22; --bg3: #21262d;
      --border: #30363d; --text: #e6edf3; --muted: #8b949e;
      --red: #f85149; --orange: #f0883e; --yellow: #d29922;
      --green: #3fb950; --accent: #58a6ff; --purple: #bc8cff;
      --nav-bg: rgba(13,17,23,0.92); --code-bg: #0d1117; --code-text: #a5d6ff;
    }
    html[data-theme="light"] {
      --bg:#fff;--bg2:#f6f8fa;--bg3:#eaeef2;--border:#d0d7de;--text:#1f2328;
      --muted:#57606a;--red:#cf222e;--orange:#bc4c00;--green:#1a7f37;
      --accent:#0969da;--purple:#8250df;--nav-bg:rgba(255,255,255,0.92);
      --code-bg:#f6f8fa;--code-text:#24292f;
    }
    @media(prefers-color-scheme:light){html:not([data-theme="dark"]){
      --bg:#fff;--bg2:#f6f8fa;--bg3:#eaeef2;--border:#d0d7de;--text:#1f2328;
      --muted:#57606a;--red:#cf222e;--orange:#bc4c00;--green:#1a7f37;
      --accent:#0969da;--purple:#8250df;--nav-bg:rgba(255,255,255,0.92);
      --code-bg:#f6f8fa;--code-text:#24292f;
    }}
    html{scroll-behavior:smooth}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;font-size:16px}
    a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
    code,pre{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace}
    nav{position:sticky;top:0;z-index:100;background:var(--nav-bg);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);padding:0 2rem;display:flex;align-items:center;justify-content:space-between;height:56px}
    .nav-brand{font-weight:800;font-size:1rem;color:var(--text);letter-spacing:-0.02em}
    .nav-brand span{color:var(--accent)}
    .nav-meta{font-size:0.8rem;color:var(--muted)}
    .theme-btn{width:32px;height:32px;background:var(--bg3);border:1px solid var(--border);border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--muted)}
    .theme-btn:hover{color:var(--text)}
    section{padding:4rem 1rem}
    .container{max-width:900px;margin:0 auto}
    .divider{border:none;border-top:1px solid var(--border);margin:0}
    .hero{padding:4rem 1rem 3rem;background:radial-gradient(ellipse 80% 50% at 50% -20%,rgba(88,166,255,0.07),transparent)}
    .report-badge{display:inline-block;background:rgba(88,166,255,0.1);border:1px solid rgba(88,166,255,0.25);color:var(--accent);font-size:0.75rem;font-weight:700;padding:0.25rem 0.75rem;border-radius:20px;margin-bottom:1.25rem;letter-spacing:0.05em;text-transform:uppercase}
    .hero h1{font-size:clamp(1.6rem,4vw,2.5rem);font-weight:800;letter-spacing:-0.03em;line-height:1.15;margin-bottom:0.75rem}
    .hero h1 em{color:var(--accent);font-style:normal}
    .hero-meta{font-size:0.82rem;color:var(--muted);margin-bottom:2rem;font-family:monospace}
    .hero-meta span{color:var(--text)}
    .stats-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:10px;overflow:hidden}
    .stat-cell{background:var(--bg2);padding:1.25rem 1rem;text-align:center}
    .stat-cell .n{font-size:1.75rem;font-weight:800;letter-spacing:-0.04em}
    .stat-cell .label{font-size:0.72rem;color:var(--muted);margin-top:0.2rem;line-height:1.3}
    .verdict{border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.5rem;border:1px solid;display:flex;align-items:center;gap:1rem}
    .verdict.fail{background:rgba(248,81,73,0.07);border-color:rgba(248,81,73,0.3)}
    .verdict.ok{background:rgba(63,185,80,0.07);border-color:rgba(63,185,80,0.3)}
    .verdict-icon{font-size:1.5rem;flex-shrink:0}
    .verdict-title{font-weight:800;font-size:1.05rem;margin-bottom:0.2rem}
    .verdict.fail .verdict-title{color:var(--red)}
    .verdict.ok .verdict-title{color:var(--green)}
    .verdict-sub{font-size:0.85rem;color:var(--muted)}
    .section-label{font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--accent);margin-bottom:0.6rem}
    .section-title{font-size:clamp(1.25rem,2.5vw,1.75rem);font-weight:800;letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.6rem}
    .section-sub{font-size:0.9rem;color:var(--muted);max-width:620px;line-height:1.7;margin-bottom:2rem}
    .match-card{background:var(--bg2);border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:1.5rem}
    .match-card.critical{border-color:rgba(248,81,73,0.4)}
    .match-card.high{border-color:rgba(240,136,62,0.4)}
    .match-header{padding:1rem 1.25rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap}
    .match-code{background:rgba(88,166,255,0.12);border:1px solid rgba(88,166,255,0.25);color:var(--accent);font-weight:800;font-size:0.85rem;padding:0.2rem 0.65rem;border-radius:5px;font-family:monospace;flex-shrink:0}
    .match-title{font-weight:700;font-size:1rem}
    .match-badges{margin-left:auto;display:flex;gap:0.5rem;align-items:center;flex-shrink:0}
    .badge{font-size:0.7rem;font-weight:700;padding:0.2rem 0.55rem;border-radius:4px;text-transform:uppercase;letter-spacing:0.04em}
    .badge.critical{background:rgba(248,81,73,0.15);color:var(--red)}
    .badge.high{background:rgba(240,136,62,0.15);color:var(--orange)}
    .badge.med{background:rgba(210,153,34,0.15);color:var(--yellow)}
    .badge.conf{background:rgba(63,185,80,0.12);color:var(--green)}
    .badge.det{background:rgba(188,140,255,0.12);color:var(--purple)}
    .match-body{padding:1.25rem}
    .match-evidence{font-size:0.85rem;color:var(--muted);line-height:1.6;padding:0.75rem 1rem;background:var(--bg3);border-radius:6px;margin-bottom:1.25rem}
    .match-evidence strong{color:var(--text)}
    .events-label{font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--muted);margin-bottom:0.6rem}
    .event-list{display:flex;flex-direction:column;gap:0.5rem;margin-bottom:1.25rem}
    .event-row{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:0.7rem 0.9rem;font-size:0.78rem}
    .event-cmd{font-family:monospace;color:var(--code-text);word-break:break-all;margin-bottom:0.35rem}
    .event-meta{display:flex;gap:1rem;flex-wrap:wrap}
    .event-tag{font-size:0.7rem;font-weight:600;padding:0.1rem 0.4rem;border-radius:3px}
    .event-tag.fail{background:rgba(248,81,73,0.12);color:var(--red)}
    .event-tag.retry{background:rgba(240,136,62,0.12);color:var(--orange)}
    .event-tag.ok{background:rgba(63,185,80,0.10);color:var(--green)}
    .event-excerpt{color:var(--muted);font-family:monospace;margin-top:0.3rem;word-break:break-all}
    .workaround-block{background:var(--bg);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:1rem}
    .workaround-label{padding:0.5rem 1rem;background:var(--bg3);border-bottom:1px solid var(--border);font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--accent)}
    .workaround-body{padding:1rem 1.25rem;font-size:0.8rem;color:var(--muted);line-height:1.7}
    .workaround-body code{background:var(--bg3);padding:0.1rem 0.35rem;border-radius:3px;color:var(--code-text);font-size:0.78rem}
    .workaround-body pre{background:var(--code-bg);color:var(--code-text);border:1px solid var(--border);border-radius:6px;padding:0.85rem 1rem;margin:0.75rem 0;font-size:0.76rem;line-height:1.6;overflow-x:auto;white-space:pre}
    .workaround-body strong{color:var(--text)}
    .limitation-block{padding:0.7rem 1rem;background:rgba(240,136,62,0.07);border:1px solid rgba(240,136,62,0.2);border-radius:6px;font-size:0.8rem;color:var(--muted);line-height:1.6;margin-bottom:1rem}
    .limitation-block strong{color:var(--orange)}
    .store-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1.25rem}
    .store-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;overflow:hidden}
    .store-label{padding:0.45rem 0.9rem;background:var(--bg3);border-bottom:1px solid var(--border);font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--muted)}
    .store-body{padding:0.75rem 0.9rem;font-size:0.78rem;color:var(--muted);line-height:1.6;font-family:monospace}
    footer{border-top:1px solid var(--border);padding:2rem 1rem;text-align:center;color:var(--muted);font-size:0.82rem}
    footer a{color:var(--muted)}
    @media(max-width:640px){.stats-strip{grid-template-columns:repeat(3,1fr)}.store-grid{grid-template-columns:1fr}.match-badges{margin-left:0;width:100%}}
"""

JS = """
  const SUN  = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  const MOON = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  function theme(){return document.documentElement.getAttribute('data-theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light')}
  function updateBtn(){const b=document.getElementById('tb'),d=theme()==='dark';b.innerHTML=d?SUN:MOON;b.title=d?'Switch to light':'Switch to dark'}
  function toggleTheme(){const n=theme()==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('theme',n);updateBtn()}
  updateBtn();window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',updateBtn);
"""


def render_html(diag: dict, stats: dict, trace_path: Path, out_path: Path) -> str:
    matches = diag.get("matches", [])
    no_match = diag.get("no_match", False)
    trace_insufficient = diag.get("trace_insufficient", False)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    match_count = len(matches)
    critical_count = sum(1 for m in matches if m.get("severity") == "critical")
    retry_count = int(diag.get("trace_summary", "").count("retry attempt")) * 20  # rough

    # Extract retry count from trace_summary
    import re
    m_retry = re.search(r"(\d+) retry attempt", diag.get("trace_summary", ""))
    retry_count = int(m_retry.group(1)) if m_retry else 0

    bash = stats.get("bash", 0)
    total = stats.get("total", 0)
    total_ms = stats.get("total_ms", 0)
    session_id = stats.get("session_id", "")

    verdict_class = "fail" if match_count > 0 else "ok"
    verdict_icon = "⚠" if match_count > 0 else "✓"
    if match_count > 0:
        verdict_title = f"{match_count} failure mode{'s' if match_count != 1 else ''} detected — resolve before retrying"
        verdict_sub = ", ".join(f"§{m['failure_mode_id']} ({m.get('severity','?')})" for m in matches)
    else:
        verdict_title = "No known failure modes detected"
        verdict_sub = "The trace did not match any §N patterns. May be application-specific."

    matches_html = "".join(render_match(m) for m in matches)
    action_items_html = render_action_items(matches)

    tool_counts = stats.get("tool_counts", {})
    tool_cells = "".join(
        f'<div style="background:var(--bg);padding:1.25rem;text-align:center;">'
        f'<div style="font-size:1.75rem;font-weight:800;color:var(--text)">{count}</div>'
        f'<div style="font-size:0.72rem;color:var(--muted);margin-top:0.2rem">{h(tool)}</div>'
        f'</div>'
        for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FixLayer Audit — {h(trace_path.name)}</title>
  <script>(function(){{var t=localStorage.getItem('theme');if(t&&t!=='auto')document.documentElement.setAttribute('data-theme',t);}})();</script>
  <style>{CSS}</style>
</head>
<body>

<nav>
  <span class="nav-brand">Fix<span>Layer</span> <span style="font-weight:400;color:var(--muted);font-size:0.8rem">Audit Report</span></span>
  <span class="nav-meta">{h(trace_path.name)} &nbsp;·&nbsp; <span>{generated_at}</span></span>
  <button class="theme-btn" onclick="toggleTheme()" id="tb" aria-label="Toggle theme"></button>
</nav>

<section class="hero">
  <div class="container">
    <div class="report-badge">Complete Trace Audit</div>
    <h1>Session audit: <em>{match_count} failure mode{"s" if match_count != 1 else ""}</em> in {bash} Bash calls</h1>
    <p class="hero-meta">
      {"Session &nbsp;<span>" + h(session_id) + "</span> &nbsp;·&nbsp; " if session_id else ""}
      Source &nbsp;<span>{h(str(trace_path))}</span> &nbsp;·&nbsp;
      Generated &nbsp;<span>{generated_at}</span>
    </p>

    <div class="stats-strip">
      <div class="stat-cell"><div class="n" style="color:var(--accent)">{total}</div><div class="label">total tool calls</div></div>
      <div class="stat-cell"><div class="n" style="color:var(--text)">{bash}</div><div class="label">Bash calls analyzed</div></div>
      <div class="stat-cell"><div class="n" style="color:var(--orange)">{retry_count}</div><div class="label">retry attempts</div></div>
      <div class="stat-cell"><div class="n" style="color:var(--red)">{match_count}</div><div class="label">§N matches ({critical_count} critical)</div></div>
      <div class="stat-cell"><div class="n" style="color:var(--muted)">{total_ms/1000:.1f}s</div><div class="label">total Bash duration</div></div>
    </div>

    <div class="verdict {verdict_class}">
      <div class="verdict-icon">{verdict_icon}</div>
      <div>
        <div class="verdict-title">{h(verdict_title)}</div>
        <div class="verdict-sub">{h(verdict_sub)}</div>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<section>
  <div class="container">
    <div class="section-label">Failure Modes Detected</div>
    <h2 class="section-title">{match_count} match{"es" if match_count != 1 else ""} · {critical_count} critical</h2>
    <p class="section-sub">Each card shows triggering tool calls, the applicable workaround, and what to store so future sessions don't repeat the failure.</p>
    {matches_html if matches_html else '<p style="color:var(--muted);font-size:0.9rem">No §N failure modes matched this trace.</p>'}
  </div>
</section>

<hr class="divider">

<section style="background:var(--bg2)">
  <div class="container">
    <div class="section-label">Session Breakdown</div>
    <h2 class="section-title">Tool call distribution</h2>
    <div style="display:grid;grid-template-columns:repeat({min(len(tool_counts),4)},1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:10px;overflow:hidden">
      {tool_cells}
    </div>
    <div style="margin-top:1.25rem;display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem">
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem 1.25rem">
        <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:0.3rem">Avg Bash duration</div>
        <div style="font-size:1.4rem;font-weight:800;color:var(--text)">{stats.get("avg_ms",0)}ms</div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem 1.25rem">
        <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:0.3rem">Slowest call</div>
        <div style="font-size:1.4rem;font-weight:800;color:var(--orange)">{stats.get("max_ms",0):,}ms</div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem 1.25rem">
        <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:0.3rem">Retries detected</div>
        <div style="font-size:1.4rem;font-weight:800;color:var(--red)">{retry_count}</div>
      </div>
    </div>
  </div>
</section>

<hr class="divider">

<section>
  <div class="container">
    <div class="section-label">Action Items</div>
    <h2 class="section-title">What to do before next session</h2>
    <div style="display:flex;flex-direction:column;gap:0">
      {action_items_html}
    </div>
  </div>
</section>

<hr class="divider">

<footer>
  <p>
    Generated by <a href="../docs/fixlayer.html">FixLayer</a> &nbsp;·&nbsp;
    built on the <a href="https://github.com/cli-agent-spec/cli-agent-spec">CLI Agent Spec</a>
    (73 failure modes · 155 requirements) &nbsp;·&nbsp;
    source: <code>{h(str(trace_path))}</code>
  </p>
</footer>

<script>{JS}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    require_supported_python()

    parser = argparse.ArgumentParser(description="Generate a FixLayer HTML audit report from a trace file")
    parser.add_argument("trace", help="Path to trace file (JSONL, JSON array, or single-event JSON)")
    parser.add_argument("--out", default="", help="Output HTML path (default: <trace-stem>-report.html)")
    parser.add_argument("--challenges-dir", default="", help="Override challenges/ directory path")
    args = parser.parse_args()

    trace_path = Path(args.trace).resolve()
    if not trace_path.exists():
        print(f"Error: {trace_path} not found", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out).resolve() if args.out else trace_path.parent / f"{trace_path.stem}-report.html"
    challenges_dir = Path(args.challenges_dir).resolve() if args.challenges_dir else None

    print(f"Running classifier on {trace_path.name}…", file=sys.stderr)
    diag = run_diagnose(trace_path, challenges_dir)

    print("Collecting session stats…", file=sys.stderr)
    stats = session_stats(trace_path)

    print("Rendering HTML…", file=sys.stderr)
    rendered = render_html(diag, stats, trace_path, out_path)
    out_path.write_text(rendered, encoding="utf-8")

    match_count = len(diag.get("matches", []))
    print(f"Report written: {out_path}", file=sys.stderr)
    print(f"  {match_count} failure mode(s) detected", file=sys.stderr)
    print(str(out_path))


if __name__ == "__main__":
    main()
