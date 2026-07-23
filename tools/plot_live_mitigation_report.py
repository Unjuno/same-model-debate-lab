"""Create dependency-free SVG plots from the repeated-run report JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COLORS = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"]

def esc(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def svg_start(title: str, width: int = 1000, height: int = 560) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', '<style>text{font-family:Arial,sans-serif;fill:#263238} .muted{fill:#607d8b;font-size:14px} .grid{stroke:#cfd8dc;stroke-width:1} .axis{stroke:#455a64;stroke-width:2}</style>', f'<text x="60" y="42" font-size="24" font-weight="bold">{esc(title)}</text>']

def bar_plot(report: dict, metric: str, title: str, out: Path, y_max: float = 1.0) -> None:
    width, height, left, top, plot_w, plot_h = 1000, 560, 100, 80, 830, 390
    conditions = report["conditions"]
    vals = [report["by_condition"][c]["metrics"][metric]["mean"] for c in conditions]
    cis = [report["by_condition"][c]["metrics"][metric]["ci95"] for c in conditions]
    lines = svg_start(title, width, height)
    for tick in range(0, 6):
        y = top + plot_h - tick * plot_h / 5
        value = y_max * tick / 5
        lines += [f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}"/>', f'<text class="muted" x="62" y="{y+5:.1f}">{value:.1f}</text>']
    lines.append(f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}"/>')
    step = plot_w / len(conditions)
    for i, (c, value, interval) in enumerate(zip(conditions, vals, cis, strict=True)):
        x = left + i * step + step * 0.22
        bar_w = step * 0.56
        y = top + plot_h - value / y_max * plot_h
        h = value / y_max * plot_h
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{COLORS[i]}"/>')
        lo, hi = interval
        cy1, cy2 = top + plot_h - hi / y_max * plot_h, top + plot_h - lo / y_max * plot_h
        cx = x + bar_w / 2
        lines += [f'<line x1="{cx:.1f}" y1="{cy1:.1f}" x2="{cx:.1f}" y2="{cy2:.1f}" stroke="#111" stroke-width="3"/>', f'<line x1="{cx-8:.1f}" y1="{cy1:.1f}" x2="{cx+8:.1f}" y2="{cy1:.1f}" stroke="#111" stroke-width="2"/>', f'<line x1="{cx-8:.1f}" y1="{cy2:.1f}" x2="{cx+8:.1f}" y2="{cy2:.1f}" stroke="#111" stroke-width="2"/>']
        label = c.replace("_", " ")
        lines.append(f'<text class="muted" text-anchor="middle" x="{cx:.1f}" y="{top+plot_h+28}" transform="rotate(-18 {cx:.1f} {top+plot_h+28})">{esc(label)}</text>')
    lines += ['<text class="muted" x="60" y="535">Bars: mean across 20 repeats; whiskers: 95% exploratory CI.</text>', '</svg>']
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

def repeat_plot(report: dict, out: Path) -> None:
    width, height, left, top, plot_w, plot_h = 1000, 560, 80, 80, 850, 390
    lines = svg_start("Final accuracy across repeats", width, height)
    n = report["n_repeats"]
    for tick in range(0, 6):
        y = top + plot_h - tick * plot_h / 5
        value = tick / 5
        lines += [f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}"/>', f'<text class="muted" x="42" y="{y+5:.1f}">{value:.1f}</text>']
    lines.append(f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}"/>')
    for i, condition in enumerate(report["conditions"]):
        points = []
        for repeat in range(n):
            value = report["repeat_metrics"][condition][str(repeat)]["final_accuracy"]
            x = left + repeat * plot_w / max(1, n - 1)
            y = top + plot_h - value * plot_h
            points.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{COLORS[i]}" stroke-width="3"/>')
        lines.append(f'<text class="muted" x="{left+plot_w-170}" y="{top+20+i*22}" fill="{COLORS[i]}">{esc(condition.replace("_", " "))}</text>')
    for repeat in range(n):
        x = left + repeat * plot_w / max(1, n - 1)
        lines.append(f'<text class="muted" text-anchor="middle" x="{x:.1f}" y="{top+plot_h+25}">{repeat:02d}</text>')
    lines += ['<text class="muted" x="60" y="535">Each line shows one 9-item repeat. Lines are descriptive; repeats are not time series.</text>', '</svg>']
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bar_plot(report, "final_accuracy", "Final accuracy by condition", out / "final_accuracy.svg")
    bar_plot(report, "answer_loss_rate", "Answer loss rate by condition", out / "answer_loss_rate.svg")
    bar_plot(report, "initial_any_correct_rate", "Initial correct-path availability by condition", out / "initial_correct_paths.svg")
    repeat_plot(report, out / "condition_comparison.svg")

if __name__ == "__main__":
    main()
