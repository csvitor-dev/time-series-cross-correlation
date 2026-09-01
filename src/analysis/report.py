from __future__ import annotations

from pathlib import Path

from analysis.cross_correlation import AnalysisOutput
from config import PipelineConfig


def _coverage_table(output: AnalysisOutput, min_coverage: float) -> list[str]:
    lines = ["| dia | cobertura | |", "|---|---|---|"]
    for day in sorted(output.coverage):
        cov = output.coverage[day]
        flag = "⚠" if cov < min_coverage else ""
        lines.append(f"| {day.isoformat()} | {cov:.1%} | {flag} |")
    return lines


def _method_section(name: str, output: AnalysisOutput) -> list[str]:
    pairs = output.pairs[name].copy()
    pairs["abs"] = pairs["coefficient"].abs()
    top = pairs.sort_values("abs", ascending=False).head(10)
    significant = int((pairs["p_value"] < 0.05).sum())

    lines = [
        f"### {name}",
        "",
        f"Pares: {len(pairs)} · significativos (p < 0.05): {significant}",
        "",
        "| d_i | d_j | lag (dias) | coef. | p-valor | estab. (σ) |",
        "|---|---|---|---|---|---|",
    ]
    for row in top.itertuples(index=False):
        lines.append(
            f"| {row.d_i} | {row.d_j} | {row.lag_days} | {row.coefficient:.3f} | "
            f"{row.p_value:.3f} | {row.stability_std:.3f} |"
        )
    lines += ["", f"![heatmap {name}](correlations/heatmap_{name}.png)", ""]
    return lines


def write_report(output: AnalysisOutput, config: PipelineConfig, path: str | Path) -> Path:
    analysis = config.analysis
    lines = [
        f"# Amostragem — correlação cruzada ({config.symbol}, {len(output.coverage)} dias)",
        "",
        "## Parâmetros",
        "",
        f"- valor da série: `{analysis.value}`",
        f"- métodos: {', '.join(analysis.methods)}",
        f"- janela: {analysis.window.start}–{analysis.window.end} ({analysis.window.tz})",
        f"- cobertura mínima: {analysis.min_coverage:.0%}",
        f"- sub-janelas de estabilidade: {analysis.stability_subwindows}",
        "",
        "## Cobertura por dia",
        "",
        *_coverage_table(output, analysis.min_coverage),
        "",
        "## Resultados",
        "",
    ]
    for name in analysis.methods:
        lines += _method_section(name, output)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
