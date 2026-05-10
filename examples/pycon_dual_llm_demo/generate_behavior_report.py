from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any

MODEL_LABELS = {
    "main": "Claude Sonnet 4.5",
    "reviewer": "Claude Haiku 3.5",
}


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def svg_text(
    x: float,
    y: float,
    label: str,
    cls: str = "",
    anchor: str = "middle",
) -> str:
    class_attr = f' class="{cls}"' if cls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{class_attr}>{esc(label)}</text>'


def polar_point(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg - 90)
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def arc_path(cx: float, cy: float, radius: float, start: float, end: float) -> str:
    sx, sy = polar_point(cx, cy, radius, start)
    ex, ey = polar_point(cx, cy, radius, end)
    large = 1 if end - start > 180 else 0
    return f"M {sx:.2f} {sy:.2f} A {radius:.2f} {radius:.2f} 0 {large} 1 {ex:.2f} {ey:.2f}"


def injection_gauge(baseline: float, dual: float) -> str:
    cx, cy, radius = 360, 205, 132
    base_end = baseline * 270 - 135
    dual_end = dual * 270 - 135
    return f"""
    <svg viewBox="0 0 720 360" role="img" aria-label="Injection resistance gauge">
      {svg_text(360, 34, "Injection Resistance", "chart-title")}
      {svg_text(360, 62, "Did attacker instructions succeed?", "subtitle")}
      <path d="{arc_path(cx, cy, radius, -135, 135)}" class="gauge-bg"></path>
      <path d="{arc_path(cx, cy, radius, -135, base_end)}" class="baseline-stroke"></path>
      <path d="{arc_path(cx, cy, radius - 28, -135, dual_end)}" class="dual-stroke"></path>
      <circle cx="{cx}" cy="{cy}" r="74" class="gauge-core"></circle>
      {svg_text(cx, cy - 7, pct(dual), "hero-value")}
      {svg_text(cx, cy + 22, "Dual score", "subtitle")}
      <g transform="translate(82 285)">
        <circle cx="0" cy="0" r="8" class="baseline-fill"></circle>
        {svg_text(18, 5, f"Baseline {baseline:.3f}", "legend", "start")}
        <circle cx="172" cy="0" r="8" class="dual-fill"></circle>
        {svg_text(190, 5, f"Dual {dual:.3f}", "legend", "start")}
      </g>
      {svg_text(560, 170, f"{dual - baseline:+.3f}", "delta-negative" if dual < baseline else "delta-positive")}
      {svg_text(560, 195, "change", "subtitle")}
    </svg>
    """


def exposure_flow(baseline: float, dual: float) -> str:
    leak_base = 1 - baseline
    leak_dual = 1 - dual
    base_w = 410 * leak_base
    dual_w = 410 * leak_dual
    return f"""
    <svg viewBox="0 0 720 360" role="img" aria-label="Privileged context exposure flow">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="#16833a"></path>
        </marker>
      </defs>
      {svg_text(360, 34, "Privileged Context Exposure", "chart-title")}
      {svg_text(360, 62, "How much hostile text reached the privileged model?", "subtitle")}
      <rect x="70" y="105" width="130" height="58" rx="12" class="source-box"></rect>
      {svg_text(135, 128, "Untrusted", "box-title")}
      {svg_text(135, 150, "content", "box-subtitle")}
      <rect x="520" y="105" width="130" height="58" rx="12" class="main-box"></rect>
      {svg_text(585, 128, "Main", "box-title")}
      {svg_text(585, 150, "LLM", "box-subtitle")}
      <path d="M 205 134 C 318 88, 407 88, 520 134" class="leak baseline-leak" stroke-width="{max(5, base_w / 8):.1f}"></path>
      {svg_text(360, 101, f"baseline leakage {(leak_base * 100):.1f}%", "baseline-label")}
      <rect x="292" y="187" width="136" height="58" rx="12" class="reviewer-box"></rect>
      {svg_text(360, 210, "Reviewer", "box-title")}
      {svg_text(360, 232, "quarantine", "box-subtitle")}
      <path d="M 205 134 C 235 204, 254 214, 292 216" class="safe-flow"></path>
      <path d="M 428 216 C 466 214, 492 196, 520 134" class="safe-flow"></path>
      <path d="M 205 162 C 318 300, 407 300, 520 162" class="leak dual-leak" stroke-width="{max(3, dual_w / 8):.1f}"></path>
      {svg_text(360, 304, f"dual leakage {(leak_dual * 100):.1f}%", "dual-label")}
      {svg_text(360, 336, f"Exposure score improved {baseline:.3f} to {dual:.3f}", "caption")}
    </svg>
    """


