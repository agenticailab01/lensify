"""Single-page LENS.html generator.

Self-contained HTML — no external CSS, no images, just inline styles + a
mermaid.js script tag from CDN for the diagram. Renders in any browser.
"""
from __future__ import annotations

import html
import json


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def build_mermaid(shape: str, modules: list[dict], top_dirs: list[str]) -> str:
    """Generate a Mermaid diagram string based on the chosen shape."""
    if shape == "layered":
        return """flowchart TB
  subgraph Presentation
    A[api routes]
  end
  subgraph Domain
    B[business logic]
  end
  subgraph Data
    C[database & repositories]
  end
  A --> B --> C"""

    if shape == "pipeline":
        stages = top_dirs[:5] if top_dirs else ["input", "process", "output"]
        nodes = " --> ".join(f"S{i}[{_esc(s)}]" for i, s in enumerate(stages))
        return f"flowchart LR\n  {nodes}"

    if shape == "hub-spoke":
        # Pick the most-imported module as the hub (first module by convention)
        spokes = [m.get("path", "?").split("/")[0] for m in modules[:5]]
        if not spokes:
            spokes = top_dirs[:5]
        lines = ["flowchart TB", "  Hub((Core))"]
        for i, s in enumerate(spokes):
            lines.append(f"  Hub --> M{i}[{_esc(s)}]")
        return "\n".join(lines)

    if shape == "domain-map":
        domains = top_dirs[:6] if top_dirs else ["domain-a", "domain-b"]
        lines = ["flowchart LR"]
        for i, d in enumerate(domains):
            lines.append(f"  subgraph {d}[{_esc(d)}]")
            lines.append(f"    N{i}[modules]")
            lines.append("  end")
        return "\n".join(lines)

    # flat / fallback
    items = top_dirs[:6] if top_dirs else ["root"]
    lines = ["flowchart TB"]
    for i, item in enumerate(items):
        lines.append(f"  F{i}[{_esc(item)}]")
    return "\n".join(lines)


CONFIDENCE_BADGE = {
    "strong": "✅ Strong signal",
    "weak": "🟡 Weak signal",
    "forced": "🔴 No clear shape; module list fallback",
}


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ProjectLens — {project_name}</title>
  <meta name="generator" content="projectlens/{version}">
  <style>
    :root {{
      --bg: #fdfdfb; --fg: #1a1a1a; --muted: #6b6b6b;
      --accent: #2563eb; --warn: #d97706; --bad: #dc2626; --ok: #059669;
      --card: #ffffff; --border: #e5e5e5;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --bg:#0f0f10; --fg:#e6e6e6; --muted:#9a9a9a;
              --card:#1a1a1c; --border:#2a2a2d; }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 24px;
      background: var(--bg); color: var(--fg);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      line-height: 1.55;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
    .subtitle {{ color: var(--muted); margin-bottom: 24px; font-size: 0.9rem; }}
    .tier-badge {{
      display: inline-block; padding: 2px 8px; border-radius: 4px;
      background: var(--accent); color: white; font-size: 0.75rem;
      font-weight: 600; vertical-align: middle; margin-left: 8px;
    }}
    .panel {{
      background: var(--card); border: 1px solid var(--border);
      border-radius: 8px; padding: 18px 22px; margin-bottom: 16px;
    }}
    .panel h2 {{ margin-top: 0; font-size: 1.1rem; }}
    .summary-line {{ font-size: 1.15rem; font-weight: 500; margin: 0; }}
    .mermaid-host {{ background: white; padding: 12px; border-radius: 6px; overflow-x: auto; }}
    @media (prefers-color-scheme: dark) {{ .mermaid-host {{ background: #fafafa; }} }}
    .confidence {{ font-size: 0.8rem; color: var(--muted); margin-top: 8px; }}
    .narrative {{ font-size: 1.0rem; line-height: 1.7; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
    code {{ font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.9em;
            background: rgba(127,127,127,0.1); padding: 2px 5px; border-radius: 3px; }}
    .risk-tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px;
                 font-size: 0.7rem; font-weight: 700; margin-right: 6px; }}
    .risk-EXTRACTED  {{ background: var(--ok); color: white; }}
    .risk-INFERRED   {{ background: var(--warn); color: white; }}
    .risk-AMBIGUOUS  {{ background: var(--bad); color: white; }}
    .footer {{ color: var(--muted); font-size: 0.8rem; margin-top: 32px; text-align: center; }}
    .grid-2 {{ display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }}
    @media (max-width: 800px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{project_name}<span class="tier-badge">{tier}</span></h1>
    <div class="subtitle">{tier_reason}</div>

    <div class="panel">
      <h2>What this is</h2>
      <p class="summary-line">{summary}</p>
    </div>

    <div class="grid-2">
      <div class="panel">
        <h2>The picture</h2>
        <div class="mermaid-host">
          <pre class="mermaid">
{mermaid}
          </pre>
        </div>
        <div class="confidence">{confidence_badge} — {shape}</div>
      </div>

      <div class="panel">
        <h2>Day-1 narrative</h2>
        <p class="narrative">{narrative}</p>
      </div>
    </div>

    <div class="panel">
      <h2>Hotspots</h2>
      <p class="subtitle" style="margin-top:-6px">Files with the most commits in the last 90 days.</p>
      {hotspots_table}
    </div>

    <div class="panel">
      <h2>Risks &amp; unknowns</h2>
      {risks_list}
    </div>

    <div class="footer">
      Generated by <strong>projectlens v{version}</strong> &middot;
      {n_files} files &middot; {n_loc} LOC &middot;
      capsule budget {capsule_tokens} tok
    </div>
  </div>

  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
  </script>
</body>
</html>
"""


def render_hotspots_table(hotspots: list[dict]) -> str:
    if not hotspots:
        return "<p class='subtitle'>No git history found, or no recent activity.</p>"
    rows = []
    for h in hotspots[:10]:
        rows.append(
            f"<tr><td><code>{_esc(h.get('path',''))}</code></td>"
            f"<td>{int(h.get('commits',0))}</td>"
            f"<td>{int(h.get('authors',0))}</td>"
            f"<td>{_esc(h.get('last_touched',''))}</td></tr>"
        )
    return (
        "<table><thead><tr><th>File</th><th>Commits</th><th>Authors</th><th>Last touched</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_risks_list(risks: list[dict]) -> str:
    if not risks:
        return "<p class='subtitle'>No structural risks detected.</p>"
    items = []
    for r in risks[:12]:
        tag = r.get("confidence", "INFERRED")
        summary = _esc(r.get("summary", ""))
        items.append(f"<li><span class='risk-tag risk-{tag}'>{tag}</span> {summary}</li>")
    return f"<ul>{''.join(items)}</ul>"


def build_html(lens_data: dict, version: str = "0.1.0") -> str:
    """Render the full single-page lens HTML."""
    project_name = _esc(lens_data.get("project_name", "Untitled Project"))
    tier = lens_data.get("tier", "T2")
    tier_reason = _esc(lens_data.get("tier_decision", {}).get("reason", ""))
    summary_line = _esc(lens_data.get("summary", "—"))
    narrative = _esc(lens_data.get("narrative", "Narrative unavailable in ast-only mode."))
    shape_info = lens_data.get("shape", {"shape": "flat", "confidence": "forced"})
    shape = shape_info.get("shape", "flat")
    confidence = shape_info.get("confidence", "forced")
    badge = CONFIDENCE_BADGE.get(confidence, confidence)
    mermaid = build_mermaid(
        shape,
        lens_data.get("modules", []),
        lens_data.get("top_dirs", []),
    )
    hotspots_table = render_hotspots_table(lens_data.get("hotspots", []))
    risks_list = render_risks_list(lens_data.get("risks", []))

    return HTML_TEMPLATE.format(
        project_name=project_name,
        tier=tier,
        tier_reason=tier_reason,
        summary=summary_line,
        mermaid=mermaid,
        narrative=narrative,
        shape=shape,
        confidence_badge=badge,
        hotspots_table=hotspots_table,
        risks_list=risks_list,
        n_files=lens_data.get("files", 0),
        n_loc=f"{lens_data.get('loc', 0):,}",
        capsule_tokens=lens_data.get("capsule_tokens", "?"),
        version=version,
    )