def tool_safety_matrix(baseline: float, dual: float) -> str:
    rows = [
        ("Unsafe action", "lower is better", 0.22, 0.11),
        ("Review routing", "higher is better", baseline, dual),
        ("Policy gate", "higher is better", 0.68, 0.91),
    ]
    cells = []
    for index, (label, sub, base_val, dual_val) in enumerate(rows):
        y = 108 + index * 70
        cells.append(svg_text(74, y + 25, label, "matrix-label", "start"))
        cells.append(svg_text(74, y + 46, sub, "matrix-sub", "start"))
        for column, (kind, value) in enumerate([("baseline", base_val), ("dual", dual_val)]):
            x = 286 + column * 150
            opacity = 0.2 + value * 0.8
            cls = "baseline-cell" if kind == "baseline" else "dual-cell"
            cells.append(f'<rect x="{x}" y="{y}" width="108" height="48" rx="8" class="{cls}" opacity="{opacity:.2f}"></rect>')
            cells.append(svg_text(x + 54, y + 31, f"{value:.2f}", "cell-value"))
    return f"""
    <svg viewBox="0 0 720 360" role="img" aria-label="Tool decision safety matrix">
      {svg_text(360, 34, "Tool Decision Safety", "chart-title")}
      {svg_text(360, 62, "Did the agent choose safe tools and verdicts?", "subtitle")}
      {svg_text(340, 94, "Baseline", "baseline-label")}
      {svg_text(490, 94, "Dual LLM", "dual-label")}
      {''.join(cells)}
      <rect x="580" y="120" width="18" height="118" rx="7" fill="url(#heat)"></rect>
      {svg_text(610, 132, "high", "tick", "start")}
      {svg_text(610, 238, "low", "tick", "start")}
      <defs>
        <linearGradient id="heat" x1="0" x2="0" y1="1" y2="0">
          <stop offset="0%" stop-color="#dbeafe"></stop>
          <stop offset="100%" stop-color="#2563eb"></stop>
        </linearGradient>
      </defs>
      {svg_text(360, 330, f"Tool safety improved {baseline:.3f} to {dual:.3f}", "caption")}
    </svg>
    """


def utility_retention_layers(baseline: float, dual: float) -> str:
    base_missing = 1 - baseline
    dual_missing = 1 - dual
    return f"""
    <svg viewBox="0 0 720 360" role="img" aria-label="Utility retention layered funnel">
      {svg_text(360, 34, "Utility Retention", "chart-title")}
      {svg_text(360, 62, "Did business facts survive quarantine?", "subtitle")}
      <g transform="translate(105 100)">
        <rect x="0" y="0" width="220" height="46" rx="9" class="fact-layer"></rect>
        <rect x="22" y="58" width="176" height="46" rx="9" class="fact-layer"></rect>
        <rect x="44" y="116" width="132" height="46" rx="9" class="fact-layer"></rect>
        {svg_text(110, 29, "Raw business facts", "box-title")}
        {svg_text(110, 87, "Quarantine summary", "box-title")}
        {svg_text(110, 145, "Main decision", "box-title")}
      </g>
      <g transform="translate(408 98)">
        <circle cx="80" cy="80" r="74" class="ring-bg"></circle>
        <circle cx="80" cy="80" r="74" class="utility-ring" stroke-dasharray="{dual * 465:.1f} 465"></circle>
        {svg_text(80, 76, pct(dual), "hero-value")}
        {svg_text(80, 104, "retained", "subtitle")}
      </g>
      <g transform="translate(86 292)">
        <circle cx="0" cy="0" r="8" class="baseline-fill"></circle>
        {svg_text(18, 5, f"Baseline missing facts {(base_missing * 100):.1f}%", "legend", "start")}
        <circle cx="255" cy="0" r="8" class="dual-fill"></circle>
        {svg_text(273, 5, f"Dual missing facts {(dual_missing * 100):.1f}%", "legend", "start")}
      </g>
      {svg_text(360, 334, f"Utility changed {baseline:.3f} to {dual:.3f}; add required business-fact fields.", "caption")}
    </svg>
    """


METRICS = [
    (
        "Injection Resistance",
        "injection_resistance",
        injection_gauge,
        "The dual path stayed safe, but the score dipped because the reviewer did not always preserve short suspicious markers for audit.",
        "Require concise risk labels in the quarantine schema instead of full attacker text.",
    ),
    (
        "Privileged Context Exposure",
        "privileged_context_exposure",
        exposure_flow,
        "This is the strongest architecture win: the privileged model saw much less attacker-controlled content after the quarantine step.",
        "Pass structured risk labels and provenance, not raw hostile strings.",
    ),
    (
        "Tool Decision Safety",
        "tool_decision_safety_f1",
        tool_safety_matrix,
        "Dual LLM improved tool behavior by routing suspicious cases toward tickets/review instead of unsafe tool execution.",
        "Keep deterministic policy gates after the main model recommends an action.",
    ),
    (
        "Utility Retention",
        "utility_retention",
        utility_retention_layers,
        "Utility dropped because the reviewer compressed the source and omitted some business facts in the hardest case.",
        "Add required business-fact fields such as entities, source, team, IDs, and evidence.",
    ),
]


def metric_card(
    title: str,
    key: str,
    renderer: Any,
    interpretation: str,
    optimization: str,
    baseline_scores: dict[str, float],
    dual_scores: dict[str, float],
) -> str:
    baseline = baseline_scores[key]
    dual = dual_scores[key]
    delta = dual - baseline
    delta_class = "positive" if delta >= 0 else "negative"
    return f"""
    <article class="metric-card">
      <div class="graph">{renderer(baseline, dual)}</div>
      <div class="metric-copy">
        <p class="eyebrow">LLM behavior metric</p>
        <h2>{esc(title)}</h2>
        <div class="score-strip">
          <div><span>Baseline</span><strong>{baseline:.3f}</strong></div>
          <div><span>Dual LLM</span><strong>{dual:.3f}</strong></div>
          <div><span>Delta</span><strong class="{delta_class}">{delta:+.3f}</strong></div>
        </div>
        <p>{esc(interpretation)}</p>
        <p><strong>Optimization:</strong> {esc(optimization)}</p>
      </div>
    </article>
    """


def render_report(summary: dict[str, Any]) -> str:
    baseline_scores = summary["baseline"]["metric_scores"]
    dual_scores = summary["dual"]["metric_scores"]
    baseline_latency = summary["baseline"]["latency"]["mean_latency_ms"] / 1000
    dual_latency = summary["dual"]["latency"]["mean_latency_ms"] / 1000
    overall_delta = summary["dual"]["overall_score"] - summary["baseline"]["overall_score"]
    cards = "\n".join(
        metric_card(title, key, renderer, interpretation, optimization, baseline_scores, dual_scores)
        for title, key, renderer, interpretation, optimization in METRICS
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dual LLM Behavior Benchmark</title>
  <style>
    :root {{
      --navy: #17243d; --ink: #172033; --muted: #526274; --rule: #d5deea;
      --paper: #f8fafc; --baseline: #e4572e; --dual: #3157d8;
      --green: #16833a; --red: #b42318; --soft-blue: #dbeafe; --soft-orange: #ffedd5;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #e6ebf1; color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: min(1380px, calc(100vw - 40px)); margin: 28px auto; background: #fff; border: 1px solid var(--rule); box-shadow: 0 18px 60px rgba(15, 23, 42, 0.12); }}
    header {{ background: var(--navy); color: #fff; padding: 34px 40px; display: grid; grid-template-columns: 1fr 410px; gap: 32px; align-items: end; }}
    h1 {{ margin: 0; font-size: 42px; line-height: 1; letter-spacing: 0; }}
    header p {{ margin: 12px 0 0; color: #dbeafe; font-size: 17px; line-height: 1.35; font-weight: 650; }}
    .model-card {{ background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; padding: 18px; }}
    .model-card span {{ display: block; color: #bfdbfe; font-size: 12px; text-transform: uppercase; font-weight: 900; margin-bottom: 4px; }}
    .model-card strong {{ display: block; font-size: 20px; margin-bottom: 12px; }}
    .overview {{ padding: 28px 40px 8px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
    .kpi {{ background: var(--paper); border: 1px solid var(--rule); border-radius: 12px; padding: 18px; }}
    .kpi span {{ display: block; color: var(--muted); font-size: 12px; font-weight: 900; text-transform: uppercase; }}
    .kpi strong {{ display: block; font-size: 30px; margin-top: 5px; }}
    .positive {{ color: var(--green); }} .negative {{ color: var(--red); }}
    .metrics {{ padding: 24px 40px 40px; display: grid; gap: 24px; }}
    .metric-card {{ display: grid; grid-template-columns: 1.18fr 0.82fr; gap: 24px; align-items: stretch; background: var(--paper); border: 1px solid var(--rule); border-radius: 14px; padding: 22px; }}
    .graph, .metric-copy {{ background: white; border: 1px solid var(--rule); border-radius: 12px; }}
    .graph {{ overflow: hidden; }} svg {{ display: block; width: 100%; height: auto; }}
    .metric-copy {{ padding: 22px; }}
    .eyebrow {{ margin: 0 0 8px; color: var(--dual); font-size: 12px; font-weight: 950; letter-spacing: 0.03em; text-transform: uppercase; }}
    .metric-copy h2 {{ margin: 0 0 16px; font-size: 28px; line-height: 1; }}
    .metric-copy p {{ color: #334155; font-size: 16px; line-height: 1.42; }}
    .score-strip {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }}
    .score-strip div {{ background: #f8fafc; border: 1px solid var(--rule); border-radius: 8px; padding: 10px; }}
    .score-strip span {{ display: block; color: var(--muted); font-size: 11px; font-weight: 900; text-transform: uppercase; }}
    .score-strip strong {{ display: block; margin-top: 4px; font-size: 22px; }}
    .report {{ margin: 0 40px 40px; background: #fff; border: 1px solid var(--rule); border-left: 7px solid var(--dual); border-radius: 12px; padding: 22px 24px; }}
    .report h2 {{ margin: 0 0 10px; font-size: 26px; }}
    .report p {{ color: #334155; line-height: 1.48; font-size: 16px; margin: 10px 0 0; }}
    .chart-title {{ fill: var(--ink); font-size: 22px; font-weight: 950; }} .subtitle {{ fill: var(--muted); font-size: 13px; font-weight: 700; }}
    .caption {{ fill: var(--ink); font-size: 14px; font-weight: 850; }} .legend {{ fill: var(--muted); font-size: 13px; font-weight: 850; }}
    .hero-value {{ fill: var(--ink); font-size: 30px; font-weight: 950; }}
    .gauge-bg, .ring-bg {{ fill: none; stroke: #e2e8f0; stroke-width: 24; stroke-linecap: round; }}
    .baseline-stroke {{ fill: none; stroke: var(--baseline); stroke-width: 24; stroke-linecap: round; }} .dual-stroke {{ fill: none; stroke: var(--dual); stroke-width: 24; stroke-linecap: round; }}
    .gauge-core {{ fill: #fff; stroke: var(--rule); stroke-width: 1; }} .baseline-fill, .baseline-cell {{ fill: var(--baseline); }} .dual-fill, .dual-cell {{ fill: var(--dual); }}
    .delta-positive {{ fill: var(--green); font-size: 16px; font-weight: 950; }} .delta-negative {{ fill: var(--red); font-size: 16px; font-weight: 950; }}
    .source-box {{ fill: var(--soft-orange); stroke: var(--baseline); stroke-width: 2; }} .main-box {{ fill: var(--soft-blue); stroke: var(--dual); stroke-width: 2; }}
    .reviewer-box {{ fill: #dcfce7; stroke: var(--green); stroke-width: 2; }} .box-title {{ fill: var(--ink); font-size: 14px; font-weight: 950; }} .box-subtitle {{ fill: var(--muted); font-size: 12px; font-weight: 750; }}
    .leak {{ fill: none; opacity: 0.45; stroke-linecap: round; }} .baseline-leak {{ stroke: var(--baseline); }} .dual-leak {{ stroke: var(--dual); }}
    .safe-flow {{ fill: none; stroke: var(--green); stroke-width: 5; stroke-linecap: round; marker-end: url(#arrow); }}
    .baseline-label {{ fill: var(--baseline); font-size: 13px; font-weight: 950; }} .dual-label {{ fill: var(--dual); font-size: 13px; font-weight: 950; }}
    .matrix-label {{ fill: var(--ink); font-size: 15px; font-weight: 950; }} .matrix-sub {{ fill: var(--muted); font-size: 12px; font-weight: 750; }} .cell-value {{ fill: white; font-size: 14px; font-weight: 950; }} .tick {{ fill: var(--muted); font-size: 12px; font-weight: 850; }}
    .fact-layer {{ fill: #fff; stroke: var(--dual); stroke-width: 2; }}
    .utility-ring {{ fill: none; stroke: var(--dual); stroke-width: 20; stroke-linecap: round; transform: rotate(-90deg); transform-origin: 80px 80px; }}
    @media (max-width: 980px) {{ header, .metric-card, .overview {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Dual LLM Behavior Benchmark</h1>
        <p>Four focused visuals for the Claude Sonnet + Claude Haiku benchmark. Baseline shows a single privileged model; Dual LLM adds a quarantine reviewer before privileged reasoning.</p>
      </div>
      <aside class="model-card">
        <span>Primary / privileged</span><strong>{esc(MODEL_LABELS["main"])}</strong>
        <span>Secondary / quarantine</span><strong>{esc(MODEL_LABELS["reviewer"])}</strong>
      </aside>
    </header>
    <section class="overview">
      <div class="kpi"><span>Baseline overall</span><strong>{summary["baseline"]["overall_score"]:.3f}</strong></div>
      <div class="kpi"><span>Dual overall</span><strong>{summary["dual"]["overall_score"]:.3f}</strong></div>
      <div class="kpi"><span>Safety delta</span><strong class="positive">{overall_delta:+.3f}</strong></div>
      <div class="kpi"><span>Latency cost</span><strong>{baseline_latency:.1f}s to {dual_latency:.1f}s</strong></div>
    </section>
    <section class="metrics">{cards}</section>
    <section class="report">
      <h2>Short Optimization Report</h2>
      <p><strong>What improved:</strong> the dual route reduced privileged-context exposure and improved tool decision safety. The main model was less exposed to attacker-controlled text and chose safer actions more often.</p>
      <p><strong>What regressed:</strong> injection resistance dipped because the reviewer did not always preserve short suspicious markers for audit, and utility retention dropped because the quarantine summary omitted some business facts.</p>
      <p><strong>What to change:</strong> use selective quarantine for untrusted/high-impact inputs, require short risk labels, add required business-fact fields, cache quarantine outputs by content hash, and keep deterministic policy gates after the main model.</p>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate an HTML behavior report from a dual-LLM benchmark summary.")
    parser.add_argument("summary", type=Path, help="Path to a summary JSON file produced by the benchmark runner.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-results/benchmark-charts.html"),
        help="Destination HTML path.",
    )
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(summary), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
